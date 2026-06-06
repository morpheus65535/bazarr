# coding=utf-8

import json
import re
import os
import signal
import threading
import time
import typing
import logging
import random
import unicodedata as ud

import srt
import pysubs2
import requests

from collections import Counter
from typing import List
from srt import Subtitle

from app.config import settings
from sonarr.history import history_log
from radarr.history import history_log_movie
from subtitles.processing import ProcessSubtitlesResult
from app.jobs_queue import jobs_queue
from languages.get_languages import language_from_alpha2, language_from_alpha3
from ..core.translator_utils import add_translator_info, get_description, create_process_result

logger = logging.getLogger(__name__)


class SubtitleObject(typing.TypedDict):
    index: str
    content: str


class GeminiTranslatorService:

    def __init__(
        self,
        source_srt_file,
        dest_srt_file,
        to_lang,
        media_type,
        sonarr_series_id,
        sonarr_episode_id,
        radarr_id,
        forced,
        hi,
        video_path,
        from_lang,
        orig_to_lang,
        **kwargs
    ):
        self.source_srt_file = source_srt_file
        self.dest_srt_file = dest_srt_file
        self.to_lang = to_lang
        self.media_type = media_type
        self.sonarr_series_id = sonarr_series_id
        self.sonarr_episode_id = sonarr_episode_id
        self.radarr_id = radarr_id
        self.from_lang = from_lang
        self.video_path = video_path
        self.forced = forced
        self.hi = hi
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

        # Smaller default batch is more reliable for Gemini JSON output.
        self.batch_size = 50

        self.free_quota = True
        self.error_log = False
        self.token_limit = 0
        self.token_count = 0
        self.interrupt_flag = False
        self.progress_file = None
        self.current_progress = 0
        self.job_id = None

        # Gemini summary counters
        self.total_requests = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_total_tokens = 0
        self.translation_start_time = None

    def _progress_log(self, message: str):
        logger.info(f"[GeminiTranslator] {message}")

        try:
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_message=message
            )
        except Exception:
            logger.exception("[GeminiTranslator] Failed to update Bazarr progress message")

    def translate(self, job_id):
        self.job_id = job_id

        try:
            pysubs2.load(self.source_srt_file, encoding="utf-8").remove_miscellaneous_events()

            logger.info(f"BAZARR is sending subtitle file to Gemini for translation {self.source_srt_file}")

            self.gemini_api_key = settings.translator.gemini_key
            self.current_api_key = self.gemini_api_key
            self.target_language = language_from_alpha3(self.to_lang)
            self.input_file = self.source_srt_file
            self.output_file = self.dest_srt_file
            self.model_name = settings.translator.gemini_model
            self.description = get_description(self.media_type, self.radarr_id, self.sonarr_series_id)

            if "2.5-flash" in self.model_name or "pro" in self.model_name:
                self.batch_size = 10

            if self.input_file:
                self.progress_file = os.path.join(
                    os.path.dirname(self.input_file),
                    f".{os.path.basename(self.input_file)}.progress"
                )

            self._check_saved_progress()

            try:
                self._translate_with_gemini()
                add_translator_info(
                    self.dest_srt_file,
                    f"# Subtitles translated with {settings.translator.gemini_model} # "
                )
            except Exception as e:
                jobs_queue.update_job_progress(
                    job_id=job_id,
                    progress_message=f"Gemini translation error: {str(e)}"
                )
                raise

        except Exception as e:
            logger.error(f"BAZARR encountered an error translating with Gemini: {str(e)}")
            return False

        message = (
            f"{language_from_alpha2(self.from_lang)} subtitles translated to "
            f"{language_from_alpha3(self.to_lang)}."
        )

        result = create_process_result(
            message,
            self.video_path,
            self.orig_to_lang,
            self.forced,
            self.hi,
            self.dest_srt_file,
            self.media_type
        )

        if self.media_type == "series":
            history_log(
                action=6,
                sonarr_series_id=self.sonarr_series_id,
                sonarr_episode_id=self.sonarr_episode_id,
                result=result
            )
        else:
            history_log_movie(action=6, radarr_id=self.radarr_id, result=result)

        return True

    def _check_saved_progress(self):
        if not self.progress_file or not os.path.exists(self.progress_file):
            return

        if self.start_line != 1:
            return

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                input_file = data.get("input_file")

                if input_file != self.input_file:
                    jobs_queue.update_job_progress(
                        job_id=self.job_id,
                        progress_message=f"Found progress file for different subtitle: {input_file}. Ignoring."
                    )
                    return

                if os.path.exists(self.output_file):
                    os.remove(self.output_file)

        except Exception as e:
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_message=f"Error reading progress file: {e}"
            )

    def _save_progress(self, line):
        if not self.progress_file:
            return

        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump({"line": line, "input_file": self.input_file}, f)
        except Exception as e:
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_message=f"Failed to save progress: {e}"
            )

    def _clear_progress(self):
        if self.progress_file and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
            except Exception as e:
                jobs_queue.update_job_progress(
                    job_id=self.job_id,
                    progress_message=f"Failed to remove progress file: {e}"
                )

    def handle_interrupt(self, *args):
        self.interrupt_flag = True

    def setup_signal_handlers(self):
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self.handle_interrupt)
            return True
        return False

    def _get_token_limit(self) -> int:
        if "2.0-flash" in self.model_name:
            return 7000
        if "2.5-flash" in self.model_name or "pro" in self.model_name:
            return 50000
        return 7000

    def _validate_token_size(self, contents: str) -> bool:
        return True

    def _retry_delay(self, attempt: int, base_delay_seconds: int = 2) -> int:
        return min(base_delay_seconds * (2 ** (attempt - 1)), 180) + random.randint(0, 10)

    def _extract_json_array(self, text: str):
        text = text.strip()

        text = re.sub(r"^```json\s*", "", text, flags=re.I)
        text = re.sub(r"^```\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)

        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON array found in Gemini response.")

        json_text = text[start:end + 1]
        data = json.loads(json_text)

        if not isinstance(data, list):
            raise ValueError("Gemini response is not a JSON array.")

        return data

    def _validate_translated_lines(self, batch: List[SubtitleObject], translated_lines: List[SubtitleObject]):
        original_indexes = [str(x["index"]) for x in batch]
        translated_indexes = []

        for item in translated_lines:
            if not isinstance(item, dict):
                continue

            if "index" in item:
                translated_indexes.append(str(item["index"]))

            if "index" not in item or "content" not in item:
                raise ValueError("Gemini response item missing index or content.")

        missing = [x for x in original_indexes if x not in translated_indexes]
        extra = [x for x in translated_indexes if x not in original_indexes]
        duplicates = [
            index for index, count in Counter(translated_indexes).items()
            if count > 1
        ]

        if missing or extra or duplicates or len(translated_indexes) != len(original_indexes):
            raise ValueError(
                f"Invalid Gemini response. "
                f"Missing={missing}, Extra={extra}, Duplicates={duplicates}, "
                f"Returned={len(translated_indexes)}, Expected={len(original_indexes)}"
            )

    def _build_gemini_payload(self, batch: List[SubtitleObject], strict: bool = False) -> str:
        temperature = 0.0 if strict else 0.2
        top_p = 0.8 if strict else 0.9

        style_rules = f"""
Use natural conversational {self.target_language} subtitle style.
Do not translate word-for-word.
Preserve emotion, humor, sarcasm, and character tone.
Use short readable subtitle lines.
Use common spoken {self.target_language} where appropriate.
"""

        prompt = f"""
Translate this JSON subtitle chunk into {self.target_language}.

ABSOLUTE FORMAT RULES:
- Return JSON only.
- Return one JSON array only.
- Do not use markdown.
- Keep every object.
- Keep every index exactly the same.
- Do not skip any index.
- Do not add any index.
- Do not reorder objects.
- Do not merge objects.
- Do not split objects.
- Translate only the "content" field.
- Keep "index" as string.
- Keep the same number of objects.

Style:
{style_rules}

Input JSON:
{json.dumps(batch, ensure_ascii=False)}
"""

        if self.description:
            prompt += f"\nAdditional context:\n{self.description}\n"

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are a professional subtitle translator. "
                            "You must return valid JSON only. "
                            "Preserve every index exactly and translate only content values."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "index": {
                                "type": "STRING"
                            },
                            "content": {
                                "type": "STRING"
                            }
                        },
                        "required": ["index", "content"]
                    }
                }
            }
        }

        return json.dumps(payload, ensure_ascii=False)

    def _call_gemini(
        self,
        batch: List[SubtitleObject],
        max_attempts: int = 5,
        strict: bool = False
    ) -> List[SubtitleObject]:

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:generateContent?key={self.current_api_key}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        retry_http_codes = {408, 409, 429, 500, 502, 503, 504}

        for attempt in range(1, max_attempts + 1):
            if self.interrupt_flag:
                raise RuntimeError("Translation interrupted.")

            payload = self._build_gemini_payload(batch, strict=strict)

            self.total_requests += 1

            if attempt == 1:
                self._progress_log(
                    f"Sending subtitles to Gemini | BatchSize={len(batch)} | Strict={strict}"
                )

            response = requests.post(
                url,
                headers=headers,
                data=payload.encode("utf-8"),
                timeout=300
            )

            if 200 <= response.status_code < 300:
                data = response.json()

                usage = data.get("usageMetadata", {})
                self.total_input_tokens += int(usage.get("promptTokenCount", 0) or 0)
                self.total_output_tokens += int(usage.get("candidatesTokenCount", 0) or 0)
                self.total_total_tokens += int(usage.get("totalTokenCount", 0) or 0)

                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(part.get("text", "") for part in parts)

                if not text.strip():
                    raise ValueError("Gemini returned an empty response.")

                return self._extract_json_array(text)

            if response.status_code in retry_http_codes and attempt < max_attempts:
                delay = self._retry_delay(attempt)

                self._progress_log(
                    f"Gemini temporary error {response.status_code}. "
                    f"Attempt {attempt}/{max_attempts}. Retrying in {delay}s..."
                )

                time.sleep(delay)
                continue

            logger.error(
                f"[GeminiTranslator] Gemini HTTP {response.status_code}: "
                f"{response.text[:2000]}"
            )
            response.raise_for_status()

        raise RuntimeError("Gemini request failed unexpectedly.")

    def _process_batch(
        self,
        batch: List[SubtitleObject],
        translated_subtitle: List[Subtitle],
        total: int,
        retry_num=3
    ):
        try:
            translated_lines = self._call_gemini(batch, max_attempts=8, strict=False)
            self._validate_translated_lines(batch, translated_lines)

        except Exception as first_error:
            self._progress_log(
                f"Gemini validation failed. Retrying with strict JSON mode. Error={first_error}"
            )

            try:
                translated_lines = self._call_gemini(batch, max_attempts=3, strict=True)
                self._validate_translated_lines(batch, translated_lines)

            except Exception as strict_error:
                if len(batch) > 25:
                    jobs_queue.update_job_progress(
                        job_id=self.job_id,
                        progress_message="Strict retry failed. Splitting batch into chunks of 25."
                    )

                    sub_batches = [
                        batch[i:i + 25]
                        for i in range(0, len(batch), 25)
                    ]

                    for sub_batch in sub_batches:
                        self._process_batch(sub_batch, translated_subtitle, total)

                    batch.clear()
                    return self.current_progress

                raise strict_error

        self._process_translated_lines(
            translated_lines=translated_lines,
            translated_subtitle=translated_subtitle,
            batch=batch
        )

        self.current_progress += len(batch)

        jobs_queue.update_job_progress(
            job_id=self.job_id,
            progress_value=self.current_progress
        )

        batch.clear()
        return self.current_progress

    @staticmethod
    def _process_translated_lines(
        translated_lines: List[SubtitleObject],
        translated_subtitle: List[Subtitle],
        batch: List[SubtitleObject]
    ):
        def _dominant_strong_direction(s: str) -> str:
            count = Counter([ud.bidirectional(c) for c in list(s)])
            rtl_count = count["R"] + count["AL"] + count["RLE"] + count["RLI"]
            ltr_count = count["L"] + count["LRE"] + count["LRI"]
            return "rtl" if rtl_count > ltr_count else "ltr"

        batch_indexes = {str(x["index"]) for x in batch}

        for line in translated_lines:
            index = str(line["index"])

            if index not in batch_indexes:
                raise ValueError("Gemini returned different indices.")

            content = str(line["content"]).strip()

            if _dominant_strong_direction(content) == "rtl":
                translated_subtitle[int(index)].content = f"\u202b{content}\u202c"
            else:
                translated_subtitle[int(index)].content = content

    def _translate_with_gemini(self):
        if not self.current_api_key:
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_message="Please provide a valid Gemini API key."
            )
            return

        if not self.target_language:
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_message="Please provide a target language."
            )
            return

        if not self.input_file:
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_message="Please provide a subtitle file."
            )
            return

        self.token_limit = self._get_token_limit()
        self.translation_start_time = time.time()
        total = 0

        try:
            with open(self.input_file, "r", encoding="utf-8") as original_file:
                original_text = original_file.read()
                original_subtitle = list(srt.parse(original_text))
                translated_subtitle = original_subtitle.copy()

            if len(original_subtitle) < self.batch_size:
                self.batch_size = len(original_subtitle)

            delay = True
            delay_time = 5

            i = self.start_line - 1
            total = len(original_subtitle)

            self._progress_log(
                f"Gemini translation started | "
                f"Model={self.model_name} | "
                f"Target={self.target_language} | "
                f"Subtitles={total} | "
                f"BatchSize={self.batch_size}"
            )

            if total == 0:
                raise ValueError("No subtitle lines found.")

            batch = []

            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_max=total,
                progress_message=self.source_srt_file
            )

            while (i < total or len(batch) > 0) and not self.interrupt_flag:
                if i < total and len(batch) < self.batch_size:
                    batch.append(
                        SubtitleObject(
                            index=str(i),
                            content=original_subtitle[i].content
                        )
                    )
                    i += 1
                    continue

                if not batch:
                    continue

                try:
                    if not self._validate_token_size(json.dumps(batch, ensure_ascii=False)):
                        jobs_queue.update_job_progress(
                            job_id=self.job_id,
                            progress_message=(
                                f"Token size exceeds limit for {self.model_name}. "
                                f"Please reduce batch size."
                            )
                        )
                        self.batch_size = max(1, self.batch_size // 2)
                        continue

                    start_time = time.time()

                    self._process_batch(batch, translated_subtitle, total)

                    end_time = time.time()

                    self._save_progress(i + 1)

                    if delay and (end_time - start_time < delay_time) and i < total:
                        time.sleep(delay_time - (end_time - start_time))

                except Exception as e:
                    self._clear_progress()
                    raise e

            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_value=total
            )

            if self.interrupt_flag:
                self._clear_progress()
                raise RuntimeError("Translation interrupted.")

            with open(self.output_file, "w", encoding="utf-8") as translated_file:
                translated_file.write(srt.compose(translated_subtitle))

            elapsed = round(time.time() - self.translation_start_time, 2) if self.translation_start_time else 0

            self._progress_log(
                f"Gemini translation completed successfully | "
                f"Subtitles={total} | "
                f"Requests={self.total_requests} | "
                f"InputTokens={self.total_input_tokens:,} | "
                f"OutputTokens={self.total_output_tokens:,} | "
                f"TotalTokens={self.total_total_tokens:,} | "
                f"Duration={elapsed}s"
            )

            logger.info(
                f"[GeminiTranslator] Summary | "
                f"Model={self.model_name} | "
                f"Subtitles={total} | "
                f"Requests={self.total_requests} | "
                f"InputTokens={self.total_input_tokens:,} | "
                f"OutputTokens={self.total_output_tokens:,} | "
                f"TotalTokens={self.total_total_tokens:,} | "
                f"Duration={elapsed}s"
            )

            self._clear_progress()

        except Exception as e:
            logger.error(f"BAZARR encountered an error translating with Gemini: {str(e)}")
            jobs_queue.update_job_progress(
                job_id=self.job_id,
                progress_value=total,
                progress_message=f"Gemini translation failed: {str(e)}"
            )
            self._clear_progress()
            raise e