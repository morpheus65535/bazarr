# coding=utf-8

import logging
import os
import pysubs2
import requests
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from retry.api import retry
from deep_translator.exceptions import TooManyRequests, RequestError

from app.config import settings
from app.jobs_queue import jobs_queue, JobCanceled
from languages.get_languages import language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log

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
            'pb': 'pt-BR',
        }

    def translate(self, job_id=None):
        try:
            jobs_queue.update_job_progress(job_id=job_id, progress_max=1, progress_message=self.source_srt_file)

            subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
            lines_list = [x.plaintext for x in subs]
            lines_list_len = len(lines_list)

            if lines_list_len == 0:
                logger.debug(f'No lines to translate in subtitle file {self.source_srt_file}')
                return self.dest_srt_file

            logger.debug(f'Starting translation for {self.source_srt_file}')
            translated_lines = self._translate_content(lines_list, job_id=job_id)

            if translated_lines is None:
                logger.error(f'Translation failed for {self.source_srt_file}')
                jobs_queue.update_job_progress(job_id=job_id,
                                               progress_message=f'Translation failed for {self.source_srt_file}')
                raise RuntimeError(f'Translation failed for {self.source_srt_file}')

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

            if self.media_type == 'episode':
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

        except JobCanceled:
            jobs_queue.update_job_progress(job_id=job_id, progress_message='Lingarr translation canceled')
            raise
        except Exception as e:
            logger.error(f'BAZARR encountered an error during Lingarr translation for {self.source_srt_file}: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id, progress_message=f'Lingarr translation failed: {str(e)}')
            raise

    def _wait_for_response(self, future: Future, job_id: int | None, title: str,
                           headers: dict[str, str]) -> requests.Response:
        """Wait for the Lingarr content response, cancelling the remote request if the job is cancelled.

        :param future: Future holding the in-flight POST to the Lingarr content endpoint.
        :param job_id: Identifier of the running Bazarr job, or None when not run from the job queue.
        :param title: Title Lingarr stored for the request, used to find it for cancellation.
        :param headers: Request headers, including the API key when one is configured.
        :return: The response returned by Lingarr.
        :raises JobCanceled: If the user cancelled the job while Lingarr was still translating.
        """
        while True:
            try:
                return future.result(timeout=1)
            except FutureTimeoutError:
                if jobs_queue.is_cancel_requested(job_id):
                    self._cancel_remote_request(title, headers)
                    raise JobCanceled()

    def _cancel_remote_request(self, title: str, headers: dict[str, str]) -> None:
        """Ask Lingarr to cancel the active translation request created for this subtitle file.

        Lingarr does not return the request id from the content endpoint, so the request is looked up by
        title. The newest request with that title and no completion time is cancelled. Failures are logged
        and do not stop the Bazarr job from being cancelled.

        :param title: Title Lingarr stored for the request.
        :param headers: Request headers, including the API key when one is configured.
        :return: None
        """
        base_url = settings.translator.lingarr_url
        try:
            listing = requests.get(
                f"{base_url}/api/TranslationRequest/requests",
                params={"searchQuery": title, "orderBy": "CreatedAt", "ascending": "true", "pageNumber": 1},
                headers=headers,
                timeout=30,
            )
            listing.raise_for_status()
            items = listing.json().get("items", [])
            match = next(
                (item for item in items
                 if (item.get("title") or "").strip() == title.strip() and item.get("completedAt") is None),
                None,
            )
            if match is None:
                logger.warning(f'No active Lingarr translation request found to cancel for {self.source_srt_file}')
                return

            cancel_response = requests.post(f"{base_url}/api/TranslationRequest/cancel", json=match,
                                            headers=headers, timeout=30)
            cancel_response.raise_for_status()
            logger.info(f'Cancelled Lingarr translation request {match.get("id")} for {self.source_srt_file}')
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f'Unable to cancel Lingarr translation request for {self.source_srt_file}: {str(e)}')

    # Only retry failures where Lingarr did not accept the request: rate limiting (429) and connection
    # errors. A 5xx or a timeout can happen after Lingarr has already spent a long time translating the
    # file, so re-sending the whole payload would duplicate that work and leave orphaned jobs on Lingarr.
    @retry(exceptions=(TooManyRequests, requests.exceptions.ConnectionError), tries=3, delay=1,
           backoff=2, jitter=(0, 1))
    def _translate_content(self, lines_list, job_id):
        try:
            source_lang = self.language_code_convert_dict.get(self.from_lang, self.from_lang)
            target_lang = self.language_code_convert_dict.get(self.orig_to_lang, self.orig_to_lang)

            lines_payload = []
            for i, line in enumerate(lines_list):
                if not line.strip():
                    continue
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
            # Lingarr content API has no subtitle path field; put basename in title
            # so the Translations UI is not blank when title lookup fails or is empty.
            src_base = os.path.basename(self.source_srt_file or '') or 'subtitle.srt'
            display_title = f'{title} · {src_base}' if (title or '').strip() else src_base

            if self.media_type == 'episode':
                api_media_type = "Episode"
                arr_media_id = self.sonarr_episode_id or 0
            else:
                api_media_type = "Movie"
                arr_media_id = self.radarr_id or 0

            payload = {
                "arrMediaId": arr_media_id,
                "title": display_title,
                "sourceLanguage": source_lang,
                "targetLanguage": target_lang,
                "mediaType": api_media_type,
                "lines": lines_payload,
                # Optional; ignored by older Lingarr, used when content API accepts paths
                "sourceSubtitlePath": self.source_srt_file,
                "translatedSubtitlePath": self.dest_srt_file,
            }

            logger.debug(f'BAZARR is sending {len(lines_payload)} lines to Lingarr for {self.source_srt_file} with full '
                         f'media context')

            headers = {"Content-Type": "application/json"}
            if settings.translator.lingarr_token:
                headers["X-Api-Key"] = settings.translator.lingarr_token

            # The POST runs in a worker thread so this job can notice a user cancellation while Lingarr is busy.
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                requests.post,
                f"{settings.translator.lingarr_url}/api/translate/content",
                json=payload,
                headers=headers,
                timeout=settings.translator.lingarr_timeout  # default 1920 (32 minutes) leaves time for the Lingarr
                # timeout (30 minutes) to occur and get reported to Bazarr instead of silently failing.
            )
            executor.shutdown(wait=False)
            response = self._wait_for_response(future, job_id, display_title, headers)

            if response.status_code == 200:
                translated_batch = response.json()
                # Validate response
                if isinstance(translated_batch, list):
                    for item in translated_batch:
                        if not isinstance(item, dict) or 'position' not in item or 'line' not in item:
                            logger.error(f'Invalid response format from Lingarr API for {self.source_srt_file}: {item}')
                            return None
                    return translated_batch
                else:
                    logger.error(f'Unexpected response format from Lingarr API: {translated_batch}')
                    return None
            elif response.status_code == 401:
                raise RequestError("Authentication failed: Invalid or missing API key")
            elif response.status_code == 429:
                raise TooManyRequests("Rate limit exceeded")
            elif response.status_code >= 500:
                raise RequestError(f"Server error: {response.status_code}")
            else:
                logger.debug(f'Lingarr API error for {self.source_srt_file}: {response.status_code} - {response.text}')
                return None

        except JobCanceled:
            logger.info(f'BAZARR canceled Lingarr translation for {self.source_srt_file}')
            raise
        except requests.exceptions.Timeout:
            logger.error(f'Lingarr API request timed out for {self.source_srt_file}')
            raise RequestError("Request timed out")
        except requests.exceptions.ConnectionError:
            logger.error(f'Lingarr API connection error for {self.source_srt_file}')
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f'Lingarr API request failed for {self.source_srt_file}: {str(e)}')
            raise
        except (TooManyRequests, RequestError) as e:
            logger.error(f'Lingarr API error for {self.source_srt_file}: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id, progress_message=f'Lingarr API error: {str(e)}')
            raise
        except Exception as e:
            logger.error(f'Unexpected error in Lingarr translation for {self.source_srt_file}: {str(e)}')
            jobs_queue.update_job_progress(job_id=job_id, progress_message=f'Translation error: {str(e)}')
            raise
