# coding=utf-8
# fmt: off

import os
import sys
import logging
import subliminal
import ast

from subzero.language import Language
from subliminal_patch.core import save_subtitles
from subliminal_patch.core_persistent import download_best_subtitles
from subliminal_patch.score import ComputeScore

from app.config import settings, get_scores, get_array_from
from app.database import TableEpisodes, TableMovies, database, select, get_profiles_list
from utilities.path_mappings import path_mappings
from utilities.helper import get_target_folder, force_unicode
from languages.get_languages import alpha3_from_alpha2

from .pool import update_pools, _get_pool
from .utils import get_video, _get_lang_obj, _get_scores, _set_forced_providers
from .processing import process_subtitle


@update_pools
def generate_subtitles(path, languages, audio_language, sceneName, title, media_type, profile_id,
                       forced_minimum_score=None, is_upgrade=False, check_if_still_required=False,
                       previous_subtitles_to_delete=None, job_id=None):
    if not languages:
        return None

    logging.debug(f'BAZARR Searching subtitles for this file: {path}')

    if settings.general.utf8_encode:
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"

    pool = _get_pool(media_type, profile_id)
    providers = pool.providers

    language_set = _get_language_obj(languages=languages)
    profile = get_profiles_list(profile_id=profile_id)
    original_format = profile['originalFormat']
    hi_required = "force HI" if all([x.hi for x in language_set]) else "don't prefer"
    also_forced = any([x.forced for x in language_set])
    forced_required = all([x.forced for x in language_set])
    _set_forced_providers(pool=pool, also_forced=also_forced, forced_required=forced_required)

    try:
        video = get_video(force_unicode(path), title, sceneName, providers=providers, media_type=media_type)
    except ValueError as e:
        logging.exception(f'BAZARR Unable to get video object for {path}: {e}')
        return None

    if video:
        minimum_score = settings.general.minimum_score
        minimum_score_movie = settings.general.minimum_score_movie
        min_score, max_score, scores = _get_scores(media_type, minimum_score_movie, minimum_score)

        subz_mods = get_array_from(settings.general.subzero_mods)
        saved_any = False

        if providers:
            if forced_minimum_score:
                min_score = int(forced_minimum_score) + 1
            for language in language_set:
                # confirm if language is still missing or if cutoff has been reached
                if check_if_still_required and language not in check_missing_languages(path, media_type):
                    # cutoff has been reached
                    logging.debug(f"BAZARR this language ({parse_language_object(language)}) is ignored because cutoff "
                                  f"has been reached during this search.")
                    continue
                else:
                    try:
                        downloaded_subtitles = download_best_subtitles(videos={video},
                                                                       languages={language},
                                                                       pool_instance=pool,
                                                                       min_score=int(min_score),
                                                                       hearing_impaired=hi_required,
                                                                       compute_score=ComputeScore(get_scores()),
                                                                       use_original_format=original_format in (1, "1", "True", True))
                    except Exception as e:
                        logging.exception(f'BAZARR Error downloading Subtitles for this file {path}: {repr(e)}')
                        return None

                if downloaded_subtitles:
                    for video, subtitles in downloaded_subtitles.items():
                        if not subtitles:
                            continue

                        subtitle_formats = set()
                        for s in subtitles:
                            s.mods = subz_mods
                            subtitle_formats.add(s.format)

                        try:
                            fld = get_target_folder(path)
                            chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                                'win') and settings.general.chmod_enabled else None
                            if is_upgrade and previous_subtitles_to_delete:
                                try:
                                    # delete previously downloaded subtitles in case of an upgrade to prevent edge loop
                                    # issue.
                                    os.remove(previous_subtitles_to_delete)
                                except (OSError, FileNotFoundError):
                                    pass
                            saved_subtitles = save_subtitles(video.original_path, subtitles,
                                                             single=settings.general.single_language,
                                                             tags=None,  # fixme
                                                             directory=fld,
                                                             chmod=chmod,
                                                             formats=subtitle_formats,
                                                             path_decoder=force_unicode
                                                             )
                        except Exception as e:
                            logging.exception(
                                f'BAZARR Error saving Subtitles file to disk for this file {path}: {repr(e)}')
                            pass
                        else:
                            saved_any = True
                            for subtitle in saved_subtitles:
                                processed_subtitle = process_subtitle(subtitle=subtitle, media_type=media_type,
                                                                      audio_language=audio_language,
                                                                      is_upgrade=is_upgrade, is_manual=False,
                                                                      path=path, max_score=max_score, job_id=job_id)
                                if not processed_subtitle:
                                    logging.debug(f"BAZARR unable to process this subtitles: {subtitle}")
                                    continue
                                yield processed_subtitle
        else:
            logging.info("BAZARR All providers are throttled")
            return None

        if not saved_any:
            logging.debug(f'BAZARR No Subtitles were found for this file: {path}')
            return None

    subliminal.region.backend.sync()

    logging.debug(f'BAZARR Ended searching Subtitles for file: {path}')


def _get_language_obj(languages):
    language_set = set()

    if not isinstance(languages, (set, list)):
        languages = [languages]

    for language in languages:
        lang, hi_item, forced_item = language

        # Always use alpha2 in API Request
        lang = alpha3_from_alpha2(lang)

        lang_obj = _get_lang_obj(lang)

        if forced_item == "True":
            lang_obj = Language.rebuild(lang_obj, forced=True)
        if hi_item == "True":
            lang_obj = Language.rebuild(lang_obj, hi=True)

        language_set.add(lang_obj)

    return language_set


def parse_language_object(language):
    if isinstance(language, Language):
        hi = ":hi" if language.hi else ""
        forced = ":forced" if language.forced else ""
        return language.basename + hi + forced
    else:
        return language


def check_missing_languages(path, media_type):
    # confirm if language is still missing or if cutoff has been reached
    if media_type == 'series':
        confirmed_missing_subs = database.execute(
            select(TableEpisodes.missing_subtitles)
            .where(TableEpisodes.path == path_mappings.path_replace_reverse(path)))\
            .first()
    else:
        confirmed_missing_subs = database.execute(
            select(TableMovies.missing_subtitles)
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path)))\
            .first()

    if not confirmed_missing_subs:
        reversed_path = path_mappings.path_replace_reverse(path) if media_type == 'series' else \
            path_mappings.path_replace_reverse_movie(path)
        logging.debug(f"BAZARR no media with this path have been found in database: {reversed_path}")
        return []

    languages = []
    for language in ast.literal_eval(confirmed_missing_subs.missing_subtitles):
        if language is not None:
            hi_ = "True" if language.endswith(':hi') else "False"
            forced_ = "True" if language.endswith(':forced') else "False"
            languages.append((language.split(":")[0], hi_, forced_))

    return _get_language_obj(languages=languages)
