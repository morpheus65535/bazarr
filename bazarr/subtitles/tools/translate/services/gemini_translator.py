# coding=utf-8

import json
import re
import os
import json_tricks
import signal
import threading
import time
import typing
import logging

import srt
import pysubs2
import requests
import unicodedata as ud
from collections import Counter
from typing import List
from srt import Subtitle

from retry.api import retry
from app.config import settings
from sonarr.history import history_log
from radarr.history import history_log_movie
from deep_translator import GoogleTranslator
from utilities.path_mappings import path_mappings
from subtitles.processing import ProcessSubtitlesResult
from app.event_handler import show_progress, hide_progress, show_message
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from ..core.translator_utils import add_translator_info, get_description, create_process_result

logger = logging.getLogger(__name__)

class SubtitleObject(typing.TypedDict):
    """
    TypedDict for subtitle objects used in translation
    """
    index: str
    content: str


class GeminiTranslatorService:

    def __init__(self, source_srt_file, dest_srt_file, to_lang, media_type, sonarr_series_id, sonarr_episode_id,
                 radarr_id, forced, hi, video_path, from_lang, orig_to_lang, **kwargs):
        self.source_srt_file = source_srt_file
        self.dest_srt_file = dest_srt_file
        self.to_lang = to_lang
        self.media_type = media_type
        self.sonarr_series_id = sonarr_series_id
        self.radarr_id = radarr_id
        self.from_lang = from_lang
        self.video_path = video_path
        self.forced = forced
        self.hi = hi
        self.sonarr_series_id = sonarr_series_id
        self.sonarr_episode_id = sonarr_episode_id
        self.radarr_id = radarr_id
        self.orig_to_lang = orig_to_lang

        self.gemini_api_key = None
        self.current_api_key = None
        self.current_api_number = 1
        self.backup_api_number = 2
        self.target_language = None
        self.input_file = None
        self.output_file = None
        self.start_line = 1
        self.description = None
        self.model_name = "gemini-2.0-flash"
        self.batch_size = 100
        self.free_quota = True
        self.error_log = False
        self.token_limit = 0
        self.token_count = 0
        self.interrupt_flag = False
        self.progress_file = None
        self.current_progress = 0

    def translate(self):
        subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
        subs.remove_miscellaneous_events()

        try:
            logger.debug(f'BAZARR is sending subtitle file to Gemini for translation')
            logger.info(f"BAZARR is sending subtitle file to Gemini for translation " + self.source_srt_file)

            self.gemini_api_key = settings.translator.gemini_key
            self.current_api_key = self.gemini_api_key
            self.target_language = language_from_alpha3(self.to_lang)
            self.input_file = self.source_srt_file
            self.output_file = self.dest_srt_file
            self.model_name = settings.translator.gemini_model
            self.description = get_description(self.media_type, self.radarr_id, self.sonarr_series_id)

            if "2.5-flash" in self.model_name or "pro" in self.model_name:
                self.batch_size = 300

            if self.input_file:
                self.progress_file = os.path.join(os.path.dirname(self.input_file), f".{os.path.basename(self.input_file)}.progress")

            self._check_saved_progress()

            try:
                self._translate_with_gemini()
                add_translator_info(self.dest_srt_file, f"# Subtitles translated with {settings.translator.gemini_model} # ")
            except Exception as e:
                show_message(f'Gemini translation error: {str(e)}')

        except Exception as e:
            logger.error(f'BAZARR encountered an error translating with Gemini: {str(e)}')
            return False

    @staticmethod
    def get_instruction(language: str, description: str) -> str:
        """
        Get the instruction for the translation model based on the target language.
        """
        instruction = f"""You are an assistant that translates subtitles to {language}.
    You will receive the following JSON type:

    class SubtitleObject(typing.TypedDict):
        index: str
        content: str

    Request: list[SubtitleObject]

    The 'index' key is the index of the subtitle dialog.
    The 'content' key is the dialog to be translated.

    The indices must remain the same in the response as in the request.
    Dialogs must be translated as they are without any changes.
    If a line has a comma or multiple sentences, try to keep one line to about 40-50 characters.
    """
        if description:
            instruction += "\nAdditional user instruction: '" + description + "'"
        return instruction

    def _check_saved_progress(self):
        """Check if there's a saved progress file and load it if exists"""
        if not self.progress_file or not os.path.exists(self.progress_file):
            return

        if self.start_line != 1:
            return

        try:
            with open(self.progress_file, "r") as f:
                data = json.load(f)
                saved_line = data.get("line", 1)
                input_file = data.get("input_file")

                # Verify the progress file matches our current input file
                if input_file != self.input_file:
                    show_message(f"Found progress file for different subtitle: {input_file}")
                    show_message("Ignoring saved progress.")
                    return

                if saved_line > 1 and self.start_line == 1:
                    os.remove(self.output_file)
        except Exception as e:
            show_message(f"Error reading progress file: {e}")

    def _save_progress(self, line):
        """Save current progress to temporary file"""
        if not self.progress_file:
            return

        try:
            with open(self.progress_file, "w") as f:
                json.dump({"line": line, "input_file": self.input_file}, f)
        except Exception as e:
            show_message(f"Failed to save progress: {e}")

    def _clear_progress(self):
        """Clear the progress file on successful completion"""
        if self.progress_file and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
            except Exception as e:
                show_message(f"Failed to remove progress file: {e}")

    def handle_interrupt(self, *args):
        """Handle interrupt signal by setting interrupt flag"""
        self.interrupt_flag = True

    def setup_signal_handlers(self):
        """Set up signal handlers if in main thread"""
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self.handle_interrupt)
            return True
        return False

    def _get_token_limit(self) -> int:
        """
        Get the token limit for the current model.

        Returns:
            int: Token limit for the current model according to https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash
        """
        if "2.0-flash" in self.model_name:
            return 7000
        elif "2.5-flash" in self.model_name or "pro" in self.model_name:
            return 50000
        else:
            return 7000

    def _validate_token_size(self, contents: str) -> bool:
        """
        Validate the token size of the input contents.

        Args:
            contents (str): Input contents to validate

        Returns:
            bool: True if token size is valid, False otherwise
        """
        return True

    current_progress = 0

    def _process_batch(
            self,
            batch: List[SubtitleObject],  # Changed from list[SubtitleObject]
            translated_subtitle: List[Subtitle],  # Changed from list[Subtitle]
            total: int,
            retry_num=3
    ):
        """
        Process a batch of subtitles for translation with accurate progress tracking.

        Args:
            batch (List[SubtitleObject]): Batch of subtitles to translate
            translated_subtitle (List[Subtitle]): List to store translated subtitles
            total (int): Total number of subtitles to translate
        """

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.current_api_key}"

        payload = json.dumps({
            "system_instruction": {
                "parts": [
                    {
                        "text": self.get_instruction(self.target_language, self.description)
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": json.dumps(batch, ensure_ascii=False)
                        }
                    ]
                }
            ]
        })
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()  # Raise an exception for bad status codes

            def clean_json_string(json_string):
                pattern = r'^```json\s*(.*?)\s*```$'
                cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
                return cleaned_string.strip()

            parts = json.loads(response.text)['candidates'][0]['content']['parts']
            result = clean_json_string(''.join(part['text'] for part in parts))

            translated_lines = json_tricks.loads(result)
            chunk_size = len(translated_lines)

            # Process translated lines
            self._process_translated_lines(
                translated_lines=translated_lines,
                translated_subtitle=translated_subtitle,
                batch=batch,
            )

            # Accurately calculate and display progress
            self.current_progress = self.current_progress + chunk_size

            show_progress(id=f'translate_progress_{self.output_file}',
                          header=f'Translating subtitles with Gemini to {self.target_language}...',
                          name='',
                          value=self.current_progress,
                          count=total)

            # Validate translated lines
            if len(translated_lines) != len(batch):
                raise ValueError(
                    f"Gemini returned {len(translated_lines)} lines instead of expected {len(batch)} lines")

            # Clear the batch after successful processing
            batch.clear()

            return self.current_progress

        except Exception as e:
            if retry_num > 0:
                return self._process_batch(batch, translated_subtitle, total, retry_num - 1)
            else:
                show_message(f"Translation request failed: {e}")
                raise e

    @staticmethod
    def _process_translated_lines(
            translated_lines: List[SubtitleObject],  # Changed from list[SubtitleObject]
            translated_subtitle: List[Subtitle],  # Changed from list[Subtitle]
            batch: List[SubtitleObject],  # Changed from list[SubtitleObject]
    ):
        """
        Process the translated lines and update the subtitle list.

        Args:
            translated_lines (List[SubtitleObject]): List of translated lines
            translated_subtitle (List[Subtitle]): List to store translated subtitles
            batch (List[SubtitleObject]): Batch of subtitles to translate
        """

        def _dominant_strong_direction(s: str) -> str:
            """
            Determine the dominant text direction (RTL or LTR) of a string.

            Args:
                s (str): Input string to analyze

            Returns:
                str: 'rtl' if right-to-left is dominant, 'ltr' otherwise
            """
            count = Counter([ud.bidirectional(c) for c in list(s)])
            rtl_count = count["R"] + count["AL"] + count["RLE"] + count["RLI"]
            ltr_count = count["L"] + count["LRE"] + count["LRI"]
            return "rtl" if rtl_count > ltr_count else "ltr"

        for line in translated_lines:
            if "content" not in line or "index" not in line:
                break
            if line["index"] not in [x["index"] for x in batch]:
                raise Exception("Gemini has returned different indices.")
            if _dominant_strong_direction(line["content"]) == "rtl":
                translated_subtitle[int(line["index"])].content = f"\u202b{line['content']}\u202c"
            else:
                translated_subtitle[int(line["index"])].content = line["content"]

    def _translate_with_gemini(self):
        if not self.current_api_key:
            show_message("Please provide a valid Gemini API key.")
            return

        if not self.target_language:
            show_message("Please provide a target language.")
            return

        if not self.input_file:
            show_message("Please provide a subtitle file.")
            return

        self.token_limit = self._get_token_limit()

        try:
            with open(self.input_file, "r", encoding="utf-8") as original_file:
                original_text = original_file.read()
                original_subtitle = list(srt.parse(original_text))

                try:
                    translated_subtitle = original_subtitle.copy()
                except FileNotFoundError:
                    translated_subtitle = original_subtitle.copy()

                # Use with statement for the output file too
                with open(self.output_file, "w", encoding="utf-8") as translated_file:
                    if len(original_subtitle) < self.batch_size:
                        self.batch_size = len(original_subtitle)

                    delay = False
                    delay_time = 30

                    i = self.start_line - 1
                    total = len(original_subtitle)
                    batch = [SubtitleObject(index=str(i), content=original_subtitle[i].content)]

                    i += 1

                    # Save initial progress
                    self._save_progress(i)

                    while (i < total or len(batch) > 0) and not self.interrupt_flag:
                        if i < total and len(batch) < self.batch_size:
                            batch.append(SubtitleObject(index=str(i), content=original_subtitle[i].content))
                            i += 1
                            continue

                        try:
                            if not self._validate_token_size(json.dumps(batch, ensure_ascii=False)):
                                show_message(
                                    f"Token size ({int(self.token_count / 0.9)}) exceeds limit ({self.token_limit}) for {self.model_name}."
                                )
                                user_prompt = "0"
                                while not user_prompt.isdigit() or int(user_prompt) <= 0:
                                    user_prompt = show_message(
                                        f"Please enter a new batch size (current: {self.batch_size}): "
                                    )
                                    if user_prompt.isdigit() and int(user_prompt) > 0:
                                        new_batch_size = int(user_prompt)
                                        decrement = self.batch_size - new_batch_size
                                        if decrement > 0:
                                            for _ in range(decrement):
                                                i -= 1
                                                batch.pop()
                                        self.batch_size = new_batch_size
                                        show_message(f"Batch size updated to {self.batch_size}.")
                                    else:
                                        show_message("Invalid input. Batch size must be a positive integer.")
                                continue

                            start_time = time.time()
                            self._process_batch(batch, translated_subtitle, total)
                            end_time = time.time()

                            # Save progress after each batch
                            self._save_progress(i + 1)

                            if delay and (end_time - start_time < delay_time) and i < total:
                                time.sleep(delay_time - (end_time - start_time))

                        except Exception as e:
                            hide_progress(id=f'translate_progress_{self.output_file}')
                            self._clear_progress()
                            # File will be automatically closed by the with statement
                            raise e

                    # Check if we exited the loop due to an interrupt
                    hide_progress(id=f'translate_progress_{self.output_file}')
                    if self.interrupt_flag:
                        # File will be automatically closed by the with statement
                        self._clear_progress()

                    # Write the final result - this happens inside the with block
                    translated_file.write(srt.compose(translated_subtitle))

                    # Clear progress file on successful completion
                    self._clear_progress()

        except Exception as e:
            hide_progress(id=f'translate_progress_{self.output_file}')
            self._clear_progress()
            raise e

    def translate(self):
        subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
        subs.remove_miscellaneous_events()

        try:
            logger.debug(f'BAZARR is sending subtitle file to Gemini for translation')
            logger.info(f"BAZARR is sending subtitle file to Gemini for translation " + self.source_srt_file)

            # Set up Gemini translator parameters
            self.gemini_api_key = settings.translator.gemini_key
            self.current_api_key = self.gemini_api_key
            self.target_language = language_from_alpha3(self.to_lang)
            self.input_file = self.source_srt_file
            self.output_file = self.dest_srt_file
            self.model_name = settings.translator.gemini_model
            self.description = get_description(self.media_type, self.radarr_id, self.sonarr_series_id)

            # Adjust batch size for different models
            if "2.5-flash" in self.model_name or "pro" in self.model_name:
                self.batch_size = 300

            # Initialize progress tracking file path
            if self.input_file:
                self.progress_file = os.path.join(os.path.dirname(self.input_file), f".{os.path.basename(self.input_file)}.progress")

            # Check for saved progress
            self._check_saved_progress()

            try:
                self._translate_with_gemini()
                add_translator_info(self.dest_srt_file, f"# Subtitles translated with {settings.translator.gemini_model} # ")

                message = f"{language_from_alpha2(self.from_lang)} subtitles translated to {language_from_alpha3(self.to_lang)}."
                result = create_process_result(message, self.video_path, self.orig_to_lang, self.forced, self.hi, self.dest_srt_file, self.media_type)

                if self.media_type == 'series':
                    history_log(action=6, sonarr_series_id=self.sonarr_series_id, sonarr_episode_id=self.sonarr_episode_id, result=result)
                else:
                    history_log_movie(action=6, radarr_id=self.radarr_id, result=result)

                return self.dest_srt_file

            except Exception as e:
                show_message(f'Gemini translation error: {str(e)}')
                hide_progress(id=f'translate_progress_{self.dest_srt_file}')
                return False

        except Exception as e:
            logger.error(f'BAZARR encountered an error translating with Gemini: {str(e)}')
            show_message(f'Gemini translation failed: {str(e)}')
            hide_progress(id=f'translate_progress_{self.dest_srt_file}')
            return False