# coding=utf-8

import logging
import pysubs2
import requests

from retry.api import retry
from deep_translator.exceptions import TooManyRequests, RequestError

from app.config import settings
from app.database import TableShows, TableEpisodes, TableMovies, database, select
from app.jobs_queue import jobs_queue
from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from utilities.path_mappings import path_mappings

from ..core.translator_utils import add_translator_info, create_process_result, get_title

logger = logging.getLogger(__name__)


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
            'zh': 'zh-CN',
            'zt': 'zh-TW',
        }

    def translate(self, job_id=None):
        try:
            jobs_queue.update_job_progress(job_id=job_id, progress_max=1, progress_message=self.source_srt_file)

            subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
            lines_list = [x.plaintext for x in subs]
            lines_list_len = len(lines_list)

            if lines_list_len == 0:
                logger.debug('No lines to translate in subtitle file')
                return self.dest_srt_file

            logger.debug(f'Starting translation for {self.source_srt_file}')
            translated_lines = self._translate_content(lines_list, job_id=job_id)

            if translated_lines is None:
                logger.error(f'Translation failed for {self.source_srt_file}')
                jobs_queue.update_job_progress(job_id=job_id,
                                               progress_message=f'Translation failed for {self.source_srt_file}')
                return False

            logger.debug(f'BAZARR saving Lingarr translated subtitles to {self.dest_srt_file}')
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
                logger.error(f'BAZARR is unable to save translated subtitles to {self.dest_srt_file}')
                jobs_queue.update_job_progress(job_id=job_id,
                                               progress_message=f'Translation failed: Unable to save translated '
                                                                f'subtitles to {self.dest_srt_file}')
                raise OSError

            message = (f"{language_from_alpha2(self.from_lang)} subtitles translated to "
                       f"{language_from_alpha3(self.to_lang)} using Lingarr.")
            result = create_process_result(message, self.video_path, self.orig_to_lang, self.forced, self.hi,
                                           self.dest_srt_file, self.media_type)

            if self.media_type == 'series':
                history_log(action=6,
                            sonarr_series_id=self.sonarr_series_id,
                            sonarr_episode_id=self.sonarr_episode_id,
                            result=result)
            else:
                history_log_movie(action=6,
                                  radarr_id=self.radarr_id,
                                  result=result)

            jobs_queue.update_job_progress(job_id=job_id, progress_value='max')

            return self.dest_srt_file

        except Exception as e:
            logger.error(f'BAZARR encountered an error during Lingarr translation: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id, progress_message=f'Lingarr translation failed: {str(e)}')
            return False

    @retry(exceptions=(TooManyRequests, RequestError, requests.exceptions.RequestException), tries=3, delay=1,
           backoff=2, jitter=(0, 1))
    def _translate_content(self, lines_list, job_id):
        try:
            source_lang = self.language_code_convert_dict.get(self.from_lang, self.from_lang)
            target_lang = self.language_code_convert_dict.get(self.orig_to_lang, self.orig_to_lang)

            lines_payload = []
            for i, line in enumerate(lines_list):
                lines_payload.append({
                    "position": i,
                    "line": line
                })

            title = get_title(
                media_type=self.media_type,
                radarr_id=self.radarr_id,
                sonarr_series_id=self.sonarr_series_id,
                sonarr_episode_id=self.sonarr_episode_id
            )

            if self.media_type == 'series':
                api_media_type = "Episode"
                arr_media_id = self.sonarr_series_id or 0
            else:
                api_media_type = "Movie"
                arr_media_id = self.radarr_id or 0

            payload = {
                "arrMediaId": arr_media_id,
                "title": title,
                "sourceLanguage": source_lang,
                "targetLanguage": target_lang,
                "mediaType": api_media_type,
                "lines": lines_payload
            }

            logger.debug(f'BAZARR is sending {len(lines_payload)} lines to Lingarr with full media context')

            response = requests.post(
                f"{settings.translator.lingarr_url}/api/translate/content",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=1800
            )

            if response.status_code == 200:
                translated_batch = response.json()
                # Validate response
                if isinstance(translated_batch, list):
                    for item in translated_batch:
                        if not isinstance(item, dict) or 'position' not in item or 'line' not in item:
                            logger.error(f'Invalid response format from Lingarr API: {item}')
                            return None
                    return translated_batch
                else:
                    logger.error(f'Unexpected response format from Lingarr API: {translated_batch}')
                    return None
            elif response.status_code == 429:
                raise TooManyRequests("Rate limit exceeded")
            elif response.status_code >= 500:
                raise RequestError(f"Server error: {response.status_code}")
            else:
                logger.debug(f'Lingarr API error: {response.status_code} - {response.text}')
                return None

        except requests.exceptions.Timeout:
            logger.debug('Lingarr API request timed out')
            raise RequestError("Request timed out")
        except requests.exceptions.ConnectionError:
            logger.debug('Lingarr API connection error')
            raise RequestError("Connection error")
        except requests.exceptions.RequestException as e:
            logger.debug(f'Lingarr API request failed: {str(e)}')
            raise
        except (TooManyRequests, RequestError) as e:
            logger.error(f'Lingarr API error after retries: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id, progress_message=f'Lingarr API error: {str(e)}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error in Lingarr translation: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id, progress_message=f'Translation error: {str(e)}')
            raise
