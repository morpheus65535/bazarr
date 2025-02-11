# coding=utf-8

import logging
import pysubs2

from subliminal_patch.core import get_subtitle_path
from subzero.language import Language
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound
from time import sleep
from concurrent.futures import ThreadPoolExecutor

from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from app.event_handler import show_progress, hide_progress
from utilities.path_mappings import path_mappings


def translate_subtitles_file(video_path, source_srt_file, from_lang, to_lang, forced, hi, media_type, sonarr_series_id,
                             sonarr_episode_id, radarr_id):
    language_code_convert_dict = {
        'he': 'iw',
        'zh': 'zh-CN',
        'zt': 'zh-TW',
    }

    orig_to_lang = to_lang
    to_lang = alpha3_from_alpha2(to_lang)
    try:
        lang_obj = Language(to_lang)
    except ValueError:
        custom_lang_obj = CustomLanguage.from_value(to_lang, "alpha3")
        if custom_lang_obj:
            lang_obj = CustomLanguage.subzero_language(custom_lang_obj)
        else:
            logging.debug(f'BAZARR is unable to translate to {to_lang} for this subtitles: {source_srt_file}')
            return False
    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)
    if hi:
        lang_obj = Language.rebuild(lang_obj, hi=True)

    logging.debug(f'BAZARR is translating in {lang_obj} this subtitles {source_srt_file}')

    dest_srt_file = get_subtitle_path(video_path,
                                      language=lang_obj if isinstance(lang_obj, Language) else lang_obj.subzero_language(),
                                      extension='.srt',
                                      forced_tag=forced,
                                      hi_tag=hi)

    subs = pysubs2.load(source_srt_file, encoding='utf-8')
    subs.remove_miscellaneous_events()
    lines_list = [x.plaintext for x in subs]
    lines_list_len = len(lines_list)

    def translate_line(id, line, attempt):
        try:
            translated_text = GoogleTranslator(
                source='auto',
                target=language_code_convert_dict.get(lang_obj.alpha2, lang_obj.alpha2)
            ).translate(text=line)
        except TooManyRequests:
            if attempt <= 5:
                sleep(1)
                super(translate_line(id, line, attempt+1))
            else:
                logging.debug(f'Too many requests while translating {line}')
                translated_lines.append({'id': id, 'line': line})
        except (RequestError, TranslationNotFound):
            logging.debug(f'Unable to translate line {line}')
            translated_lines.append({'id': id, 'line': line})
        else:
            translated_lines.append({'id': id, 'line': translated_text})
        finally:
            show_progress(id=f'translate_progress_{dest_srt_file}',
                          header=f'Translating subtitles lines to {language_from_alpha3(to_lang)}...',
                          name='',
                          value=len(translated_lines),
                          count=lines_list_len)

    logging.debug(f'BAZARR is sending {lines_list_len} blocks to Google Translate')

    pool = ThreadPoolExecutor(max_workers=10)

    translated_lines = []

    for i, line in enumerate(lines_list):
        pool.submit(translate_line, i, line, 1)

    pool.shutdown(wait=True)

    for i, line in enumerate(translated_lines):
        lines_list[line['id']] = line['line']

    show_progress(id=f'translate_progress_{dest_srt_file}',
                  header=f'Translating subtitles lines to {language_from_alpha3(to_lang)}...',
                  name='',
                  value=lines_list_len,
                  count=lines_list_len)

    logging.debug(f'BAZARR saving translated subtitles to {dest_srt_file}')
    for i, line in enumerate(subs):
        try:
            if lines_list[i]:
                line.plaintext = lines_list[i]
            else:
                # we assume that there was nothing to translate if Google returns None. ex.: "♪♪"
                continue
        except IndexError:
            logging.error(f'BAZARR is unable to translate malformed subtitles: {source_srt_file}')
            return False
    try:
        subs.save(dest_srt_file)
    except OSError:
        logging.error(f'BAZARR is unable to save translated subtitles to {dest_srt_file}')
        raise OSError

    message = f"{language_from_alpha2(from_lang)} subtitles translated to {language_from_alpha3(to_lang)}."

    if media_type == 'series':
        prr = path_mappings.path_replace_reverse
    else:
        prr = path_mappings.path_replace_reverse_movie

    result = ProcessSubtitlesResult(message=message,
                                    reversed_path=prr(video_path),
                                    downloaded_language_code2=orig_to_lang,
                                    downloaded_provider=None,
                                    score=None,
                                    forced=forced,
                                    subtitle_id=None,
                                    reversed_subtitles_path=prr(dest_srt_file),
                                    hearing_impaired=hi)

    if media_type == 'series':
        history_log(action=6, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id, result=result)
    else:
        history_log_movie(action=6, radarr_id=radarr_id, result=result)

    return dest_srt_file
