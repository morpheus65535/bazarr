# coding=utf-8
# fmt: off

import os
import sys
import logging
import pickle
import codecs
import subliminal

from subzero.language import Language
from subliminal_patch.core import save_subtitles
from subliminal_patch.core_persistent import list_all_subtitles, download_subtitles
from subliminal_patch.score import ComputeScore

from languages.get_languages import alpha3_from_alpha2
from app.config import get_scores, settings, get_array_from
from utilities.helper import get_target_folder, force_unicode
from app.database import get_profiles_list

from .pool import update_pools, _get_pool
from .utils import get_video, _get_lang_obj, _get_scores, _set_forced_providers
from .processing import process_subtitle


@update_pools
def manual_search(path, profile_id, providers, sceneName, title, media_type):
    logging.debug(f'BAZARR Manually searching subtitles for this file: {path}')

    final_subtitles = []

    pool = _get_pool(media_type, profile_id)

    language_set, initial_language_set, original_format = _get_language_obj(profile_id=profile_id)
    also_forced = any([x.forced for x in initial_language_set])
    forced_required = all([x.forced for x in initial_language_set])
    compute_score = ComputeScore(get_scores())
    _set_forced_providers(pool=pool, also_forced=also_forced, forced_required=forced_required)

    if providers:
        video = get_video(force_unicode(path), title, sceneName, providers=providers, media_type=media_type)
    else:
        logging.info("BAZARR All providers are throttled")
        return 'All providers are throttled'
    if video:
        try:
            if providers:
                subtitles = list_all_subtitles([video], language_set, pool)
            else:
                logging.info("BAZARR All providers are throttled")
                return 'All providers are throttled'
        except Exception:
            logging.exception(f"BAZARR Error trying to get Subtitle list from provider for this file: {path}")
        else:
            subtitles_list = []
            minimum_score = settings.general.minimum_score
            minimum_score_movie = settings.general.minimum_score_movie

            for s in subtitles[video]:
                try:
                    matches = s.get_matches(video)
                except AttributeError:
                    continue

                # skip wrong season/episodes
                if media_type == "series":
                    can_verify_series = True
                    if not s.hash_verifiable and "hash" in matches:
                        can_verify_series = False

                    if can_verify_series and not {"series", "season", "episode"}.issubset(matches):
                        try:
                            logging.debug(f"BAZARR Skipping {s}, because it doesn't match our series/episode")
                        except TypeError:
                            logging.debug("BAZARR Ignoring invalid subtitles")
                        continue

                initial_hi = None
                initial_hi_match = False
                for language in initial_language_set:
                    if s.language.basename == language.basename and \
                            s.language.forced == language.forced and \
                            s.language.hi == language.hi:
                        initial_hi = language.hi
                        initial_hi_match = True
                        break
                if not initial_hi_match:
                    initial_hi = None

                _, max_score, scores = _get_scores(media_type, minimum_score_movie, minimum_score)
                score, score_without_hash = compute_score(matches, s, video, hearing_impaired=initial_hi)
                if 'hash' not in matches:
                    not_matched = scores - matches
                    s.score = score_without_hash
                else:
                    s.score = score
                    not_matched = set()

                if s.hearing_impaired == initial_hi:
                    matches.add('hearing_impaired')
                else:
                    not_matched.add('hearing_impaired')

                releases = []
                if hasattr(s, 'release_info'):
                    if s.release_info is not None:
                        for s_item in s.release_info.split(','):
                            if s_item.strip():
                                releases.append(s_item)

                if s.uploader and s.uploader.strip():
                    s_uploader = s.uploader.strip()
                else:
                    s_uploader = None

                subtitles_list.append(
                    dict(score=round((score / max_score * 100), 2),
                         orig_score=score,
                         score_without_hash=score_without_hash,
                         forced=str(s.language.forced),
                         language=str(s.language.basename),
                         hearing_impaired=str(s.hearing_impaired),
                         provider=s.provider_name,
                         subtitle=codecs.encode(pickle.dumps(s.make_picklable()), "base64").decode(),
                         url=s.page_link,
                         original_format=original_format,
                         matches=list(matches),
                         dont_matches=list(not_matched),
                         release_info=releases,
                         uploader=s_uploader))

            final_subtitles = sorted(subtitles_list, key=lambda x: (x['orig_score'], x['score_without_hash']),
                                     reverse=True)
            logging.debug(f'BAZARR {len(final_subtitles)} Subtitles have been found for this file: {path}')
            logging.debug(f'BAZARR Ended searching Subtitles for this file: {path}')

    subliminal.region.backend.sync()

    return final_subtitles


