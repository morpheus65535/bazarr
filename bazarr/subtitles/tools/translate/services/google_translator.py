# coding=utf-8

import logging
import srt
import pysubs2

from retry.api import retry
from app.config import settings
from ..core.translator_utils import add_translator_info, create_process_result
from sonarr.history import history_log
from radarr.history import history_log_movie
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor
from utilities.path_mappings import path_mappings
from subtitles.processing import ProcessSubtitlesResult
from app.event_handler import show_progress, hide_progress, show_message
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3


class GoogleTranslatorService:

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
            subs.remove_miscellaneous_events()
            lines_list = [x.plaintext for x in subs]
            lines_list_len = len(lines_list)

            translated_lines = []
            logging.debug(f'starting translation for {self.source_srt_file}')
            def translate_line(line_id, subtitle_line):
                try:
                    translated_text = self._translate_text(subtitle_line)
                    translated_lines.append({'id': line_id, 'line': translated_text})
                except TranslationNotFound:
                    logging.debug(f'Unable to translate line {subtitle_line}')
                    translated_lines.append({'id': line_id, 'line': subtitle_line})
                finally:
                    show_progress(id=f'translate_progress_{self.dest_srt_file}',
                                  header=f'Translating subtitles lines to {language_from_alpha3(self.to_lang)} using Google Translate...',
                                  name='',
                                  value=len(translated_lines),
                                  count=lines_list_len)

            logging.debug(f'BAZARR is sending {lines_list_len} blocks to Google Translate')
            pool = ThreadPoolExecutor(max_workers=10)
            futures = []
            for i, line in enumerate(lines_list):
                future = pool.submit(translate_line, i, line)
                futures.append(future)
            pool.shutdown(wait=True)
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in translation task: {e}")

            for i, line in enumerate(translated_lines):
                lines_list[line['id']] = line['line']

            show_progress(id=f'translate_progress_{self.dest_srt_file}',
                          header=f'Translating subtitles lines to {language_from_alpha3(self.to_lang)}...',
                          name='',
                          value=lines_list_len,
                          count=lines_list_len)

            logging.debug(f'BAZARR saving translated subtitles to {self.dest_srt_file}')
            for i, line in enumerate(subs):
                try:
                    if lines_list[i]:
                        line.plaintext = lines_list[i]
                    else:
                        # we assume that there was nothing to translate if Google returns None. ex.: "♪♪"
                        continue
                except IndexError:
                    logging.error(f'BAZARR is unable to translate malformed subtitles: {self.source_srt_file}')
                    show_message(f'Translation failed: Unable to translate malformed subtitles for {self.source_srt_file}')
                    return False

            try:
                subs.save(self.dest_srt_file)
                add_translator_info(self.dest_srt_file, f"# Subtitles translated with Google Translate # ")
            except OSError:
                logging.error(f'BAZARR is unable to save translated subtitles to {self.dest_srt_file}')
                show_message(f'Translation failed: Unable to save translated subtitles to {self.dest_srt_file}')
                raise OSError

            message = f"{language_from_alpha2(self.from_lang)} subtitles translated to {language_from_alpha3(self.to_lang)}."
            result = create_process_result(message, self.video_path, self.orig_to_lang, self.forced, self.hi, self.dest_srt_file, self.media_type)

            if self.media_type == 'series':
                history_log(action=6, sonarr_series_id=self.sonarr_series_id, sonarr_episode_id=self.sonarr_episode_id, result=result)
            else:
                history_log_movie(action=6, radarr_id=self.radarr_id, result=result)

            return self.dest_srt_file

        except Exception as e:
            logging.error(f'BAZARR encountered an error during translation: {str(e)}')
            show_message(f'Google translation failed: {str(e)}')
            hide_progress(id=f'translate_progress_{self.dest_srt_file}')
            return False

    @retry(exceptions=(TooManyRequests, RequestError), tries=6, delay=1, backoff=2, jitter=(0, 1))
    def _translate_text(self, text):
        try:
            return GoogleTranslator(
                source='auto',
                target=self.language_code_convert_dict.get(self.lang_obj.alpha2, self.lang_obj.alpha2)
            ).translate(text=text)
        except (TooManyRequests, RequestError) as e:
            logging.error(f'Google Translate API error after retries: {str(e)}')
            show_message(f'Google Translate API error: {str(e)}')
            raise
        except Exception as e:
            logging.error(f'Unexpected error in Google translation: {str(e)}')
            show_message(f'Translation error: {str(e)}')
            raise
