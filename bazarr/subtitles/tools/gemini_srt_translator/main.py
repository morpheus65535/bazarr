import json
import re

import json_repair
import os
import signal
import threading
import time
import typing
import unicodedata as ud
from collections import Counter
from app.event_handler import show_progress, hide_progress, show_message


import srt
from srt import Subtitle
import requests

from .helpers import get_instruction


class SubtitleObject(typing.TypedDict):
    """
    TypedDict for subtitle objects used in translation
    """

    index: str
    content: str


class GeminiSRTTranslator:
    """
    A translator class that uses Gemini API to translate subtitles.
    """

    def __init__(
            self,
            gemini_api_key: str = None,
            gemini_api_key2: str = None,
            target_language: str = None,
            input_file: str = None,
            output_file: str = None,
            start_line: int = 1,
            description: str = None,
            model_name: str = "gemini-2.0-flash",
            batch_size: int = 100,
            free_quota: bool = True,
            use_colors: bool = True,
            error_log: bool = False,
    ):
        """
        Initialize the translator with necessary parameters.

        Args:
            gemini_api_key (str): Primary Gemini API key
            gemini_api_key2 (str): Secondary Gemini API key for additional quota
            target_language (str): Target language for translation
            input_file (str): Path to input subtitle file
            output_file (str): Path to output translated subtitle file
            start_line (int): Line number to start translation from
            description (str): Additional instructions for translation
            model_name (str): Gemini model to use
            batch_size (int): Number of subtitles to process in each batch
            free_quota (bool): Whether to use free quota (affects rate limiting)
            use_colors (bool): Whether to use colored output
        """

        self.input_file = input_file

        if not input_file:
            self.output_file = output_file or "translated.srt"
        elif not output_file:
            try:
                self.output_file = ".".join(input_file.split(".")[:-1]) + "_translated.srt"
            except:
                self.output_file = "translated.srt"
        else:
            self.output_file = output_file

        self.gemini_api_key = gemini_api_key
        self.gemini_api_key2 = gemini_api_key2
        self.current_api_key = gemini_api_key
        self.current_api_number = 1
        self.backup_api_number = 2
        self.target_language = target_language
        self.input_file = input_file
        self.start_line = start_line
        self.description = description
        self.model_name = model_name
        self.batch_size = batch_size
        self.free_quota = free_quota
        self.error_log = error_log
        self.token_limit = 0
        self.token_count = 0
        self.interrupt_flag = False  # Flag to check for interruption

        # Initialize progress tracking file path
        self.progress_file = None
        if input_file:
            self.progress_file = os.path.join(os.path.dirname(input_file), f".{os.path.basename(input_file)}.progress")

        # Check for saved progress
        self._check_saved_progress()

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

    def translate(self):
        """
        Main translation method. Reads the input subtitle file, translates it in batches,
        and writes the translated subtitles to the output file.
        """
        if not self.current_api_key:
            show_message("Please provide a valid Gemini API key.")
            exit(0)

        if not self.target_language:
            show_message("Please provide a target language.")
            exit(0)

        if not self.input_file:
            show_message("Please provide a subtitle file.")
            exit(0)

        self.token_limit = self._get_token_limit()

        # Setup signal handlers if possible
        is_main_thread = self.setup_signal_handlers()

        with open(self.input_file, "r", encoding="utf-8") as original_file:
            original_text = original_file.read()
            original_subtitle = list(srt.parse(original_text))
            try:
                translated_subtitle = original_subtitle.copy()

            except FileNotFoundError:
                translated_subtitle = original_subtitle.copy()

            if len(original_subtitle) != len(translated_subtitle):
                show_message(
                    f"Number of lines of existing translated file does not match the number of lines in the original file."
                )
                exit(0)

            translated_file = open(self.output_file, "w", encoding="utf-8")

            if self.start_line > len(original_subtitle) or self.start_line < 1:
                show_message(f"Start line must be between 1 and {len(original_subtitle)}. Please try again.")
                exit(0)

            if len(original_subtitle) < self.batch_size:
                self.batch_size = len(original_subtitle)

            delay = False
            delay_time = 30

            if "pro" in self.model_name and self.free_quota:
                delay = True
                if not self.gemini_api_key2:
                    show_message("Pro model and free user quota detected.\n")
                else:
                    delay_time = 15
                    show_message("Pro model and free user quota detected, using secondary API key if needed.\n")

            i = self.start_line - 1
            total = len(original_subtitle)
            batch = [SubtitleObject(index=str(i), content=original_subtitle[i].content)]

            i += 1

            if self.gemini_api_key2:
                show_message(f"Starting with API Key {self.current_api_number}")

            # Save initial progress
            self._save_progress(i)

            last_time = 0
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
                    raise e

            # Check if we exited the loop due to an interrupt
            hide_progress(id=f'translate_progress_{self.output_file}')
            if self.interrupt_flag:
                return


            translated_file.write(srt.compose(translated_subtitle))

            # Clear progress file on successful completion
            self._clear_progress()

    def _get_token_limit(self) -> int:
        """
        Get the token limit for the current model.

        Returns:
            int: Token limit for the current model
        """
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
            batch: list[SubtitleObject],
            translated_subtitle: list[Subtitle],
            total: int,
    ):
        """
        Process a batch of subtitles for translation with accurate progress tracking.

        Args:
            batch (list[SubtitleObject]): Batch of subtitles to translate
            translated_subtitle (list[Subtitle]): List to store translated subtitles
            total (int): Total number of subtitles to translate
        """

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.current_api_key}"

        payload = json.dumps({
            "system_instruction": {
                "parts": [
                    {
                        "text": get_instruction(self.target_language, self.description)
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

            translated_lines = json_repair.loads(result)
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

        except requests.RequestException as e:
            # More comprehensive error handling
            print(f"Translation request failed: {e}")
            raise e

        except (json.JSONDecodeError, json_repair.JSONDecodeError) as e:
            print(f"Error parsing JSON response: {e}")
            exit(0)
            raise

        except Exception as e:
            exit(0)
            throw(e)
            raise

    def _process_translated_lines(
            self,
            translated_lines: list[SubtitleObject],
            translated_subtitle: list[Subtitle],
            batch: list[SubtitleObject],
    ):
        """
        Process the translated lines and update the subtitle list.

        Args:
            translated_lines (list[SubtitleObject]): List of translated lines
            translated_subtitle (list[Subtitle]): List to store translated subtitles
            batch (list[SubtitleObject]): Batch of subtitles to translate
        """
        for line in translated_lines:
            if "content" not in line or "index" not in line:
                break
            if line["index"] not in [x["index"] for x in batch]:
                raise Exception("Gemini has returned different indices.")
            if self._dominant_strong_direction(line["content"]) == "rtl":
                translated_subtitle[int(line["index"])].content = f"\u202b{line['content']}\u202c"
            else:
                translated_subtitle[int(line["index"])].content = line["content"]

    def _dominant_strong_direction(self, s: str) -> str:
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