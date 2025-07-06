# coding=utf-8

import logging
import os
import srt
import datetime

from app.config import settings
from subzero.language import Language
from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from subtitles.processing import ProcessSubtitlesResult
from utilities.path_mappings import path_mappings

from app.database import TableShows, TableEpisodes, TableMovies, database, select


def validate_translation_params(video_path, source_srt_file, from_lang, to_lang):
    """Validate translation parameters."""
    if not os.path.exists(source_srt_file):
        raise FileNotFoundError(f"Source subtitle file not found: {source_srt_file}")

    if not from_lang or not to_lang:
        raise ValueError("Source and target languages must be specified")

    return True

def convert_language_codes(to_lang, forced=False, hi=False):
    """Convert and validate language codes."""
    orig_to_lang = to_lang
    to_lang = alpha3_from_alpha2(to_lang)

    try:
        lang_obj = Language(to_lang)
    except ValueError:
        custom_lang_obj = CustomLanguage.from_value(to_lang, "alpha3")
        if custom_lang_obj:
            lang_obj = CustomLanguage.subzero_language(custom_lang_obj)
        else:
            raise ValueError(f'Unable to translate to {to_lang}')

    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)
    if hi:
        lang_obj = Language.rebuild(lang_obj, hi=True)

    return lang_obj, orig_to_lang

def create_process_result(message, video_path, orig_to_lang, forced, hi, dest_srt_file, media_type):
    """Create a ProcessSubtitlesResult object with common parameters."""
    if media_type == 'series':
        prr = path_mappings.path_replace_reverse
    else:
        prr = path_mappings.path_replace_reverse_movie

    return ProcessSubtitlesResult(
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