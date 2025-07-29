# coding=utf-8

import logging
import pysubs2
import srt
import requests

from retry.api import retry
from subliminal_patch.core import get_subtitle_path
from subzero.language import Language
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound

from app.config import settings
from app.database import TableShows, TableEpisodes, TableMovies, database, select
from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from app.event_handler import show_progress, hide_progress, show_message
from utilities.path_mappings import path_mappings

from ..core.translator_utils import add_translator_info, create_process_result


class LingarrTranslatorService:

    def __init__(self, source_srt_file, dest_srt_file, lang_obj, to_lang, from_lang, media_type,
                 video_path, orig_to_lang, forced, hi, sonarr_series_id, sonarr_episode_id,
                 radarr_id):
        self.source_srt_file = source_srt_file
        self.dest_srt_file = dest_srt_file
        self.lang_obj = lang_obj
        self.to_lang = to_lang
        self.from_lang = from_lang
        self.media_type = media_type
        self.video_path = video_path
        self.orig_to_lang = orig_to_lang
        self.forced = forced
        self.hi = hi
        self.sonarr_series_id = sonarr_series_id
        self.sonarr_episode_id = sonarr_episode_id
        self.radarr_id = radarr_id
        self.language_code_convert_dict = {
            'he': 'iw',
            'zh': 'zh-CN',
            'zt': 'zh-TW',
        }

    def translate(self):
        try:
            subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
            lines_list = [x.plaintext for x in subs]
            lines_list_len = len(lines_list)

            if lines_list_len == 0:
                logging.debug('No lines to translate in subtitle file')
                return self.dest_srt_file

            lines_payload = []
            for i, line in enumerate(lines_list):
                lines_payload.append({
                    "position": i,
                    "line": line
                })

            logging.debug(f'Starting translation for {self.source_srt_file}')
            translated_lines = self._translate_batch(lines_payload)

            if translated_lines is None:
                logging.error(f'Translation failed for {self.source_srt_file}')
                show_message(f'Translation failed for {self.source_srt_file}')
                return False

            logging.debug(f'BAZARR saving Lingarr translated subtitles to {self.dest_srt_file}')
            translation_map = {}
            for item in translated_lines:
                if isinstance(item, dict) and 'position' in item and 'line' in item:
                    translation_map[item['position']] = item['line']

            for i, line in enumerate(subs):
                if i in translation_map and translation_map[i]:
                    line.text = translation_map[i]

            try:
                subs.save(self.dest_srt_file)
                add_translator_info(self.dest_srt_file, f"# Subtitles translated with Lingarr # ")
            except OSError:
                logging.error(f'BAZARR is unable to save translated subtitles to {self.dest_srt_file}')
                show_message(f'Translation failed: Unable to save translated subtitles to {self.dest_srt_file}')
                raise OSError

            message = f"{language_from_alpha2(self.from_lang)} subtitles translated to {language_from_alpha3(self.to_lang)} using Lingarr."
            result = create_process_result(message, self.video_path, self.orig_to_lang, self.forced, self.hi, self.dest_srt_file, self.media_type)

            if self.media_type == 'series':
                history_log(action=6, sonarr_series_id=self.sonarr_series_id, sonarr_episode_id=self.sonarr_episode_id,
                            result=result)
            else:
                history_log_movie(action=6, radarr_id=self.radarr_id, result=result)

            return self.dest_srt_file

        except Exception as e:
            logging.error(f'BAZARR encountered an error during Lingarr translation: {str(e)}')
            show_message(f'Lingarr translation failed: {str(e)}')
            hide_progress(id=f'translate_progress_{self.dest_srt_file}')
            return False

    @retry(exceptions=(TooManyRequests, RequestError, requests.exceptions.RequestException), tries=6, delay=1, backoff=2, jitter=(0, 1))
    def _translate_batch(self, lines_payload):
        try:
            source_lang = self.language_code_convert_dict.get(self.from_lang, self.from_lang)
            target_lang = self.language_code_convert_dict.get(self.orig_to_lang, self.orig_to_lang)

            payload = {
                "sourceLanguage": source_lang,
                "targetLanguage": target_lang,
                "lines": lines_payload
            }

            logging.debug(f'BAZARR is sending {len(lines_payload)} lines to Lingarr in a single batch request')

            # Some services can only perform a single line translation, so we set a high timeout
            response = requests.post(
                f"{settings.translator.lingarr_url}/api/translate/content",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=600
            )

            if response.status_code == 200:
                translated_batch = response.json()
                # Validate response
                if isinstance(translated_batch, list):
                    for item in translated_batch:
                        if not isinstance(item, dict) or 'position' not in item or 'line' not in item:
                            logging.error(f'Invalid response format from Lingarr API: {item}')
                            return None
                    return translated_batch
                else:
                    logging.error(f'Unexpected response format from Lingarr API: {translated_batch}')
                    return None
            elif response.status_code == 429:
                raise TooManyRequests("Rate limit exceeded")
            elif response.status_code >= 500:
                raise RequestError(f"Server error: {response.status_code}")
            else:
                logging.debug(f'Lingarr API error: {response.status_code} - {response.text}')
                return None

        except requests.exceptions.Timeout:
            logging.debug('Lingarr API request timed out')
            raise RequestError("Request timed out")
        except requests.exceptions.ConnectionError:
            logging.debug('Lingarr API connection error')
            raise RequestError("Connection error")
        except requests.exceptions.RequestException as e:
            logging.debug(f'Lingarr API request failed: {str(e)}')
            raise
        except (TooManyRequests, RequestError) as e:
            logging.error(f'Lingarr API error after retries: {str(e)}')
            show_message(f'Lingarr API error: {str(e)}')
            raise
        except Exception as e:
            logging.error(f'Unexpected error in Lingarr translation: {str(e)}')
            show_message(f'Translation error: {str(e)}')
            raise
