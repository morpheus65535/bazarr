# coding=utf-8

import logging
import datetime
import os
import pysubs2
import srt

from subliminal_patch.core import get_subtitle_path
from subzero.language import Language
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound
from time import sleep
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.database import TableShows, TableEpisodes, TableMovies, database, select
from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from subtitles.tools.translator_gemini import TranslatorGemini
from app.event_handler import show_progress, hide_progress, show_message
from utilities.path_mappings import path_mappings


def translate_subtitles_file(video_path, source_srt_file, from_lang, to_lang, forced, hi, media_type, sonarr_series_id,
                             sonarr_episode_id, radarr_id):

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

    if settings.translator.translator_type == 'gemini':
        translate_subtitles_file_gemini(dest_srt_file, source_srt_file, to_lang, media_type, sonarr_series_id,
                                        radarr_id)
    else:
        translate_subtitles_file_google(
            source_srt_file, dest_srt_file, lang_obj, to_lang, from_lang,
            media_type, video_path, orig_to_lang, forced, hi,
            sonarr_series_id, sonarr_episode_id, radarr_id
        )

    logging.debug(f'BAZARR is saving translated subtitles to {dest_srt_file}')

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


def translate_subtitles_file_google(source_srt_file, dest_srt_file, lang_obj, to_lang, from_lang, media_type,
                                    video_path, orig_to_lang, forced, hi, sonarr_series_id, sonarr_episode_id,
                                    radarr_id):
    language_code_convert_dict = {
        'he': 'iw',
        'zh': 'zh-CN',
        'zt': 'zh-TW',
    }

    subs = pysubs2.load(source_srt_file, encoding='utf-8')
    subs.remove_miscellaneous_events()
    lines_list = [x.plaintext for x in subs]
    lines_list_len = len(lines_list)

    translated_lines = []

    def translate_line(id, line, attempt):
        try:
            translated_text = GoogleTranslator(
                source='auto',
                target=language_code_convert_dict.get(lang_obj.alpha2, lang_obj.alpha2)
            ).translate(text=line)
        except TooManyRequests:
            if attempt <= 5:
                sleep(1)
                translate_line(id, line, attempt + 1)
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
        add_translator_info(dest_srt_file, f"# Subtitles translated with Google Translate # ")
    except OSError:
        logging.error(f'BAZARR is unable to save translated subtitles to {dest_srt_file}')
        raise OSError

    message = f"{language_from_alpha2(from_lang)} subtitles translated to {language_from_alpha3(to_lang)}."

    if media_type == 'series':
        prr = path_mappings.path_replace_reverse
    else:
        prr = path_mappings.path_replace_reverse_movie

    result = ProcessSubtitlesResult(
        message=message,
        reversed_path=prr(video_path),
        downloaded_language_code2=orig_to_lang,
        downloaded_provider=None,
        score=None,
        forced=forced,
        subtitle_id=None,
        reversed_subtitles_path=prr(dest_srt_file),
        hearing_impaired=hi
    )

    if media_type == 'series':
        history_log(action=6, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id, result=result)
    else:
        history_log_movie(action=6, radarr_id=radarr_id, result=result)

    return dest_srt_file


def translate_subtitles_file_gemini(dest_srt_file, source_srt_file, to_lang, media_type, sonarr_series_id, radarr_id):
    subs = pysubs2.load(source_srt_file, encoding='utf-8')
    subs.remove_miscellaneous_events()

    try:
        logging.debug(f'BAZARR is sending subtitle file to Gemini for translation')

        logging.info(f"BAZARR is sending subtitle file to Gemini for translation " + source_srt_file)

        params = {
            "gemini_api_key": settings.translator.gemini_key,
            "target_language": language_from_alpha3(to_lang),
            "input_file": source_srt_file,
            "output_file": dest_srt_file,
            "model_name": settings.translator.gemini_model,
            "description": get_description(media_type, radarr_id, sonarr_series_id),
        }

        try:
            filtered_params = {k: v for k, v in params.items() if v is not None}
            translator = TranslatorGemini(**filtered_params)
            translator.translate()
            add_translator_info(dest_srt_file, f"# Subtitles translated with {settings.translator.gemini_model} # ")
        except Exception as e:
            os.remove(dest_srt_file)
            logging.error(f'translate encountered an error translating with Gemini: {str(e)}')
            show_message(f'Gemini translation error: {str(e)}')

    except Exception as e:
        logging.error(f'BAZARR encountered an error translating with Gemini: {str(e)}')
        return False


def get_description(media_type, radarr_id, sonarr_series_id):
    try:
        if media_type == 'movies':
            movie = database.execute(
                select(TableMovies.title, TableMovies.imdbId, TableMovies.year, TableMovies.overview)
                .where(TableMovies.radarrId == radarr_id)
            ).first()

            if movie:
                return (f"You will translate movie that is called {movie.title} from {movie.year} "
                        f"and it has IMDB ID = {movie.imdbId}. Its overview: {movie.overview}")
            else:
                logging.info(f"No movie found for this radarr_id: {radarr_id}")
                return ""

        else:
            series = database.execute(
                select(TableShows.title, TableShows.imdbId, TableShows.year, TableShows.overview)
                .where(TableShows.sonarrSeriesId == sonarr_series_id)
            ).first()

            if series:
                return (f"You will translate TV show that is called {series.title} from {series.year} "
                        f"and it has IMDB ID = {series.imdbId}. Its overview: {series.overview}")
            else:
                logging.info(f"No series found for this sonarr_series_id: {sonarr_series_id}")
                return ""
    except Exception:
        logging.info("Problem with getting media info")
        return ""


def add_translator_info(dest_srt_file, info):
    if settings.translator.translator_info:
        # Load the SRT content
        with open(dest_srt_file, "r", encoding="utf-8") as f:
            srt_content = f.read()

        # Parse subtitles
        subtitles = list(srt.parse(srt_content))

        if subtitles:
            first_start = subtitles[0].start
        else:
            # If no subtitles exist, set an arbitrary end time for the info subtitle
            first_start = datetime.timedelta(seconds=5)

        # Determine the end time as the minimum of first_start and 5s
        end_time = min(first_start, datetime.timedelta(seconds=5))

        # If end time is exactly 5s, start at 1s. Otherwise, start at 0s.
        if end_time == datetime.timedelta(seconds=5):
            start_time = datetime.timedelta(seconds=1)
        else:
            start_time = datetime.timedelta(seconds=0)

        # Add the info subtitle
        new_sub = srt.Subtitle(
            index=1,  # temporary, will be reindexed
            start=start_time,
            end=end_time,
            content=info
        )
        subtitles.insert(0, new_sub)

        # Re-index and sort
        subtitles = list(srt.sort_and_reindex(subtitles))

        with open(dest_srt_file, "w", encoding="utf-8") as f:
            f.write(srt.compose(subtitles))
