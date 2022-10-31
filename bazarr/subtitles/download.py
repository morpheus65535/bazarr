# coding=utf-8
# fmt: off

import os
import sys
import logging
import subliminal

from subzero.language import Language
from subliminal_patch.core import save_subtitles
from subliminal_patch.core_persistent import download_best_subtitles
from subliminal_patch.score import compute_score

from app.config import settings, get_array_from
from utilities.helper import get_target_folder, force_unicode
from languages.get_languages import alpha3_from_alpha2
from subtitles.tools.score import movie_score, series_score

from .pool import update_pools, _get_pool
from .utils import get_video, _get_lang_obj, _get_scores, _set_forced_providers
from .processing import process_subtitle


@update_pools
def generate_subtitles(path, languages, audio_language, sceneName, title, media_type,
                       forced_minimum_score=None, is_upgrade=False, profile_id=None):
    if not languages:
        return None

    logging.debug('BAZARR Searching subtitles for this file: ' + path)

    if settings.general.getboolean('utf8_encode'):
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"

    pool = _get_pool(media_type, profile_id)
    providers = pool.providers

    language_set = _get_language_obj(languages=languages)
    hi_required = any([x.hi for x in language_set])
    also_forced = any([x.forced for x in language_set])
    forced_required = all([x.forced for x in language_set])
    _set_forced_providers(pool=pool, also_forced=also_forced, forced_required=forced_required)

    video = get_video(force_unicode(path), title, sceneName, providers=providers, media_type=media_type)

    if video:
        handler = series_score if media_type == "series" else movie_score
        minimum_score = settings.general.minimum_score
        minimum_score_movie = settings.general.minimum_score_movie
        min_score, max_score, scores = _get_scores(media_type, minimum_score_movie, minimum_score)

        if providers:
            if forced_minimum_score:
                min_score = int(forced_minimum_score) + 1
            downloaded_subtitles = download_best_subtitles(videos={video},
                                                           languages=language_set,
                                                           pool_instance=pool,
                                                           min_score=int(min_score),
                                                           hearing_impaired=hi_required,
                                                           compute_score=compute_score,
                                                           throttle_time=None,  # fixme
                                                           score_obj=handler)
        else:
            downloaded_subtitles = None
            logging.info("BAZARR All providers are throttled")
            return None

        subz_mods = get_array_from(settings.general.subzero_mods)
        saved_any = False
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
                        'win') and settings.general.getboolean('chmod_enabled') else None
                    saved_subtitles = save_subtitles(video.original_path, subtitles,
                                                     single=settings.general.getboolean('single_language'),
                                                     tags=None,  # fixme
                                                     directory=fld,
                                                     chmod=chmod,
                                                     formats=tuple(subtitle_formats),
                                                     path_decoder=force_unicode
                                                     )
                except Exception as e:
                    logging.exception(
                        'BAZARR Error saving Subtitles file to disk for this file:' + path + ': ' + repr(e))
                    pass
                else:
                    saved_any = True
                    for subtitle in saved_subtitles:
                        processed_subtitle = process_subtitle(subtitle=subtitle, media_type=media_type,
                                                              audio_language=audio_language, is_upgrade=is_upgrade,
                                                              is_manual=False, path=path, max_score=max_score)
                        if not processed_subtitle:
                            logging.debug(f"BAZARR unable to process this subtitles: {subtitle}")
                            continue
                        yield processed_subtitle

        if not saved_any:
            logging.debug('BAZARR No Subtitles were found for this file: ' + path)
            return None

    subliminal.region.backend.sync()

    logging.debug('BAZARR Ended searching Subtitles for file: ' + path)


def _get_language_obj(languages):
    language_set = set()

    if not isinstance(languages, (set, list)):
        languages = [languages]

    for language in languages:
        lang, hi_item, forced_item = language
        if hi_item == "True":
            hi = "force HI"
        else:
            hi = "force non-HI"

        # Always use alpha2 in API Request
        lang = alpha3_from_alpha2(lang)

        lang_obj = _get_lang_obj(lang)

        if forced_item == "True":
            lang_obj = Language.rebuild(lang_obj, forced=True)
        if hi == "force HI":
            lang_obj = Language.rebuild(lang_obj, hi=True)

        language_set.add(lang_obj)

    return language_set
