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
from subliminal_patch.score import compute_score

from get_languages import alpha3_from_alpha2
from config import settings, get_array_from
from helper import get_target_folder, force_unicode
from database import get_profiles_list
from score import movie_score, series_score
from .pool import update_pools, _get_pool, _init_pool
from .utils import get_video, _get_lang_obj, _get_scores
from .processing import process_subtitle


@update_pools
def manual_search(path, profile_id, providers, sceneName, title, media_type):
    logging.debug('BAZARR Manually searching subtitles for this file: ' + path)

    final_subtitles = []

    pool = _get_pool(media_type, profile_id)

    language_set, initial_language_set = _get_language_obj(profile_id=profile_id)
    also_forced = any([x.forced for x in initial_language_set])
    _set_forced_providers(also_forced=also_forced, pool=pool)

    if providers:
        video = get_video(force_unicode(path), title, sceneName, providers=providers, media_type=media_type)
    else:
        logging.info("BAZARR All providers are throttled")
        return None
    if video:
        handler = series_score if media_type == "series" else movie_score

        try:
            if providers:
                subtitles = list_all_subtitles([video], language_set, pool)

                if 'subscene' in providers:
                    s_pool = _init_pool("movie", profile_id, {"subscene"})

                    subscene_language_set = set()
                    for language in language_set:
                        if language.forced:
                            subscene_language_set.add(language)
                    if len(subscene_language_set):
                        s_pool.provider_configs['subscene'] = {}
                        s_pool.provider_configs['subscene']['only_foreign'] = True
                        subtitles_subscene = list_all_subtitles([video], subscene_language_set, s_pool)
                        s_pool.provider_configs['subscene']['only_foreign'] = False
                        subtitles[video] += subtitles_subscene[video]
            else:
                subtitles = []
                logging.info("BAZARR All providers are throttled")
                return None
        except Exception:
            logging.exception("BAZARR Error trying to get Subtitle list from provider for this file: " + path)
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
                        logging.debug(f"BAZARR Skipping {s}, because it doesn't match our series/episode")
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
                score, score_without_hash = compute_score(matches, s, video, hearing_impaired=initial_hi,
                                                          score_obj=handler)
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
                         matches=list(matches),
                         dont_matches=list(not_matched),
                         release_info=releases,
                         uploader=s_uploader))

            final_subtitles = sorted(subtitles_list, key=lambda x: (x['orig_score'], x['score_without_hash']),
                                     reverse=True)
            logging.debug('BAZARR ' + str(len(final_subtitles)) + " Subtitles have been found for this file: " + path)
            logging.debug('BAZARR Ended searching Subtitles for this file: ' + path)

    subliminal.region.backend.sync()

    return final_subtitles


@update_pools
def manual_download_subtitle(path, audio_language, hi, forced, subtitle, provider, sceneName, title, media_type,
                             profile_id):
    logging.debug('BAZARR Manually downloading Subtitles for this file: ' + path)

    if settings.general.getboolean('utf8_encode'):
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
    subtitle.mods = get_array_from(settings.general.subzero_mods)
    video = get_video(force_unicode(path), title, sceneName, providers={provider}, media_type=media_type)
    if video:
        try:
            if provider:
                download_subtitles([subtitle], _get_pool(media_type, profile_id))
                logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
            else:
                logging.info("BAZARR All providers are throttled")
                return None
        except Exception:
            logging.exception('BAZARR Error downloading Subtitles for this file ' + path)
            return None
        else:
            if not subtitle.is_valid():
                logging.exception('BAZARR No valid Subtitles file found for this file: ' + path)
                return
            try:
                chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                    'win') and settings.general.getboolean('chmod_enabled') else None
                saved_subtitles = save_subtitles(video.original_path, [subtitle],
                                                 single=settings.general.getboolean('single_language'),
                                                 tags=None,  # fixme
                                                 directory=get_target_folder(path),
                                                 chmod=chmod,
                                                 # formats=("srt", "vtt")
                                                 path_decoder=force_unicode)
            except Exception:
                logging.exception('BAZARR Error saving Subtitles file to disk for this file:' + path)
                return
            else:
                if saved_subtitles:
                    _, max_score, _ = _get_scores(media_type)
                    for saved_subtitle in saved_subtitles:
                        return process_subtitle(subtitle=saved_subtitle, media_type=media_type,
                                                audio_language=audio_language, is_upgrade=False,
                                                is_manual=True, path=path, max_score=max_score)
                else:
                    logging.error(
                        "BAZARR Tried to manually download a Subtitles for file: " + path
                        + " but we weren't able to do (probably throttled by " + str(subtitle.provider_name)
                        + ". Please retry later or select a Subtitles from another provider.")
                    return None

    subliminal.region.backend.sync()

    logging.debug('BAZARR Ended manually downloading Subtitles for file: ' + path)


def _get_language_obj(profile_id):
    initial_language_set = set()
    language_set = set()

    # where [3] is items list of dict(id, lang, forced, hi)
    language_items = get_profiles_list(profile_id=int(profile_id))['items']

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

    return language_set, initial_language_set


def _set_forced_providers(also_forced, pool):
    if also_forced:
        pool.provider_configs['podnapisi']['also_foreign'] = True
        pool.provider_configs['opensubtitles']['also_foreign'] = True