@update_pools
def manual_download_subtitle(path, audio_language, hi, forced, subtitle, provider, sceneName, title, media_type,
                             use_original_format, profile_id):
    logging.debug(f'BAZARR Manually downloading Subtitles for this file: {path}')

    if settings.general.utf8_encode:
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"

    subtitle = pickle.loads(codecs.decode(subtitle.encode(), "base64"))
    if hi == 'True':
        subtitle.language.hi = True
    else:
        subtitle.language.hi = False
    if forced == 'True':
        subtitle.language.forced = True
    else:
        subtitle.language.forced = False
    if use_original_format in (1, "1", "True", True):
        subtitle.use_original_format = True

    subtitle.mods = get_array_from(settings.general.subzero_mods)
    video = get_video(force_unicode(path), title, sceneName, providers={provider}, media_type=media_type)
    if video:
        try:
            if provider:
                download_subtitles([subtitle], _get_pool(media_type, profile_id))
                logging.debug(f'BAZARR Subtitles file downloaded for this file: {path}')
            else:
                logging.info("BAZARR All providers are throttled")
                return 'All providers are throttled'
        except Exception:
            logging.exception(f'BAZARR Error downloading Subtitles for this file {path}')
            return 'Error downloading Subtitles'
        else:
            if not subtitle.is_valid():
                logging.error(f"BAZARR Downloaded subtitles isn't valid for this file: {path}")
                return "Downloaded subtitles isn't valid. Check log."
            try:
                chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                    'win') and settings.general.chmod_enabled else None
                saved_subtitles = save_subtitles(video.original_path, [subtitle],
                                                 single=settings.general.single_language,
                                                 tags=None,  # fixme
                                                 directory=get_target_folder(path),
                                                 chmod=chmod,
                                                 formats=(subtitle.format,),
                                                 path_decoder=force_unicode)
            except Exception:
                logging.exception(f'BAZARR Error saving Subtitles file to disk for this file: {path}')
                return 'Error saving Subtitles file to disk'
            else:
                if saved_subtitles:
                    _, max_score, _ = _get_scores(media_type)
                    for saved_subtitle in saved_subtitles:
                        processed_subtitle = process_subtitle(subtitle=saved_subtitle, media_type=media_type,
                                                              audio_language=audio_language, is_upgrade=False,
                                                              is_manual=True, path=path, max_score=max_score)
                        if processed_subtitle:
                            return processed_subtitle
                        else:
                            logging.debug(f"BAZARR unable to process this subtitles: {subtitle}")
                            continue
                else:
                    logging.error(
                        f"BAZARR Tried to manually download a Subtitles for file: {path} but we weren't able to do "
                        f"(probably throttled by {subtitle.provider_name}. Please retry later or select a Subtitles "
                        f"from another provider.")
                    return 'Something went wrong, check the logs for error'

    subliminal.region.backend.sync()

    logging.debug(f'BAZARR Ended manually downloading Subtitles for file: {path}')


def _get_language_obj(profile_id):
    initial_language_set = set()
    language_set = set()

    profile = get_profiles_list(profile_id=int(profile_id))
    language_items = profile['items']
    original_format = profile['originalFormat']

    for language in language_items:
        forced = language['forced']
        hi = language['hi']
        language = language['language']

        lang = alpha3_from_alpha2(language)

        lang_obj = _get_lang_obj(lang)

        if forced == "True":
            lang_obj = Language.rebuild(lang_obj, forced=True)

        if hi == "True":
            lang_obj = Language.rebuild(lang_obj, hi=True)

        initial_language_set.add(lang_obj)

    language_set = initial_language_set.copy()
    for language in language_set.copy():
        lang_obj_for_hi = language
        if not language.forced and not language.hi:
            lang_obj_hi = Language.rebuild(lang_obj_for_hi, hi=True)
        elif not language.forced and language.hi:
            lang_obj_hi = Language.rebuild(lang_obj_for_hi, hi=False)
        else:
            continue
        language_set.add(lang_obj_hi)

    return language_set, initial_language_set, original_format
