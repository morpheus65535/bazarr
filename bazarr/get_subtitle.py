# coding=utf-8

import os
import sys
import ast
import logging
import subprocess
import time
import pickle
import codecs
import re
import subliminal
import copy
from datetime import datetime, timedelta
from subzero.language import Language
from subzero.video import parse_video
from subliminal import region, score as subliminal_scores, \
    list_subtitles, Episode, Movie
from subliminal_patch.core import SZAsyncProviderPool, download_best_subtitles, save_subtitles, download_subtitles, \
    list_all_subtitles, get_subtitle_path
from subliminal_patch.score import compute_score
from subliminal_patch.subtitle import Subtitle
from get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2, language_from_alpha2, \
    alpha2_from_language, alpha3_from_language
from config import settings, get_array_from
from helper import path_mappings, pp_replace, get_target_folder, force_unicode
from list_subtitles import store_subtitles, list_missing_subtitles, store_subtitles_movie, list_missing_subtitles_movies
from utils import history_log, history_log_movie, get_binary, get_blacklist, notify_sonarr, notify_radarr
from notifier import send_notifications, send_notifications_movie
from get_providers import get_providers, get_providers_auth, provider_throttle, provider_pool
from knowit import api
from subsyncer import subsync
from guessit import guessit
from custom_lang import CustomLanguage
from database import database, dict_mapper, get_exclusion_clause, get_profiles_list, get_audio_profile_languages, \
    get_desired_languages
from event_handler import event_stream, show_progress, hide_progress
from embedded_subs_reader import parse_video_metadata

from analytics import track_event
from locale import getpreferredencoding


def get_video(path, title, sceneName, providers=None, media_type="movie"):
    """
    Construct `Video` instance
    :param path: path to video
    :param title: series/movie title
    :param sceneName: sceneName
    :param providers: provider list for selective hashing
    :param media_type: movie/series
    :return: `Video` instance
    """
    hints = {"title": title, "type": "movie" if media_type == "movie" else "episode"}
    used_scene_name = False
    original_path = path
    original_name = os.path.basename(path)
    hash_from = None
    if sceneName != "None":
        # use the sceneName but keep the folder structure for better guessing
        path = os.path.join(os.path.dirname(path), sceneName + os.path.splitext(path)[1])
        used_scene_name = True
        hash_from = original_path

    try:
        video = parse_video(path, hints=hints, providers=providers, dry_run=used_scene_name,
                            hash_from=hash_from)
        video.used_scene_name = used_scene_name
        video.original_name = original_name
        video.original_path = original_path

        refine_from_db(original_path, video)
        refine_from_ffprobe(original_path, video)

        logging.debug('BAZARR is using these video object properties: %s', vars(copy.deepcopy(video)))
        return video

    except Exception as e:
        logging.exception("BAZARR Error trying to get video information for this file: " + original_path)


def get_scores(video, media_type, min_score_movie_perc=60 * 100 / 120.0, min_score_series_perc=240 * 100 / 360.0,
               min_score_special_ep=180 * 100 / 360.0):
    """
    Get score range for a video.
    :param video: `Video` instance
    :param media_type: movie/series
    :param min_score_movie_perc: Percentage of max score for min score of movies
    :param min_score_series_perc: Percentage of max score for min score of series
    :param min_score_special_ep: Percentage of max score for min score of series special episode
    :return: tuple(min_score, max_score, set(scores))
    """
    max_score = 120.0
    min_score = max_score * min_score_movie_perc / 100.0
    scores = list(subliminal_scores.movie_scores.keys())
    if media_type == "series":
        max_score = 360.0
        min_score = max_score * min_score_series_perc / 100.0
        scores = list(subliminal_scores.episode_scores.keys())
        if video.is_special:
            min_score = max_score * min_score_special_ep / 100.0

    return min_score, max_score, set(scores)


def download_subtitle(path, language, audio_language, hi, forced, providers, providers_auth, sceneName, title,
                      media_type, forced_minimum_score=None, is_upgrade=False):
    # fixme: supply all missing languages, not only one, to hit providers only once who support multiple languages in
    #  one query

    if settings.general.getboolean('utf8_encode'):
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"

    logging.debug('BAZARR Searching subtitles for this file: ' + path)
    if hi == "True":
        hi = "force HI"
    else:
        hi = "force non-HI"

    if forced == "True":
        providers_auth['podnapisi']['only_foreign'] = True  ## fixme: This is also in get_providers_auth()
        providers_auth['subscene']['only_foreign'] = True  ## fixme: This is also in get_providers_auth()
        providers_auth['opensubtitles']['only_foreign'] = True  ## fixme: This is also in get_providers_auth()
    else:
        providers_auth['podnapisi']['only_foreign'] = False
        providers_auth['subscene']['only_foreign'] = False
        providers_auth['opensubtitles']['only_foreign'] = False

    language_set = set()

    if not isinstance(language, list):
        language = [language]

    for l in language:
        # Always use alpha2 in API Request
        l = alpha3_from_alpha2(l)

        lang_obj = _get_lang_obj(l)

        if forced == "True":
            lang_obj = Language.rebuild(lang_obj, forced=True)
        if hi == "force HI":
            lang_obj = Language.rebuild(lang_obj, hi=True)

        language_set.add(lang_obj)

    minimum_score = settings.general.minimum_score
    minimum_score_movie = settings.general.minimum_score_movie
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd
    single = settings.general.getboolean('single_language')


    # todo:
    """
    AsyncProviderPool:
    implement:
        blacklist=None,
        pre_download_hook=None,
        post_download_hook=None,
        language_hook=None
    """
    video = get_video(force_unicode(path), title, sceneName, providers=providers,
                      media_type=media_type)
    if video:
        min_score, max_score, scores = get_scores(video, media_type, min_score_movie_perc=int(minimum_score_movie),
                                                  min_score_series_perc=int(minimum_score))

        if providers:
            if forced_minimum_score:
                min_score = int(forced_minimum_score) + 1
            downloaded_subtitles = download_best_subtitles({video}, language_set, int(min_score), hi,
                                                           providers=providers,
                                                           provider_configs=providers_auth,
                                                           pool_class=provider_pool(),
                                                           compute_score=compute_score,
                                                           throttle_time=None,  # fixme
                                                           blacklist=get_blacklist(media_type=media_type),
                                                           throttle_callback=provider_throttle,
                                                           pre_download_hook=None,  # fixme
                                                           post_download_hook=None,  # fixme
                                                           language_hook=None)  # fixme
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

                for s in subtitles:
                    s.mods = subz_mods

                try:
                    fld = get_target_folder(path)
                    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                        'win') and settings.general.getboolean('chmod_enabled') else None
                    saved_subtitles = save_subtitles(video.original_path, subtitles, single=single,
                                                     tags=None,  # fixme
                                                     directory=fld,
                                                     chmod=chmod,
                                                     # formats=("srt", "vtt")
                                                     path_decoder=force_unicode
                                                     )
                except Exception as e:
                    logging.exception(
                        'BAZARR Error saving Subtitles file to disk for this file:' + path + ': ' + repr(e))
                    pass
                else:
                    saved_any = True
                    for subtitle in saved_subtitles:
                        downloaded_provider = subtitle.provider_name
                        downloaded_language_code3 = _get_download_code3(subtitle)

                        downloaded_language = language_from_alpha3(downloaded_language_code3)
                        downloaded_language_code2 = alpha2_from_alpha3(downloaded_language_code3)
                        audio_language_code2 = alpha2_from_language(audio_language)
                        audio_language_code3 = alpha3_from_language(audio_language)
                        downloaded_path = subtitle.storage_path
                        subtitle_id = subtitle.id
                        if subtitle.language.hi:
                            modifier_string = " HI"
                        elif subtitle.language.forced:
                            modifier_string = " forced"
                        else:
                            modifier_string = ""
                        logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                        if is_upgrade:
                            action = "upgraded"
                        else:
                            action = "downloaded"
                        percent_score = round(subtitle.score * 100 / max_score, 2)
                        message = downloaded_language + modifier_string + " subtitles " + action + " from " + \
                            downloaded_provider + " with a score of " + str(percent_score) + "%."

                        if media_type == 'series':
                            episode_metadata = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId FROM "
                                                                "table_episodes WHERE path = ?",
                                                                (path_mappings.path_replace_reverse(path),),
                                                                only_one=True)
                            series_id = episode_metadata['sonarrSeriesId']
                            episode_id = episode_metadata['sonarrEpisodeId']
                            sync_subtitles(video_path=path, srt_path=downloaded_path,
                                           srt_lang=downloaded_language_code2, media_type=media_type,
                                           percent_score=percent_score,
                                           sonarr_series_id=episode_metadata['sonarrSeriesId'],
                                           sonarr_episode_id=episode_metadata['sonarrEpisodeId'])
                        else:
                            movie_metadata = database.execute("SELECT radarrId FROM table_movies WHERE path = ?",
                                                              (path_mappings.path_replace_reverse_movie(path),),
                                                              only_one=True)
                            series_id = ""
                            episode_id = movie_metadata['radarrId']
                            sync_subtitles(video_path=path, srt_path=downloaded_path,
                                           srt_lang=downloaded_language_code2, media_type=media_type,
                                           percent_score=percent_score,
                                           radarr_id=movie_metadata['radarrId'])

                        if use_postprocessing is True:
                            command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                 downloaded_language_code2, downloaded_language_code3, audio_language,
                                                 audio_language_code2, audio_language_code3, subtitle.language.forced,
                                                 percent_score, subtitle_id, downloaded_provider, series_id, episode_id)

                            if media_type == 'series':
                                use_pp_threshold = settings.general.getboolean('use_postprocessing_threshold')
                                pp_threshold = int(settings.general.postprocessing_threshold)
                            else:
                                use_pp_threshold = settings.general.getboolean('use_postprocessing_threshold_movie')
                                pp_threshold = int(settings.general.postprocessing_threshold_movie)

                            if not use_pp_threshold or (use_pp_threshold and percent_score < pp_threshold):
                                logging.debug("BAZARR Using post-processing command: {}".format(command))
                                postprocessing(command, path)
                            else:
                                logging.debug("BAZARR post-processing skipped because subtitles score isn't below this "
                                              "threshold value: " + str(pp_threshold) + "%")

                        # fixme: support multiple languages at once
                        if media_type == 'series':
                            reversed_path = path_mappings.path_replace_reverse(path)
                            reversed_subtitles_path = path_mappings.path_replace_reverse(downloaded_path)
                            notify_sonarr(episode_metadata['sonarrSeriesId'])

                        else:
                            reversed_path = path_mappings.path_replace_reverse_movie(path)
                            reversed_subtitles_path = path_mappings.path_replace_reverse_movie(downloaded_path)
                            notify_radarr(movie_metadata['radarrId'])

                        track_event(category=downloaded_provider, action=action, label=downloaded_language)

                        return message, reversed_path, downloaded_language_code2, downloaded_provider, subtitle.score, \
                               subtitle.language.forced, subtitle.id, reversed_subtitles_path, subtitle.language.hi

        if not saved_any:
            logging.debug('BAZARR No Subtitles were found for this file: ' + path)
            return None

    subliminal.region.backend.sync()

    logging.debug('BAZARR Ended searching Subtitles for file: ' + path)


def manual_search(path, profileId, providers, providers_auth, sceneName, title, media_type):
    logging.debug('BAZARR Manually searching subtitles for this file: ' + path)

    final_subtitles = []

    initial_language_set = set()
    language_set = set()

    # where [3] is items list of dict(id, lang, forced, hi)
    language_items = get_profiles_list(profile_id=int(profileId))['items']

    for language in language_items:
        forced = language['forced']
        hi = language['hi']
        audio_exclude = language['audio_exclude']
        language = language['language']

        lang = alpha3_from_alpha2(language)

        lang_obj = _get_lang_obj(lang)

        if forced == "True":
            lang_obj = Language.rebuild(lang_obj, forced=True)

            providers_auth['podnapisi']['also_foreign'] = True
            providers_auth['opensubtitles']['also_foreign'] = True

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

    minimum_score = settings.general.minimum_score
    minimum_score_movie = settings.general.minimum_score_movie
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd
    if providers:
        video = get_video(force_unicode(path), title, sceneName, providers=providers,
                          media_type=media_type)
    else:
        logging.info("BAZARR All providers are throttled")
        return None
    if video:
        min_score, max_score, scores = get_scores(video, media_type, min_score_movie_perc=int(minimum_score_movie),
                                                  min_score_series_perc=int(minimum_score))

        try:
            if providers:
                subtitles = list_all_subtitles([video], language_set,
                                               providers=providers,
                                               provider_configs=providers_auth,
                                               blacklist=get_blacklist(media_type=media_type),
                                               throttle_callback=provider_throttle,
                                               language_hook=None)  # fixme

                if 'subscene' in providers:
                    subscene_language_set = set()
                    for language in language_set:
                        if language.forced:
                            subscene_language_set.add(language)
                    if len(subscene_language_set):
                        providers_auth['subscene']['only_foreign'] = True
                        subtitles_subscene = list_all_subtitles([video], subscene_language_set,
                                                                providers=['subscene'],
                                                                provider_configs=providers_auth,
                                                                blacklist=get_blacklist(media_type=media_type),
                                                                throttle_callback=provider_throttle,
                                                                language_hook=None)  # fixme
                        providers_auth['subscene']['only_foreign'] = False
                        subtitles[video] += subtitles_subscene[video]
            else:
                subtitles = []
                logging.info("BAZARR All providers are throttled")
                return None
        except Exception as e:
            logging.exception("BAZARR Error trying to get Subtitle list from provider for this file: " + path)
        else:
            subtitles_list = []

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
                        logging.debug(u"BAZARR Skipping %s, because it doesn't match our series/episode", s)
                        continue

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

                score, score_without_hash = compute_score(matches, s, video, hearing_impaired=initial_hi)
                if 'hash' not in matches:
                    not_matched = scores - matches
                else:
                    not_matched = set()
                s.score = score

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


def manual_download_subtitle(path, language, audio_language, hi, forced, subtitle, provider, providers_auth, sceneName,
                             title, media_type):
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
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd
    single = settings.general.getboolean('single_language')
    video = get_video(force_unicode(path), title, sceneName, providers={provider},
                      media_type=media_type)
    if video:
        min_score, max_score, scores = get_scores(video, media_type)
        try:
            if provider:
                download_subtitles([subtitle],
                                   providers={provider},
                                   provider_configs=providers_auth,
                                   pool_class=provider_pool(),
                                   blacklist=get_blacklist(media_type=media_type),
                                   throttle_callback=provider_throttle)
                logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
            else:
                logging.info("BAZARR All providers are throttled")
                return None
        except Exception as e:
            logging.exception('BAZARR Error downloading Subtitles for this file ' + path)
            return None
        else:
            if not subtitle.is_valid():
                logging.exception('BAZARR No valid Subtitles file found for this file: ' + path)
                return
            try:
                score = round(subtitle.score / max_score * 100, 2)
                fld = get_target_folder(path)
                chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                    'win') and settings.general.getboolean('chmod_enabled') else None
                saved_subtitles = save_subtitles(video.original_path, [subtitle], single=single,
                                                 tags=None,  # fixme
                                                 directory=fld,
                                                 chmod=chmod,
                                                 # formats=("srt", "vtt")
                                                 path_decoder=force_unicode)

            except Exception as e:
                logging.exception('BAZARR Error saving Subtitles file to disk for this file:' + path)
                return
            else:
                if saved_subtitles:
                    for saved_subtitle in saved_subtitles:
                        downloaded_provider = saved_subtitle.provider_name
                        downloaded_language_code3 = _get_download_code3(subtitle)

                        downloaded_language = language_from_alpha3(downloaded_language_code3)
                        downloaded_language_code2 = alpha2_from_alpha3(downloaded_language_code3)
                        audio_language_code2 = alpha2_from_language(audio_language)
                        audio_language_code3 = alpha3_from_language(audio_language)
                        downloaded_path = saved_subtitle.storage_path
                        subtitle_id = subtitle.id
                        logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                        if subtitle.language.hi:
                            modifier_string = " HI"
                        elif subtitle.language.forced:
                            modifier_string = " forced"
                        else:
                            modifier_string = ""
                        message = downloaded_language + modifier_string + " subtitles downloaded from " + \
                                  downloaded_provider + " with a score of " + str(score) + "% using manual search."

                        if media_type == 'series':
                            episode_metadata = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId FROM "
                                                                "table_episodes WHERE path = ?",
                                                                (path_mappings.path_replace_reverse(path),),
                                                                only_one=True)
                            series_id = episode_metadata['sonarrSeriesId']
                            episode_id = episode_metadata['sonarrEpisodeId']
                            sync_subtitles(video_path=path, srt_path=downloaded_path,
                                           srt_lang=downloaded_language_code2, media_type=media_type,
                                           percent_score=score,
                                           sonarr_series_id=episode_metadata['sonarrSeriesId'],
                                           sonarr_episode_id=episode_metadata['sonarrEpisodeId'])
                        else:
                            movie_metadata = database.execute("SELECT radarrId FROM table_movies WHERE path = ?",
                                                              (path_mappings.path_replace_reverse_movie(path),),
                                                              only_one=True)
                            series_id = ""
                            episode_id = movie_metadata['radarrId']
                            sync_subtitles(video_path=path, srt_path=downloaded_path,
                                           srt_lang=downloaded_language_code2, media_type=media_type,
                                           percent_score=score, radarr_id=movie_metadata['radarrId'])

                        if use_postprocessing:
                            percent_score = round(subtitle.score * 100 / max_score, 2)
                            command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                 downloaded_language_code2, downloaded_language_code3, audio_language,
                                                 audio_language_code2, audio_language_code3, subtitle.language.forced,
                                                 percent_score, subtitle_id, downloaded_provider, series_id, episode_id)

                            if media_type == 'series':
                                use_pp_threshold = settings.general.getboolean('use_postprocessing_threshold')
                                pp_threshold = settings.general.postprocessing_threshold
                            else:
                                use_pp_threshold = settings.general.getboolean('use_postprocessing_threshold_movie')
                                pp_threshold = settings.general.postprocessing_threshold_movie

                            if not use_pp_threshold or (use_pp_threshold and score < float(pp_threshold)):
                                logging.debug("BAZARR Using post-processing command: {}".format(command))
                                postprocessing(command, path)
                            else:
                                logging.debug("BAZARR post-processing skipped because subtitles score isn't below this "
                                              "threshold value: " + pp_threshold + "%")

                        if media_type == 'series':
                            reversed_path = path_mappings.path_replace_reverse(path)
                            reversed_subtitles_path = path_mappings.path_replace_reverse(downloaded_path)
                            notify_sonarr(episode_metadata['sonarrSeriesId'])
                        else:
                            reversed_path = path_mappings.path_replace_reverse_movie(path)
                            reversed_subtitles_path = path_mappings.path_replace_reverse_movie(downloaded_path)
                            notify_radarr(movie_metadata['radarrId'])

                        track_event(category=downloaded_provider, action="manually_downloaded",
                                    label=downloaded_language)

                        return message, reversed_path, downloaded_language_code2, downloaded_provider, subtitle.score, \
                               subtitle.language.forced, subtitle.id, reversed_subtitles_path, subtitle.language.hi
                else:
                    logging.error(
                        "BAZARR Tried to manually download a Subtitles for file: " + path + " but we weren't able to do (probably throttled by " + str(
                            subtitle.provider_name) + ". Please retry later or select a Subtitles from another provider.")
                    return None

    subliminal.region.backend.sync()

    logging.debug('BAZARR Ended manually downloading Subtitles for file: ' + path)


def manual_upload_subtitle(path, language, forced, title, scene_name, media_type, subtitle, audio_language):
    logging.debug('BAZARR Manually uploading subtitles for this file: ' + path)

    single = settings.general.getboolean('single_language')

    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd

    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.getboolean('chmod_enabled') else None

    language = alpha3_from_alpha2(language)
    
    custom = Language.from_value(language)
    if custom is None:
        lang_obj = Language(language)
    else:
        lang_obj = custom.subzero_language()

    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)

    sub = Subtitle(
        lang_obj,
        mods = get_array_from(settings.general.subzero_mods)
    )

    sub.content = subtitle.read()
    if not sub.is_valid():
        logging.exception('BAZARR Invalid subtitle file: ' + subtitle.filename)
        sub.mods = None

    if settings.general.getboolean('utf8_encode'):
        sub.set_encoding("utf-8")

    saved_subtitles = []
    try:
        saved_subtitles = save_subtitles(path,
                                         [sub],
                                         single=single,
                                         tags=None,  # fixme
                                         directory=get_target_folder(path),
                                         chmod=chmod,
                                         # formats=("srt", "vtt")
                                         path_decoder=force_unicode)
    except:
        pass

    if len(saved_subtitles) < 1:
        logging.exception('BAZARR Error saving Subtitles file to disk for this file:' + path)
        return

    subtitle_path = saved_subtitles[0].storage_path
    message = language_from_alpha3(language) + (" forced" if forced else "") + " Subtitles manually uploaded."

    uploaded_language_code3 = language
    uploaded_language = language_from_alpha3(uploaded_language_code3)
    uploaded_language_code2 = alpha2_from_alpha3(uploaded_language_code3)
    audio_language_code2 = alpha2_from_language(audio_language)
    audio_language_code3 = alpha3_from_language(audio_language)

    if media_type == 'series':
        episode_metadata = database.execute("SELECT sonarrSeriesId, sonarrEpisodeId FROM table_episodes WHERE path = ?",
                                            (path_mappings.path_replace_reverse(path),),
                                            only_one=True)
        series_id = episode_metadata['sonarrSeriesId']
        episode_id = episode_metadata['sonarrEpisodeId']
        sync_subtitles(video_path=path, srt_path=subtitle_path, srt_lang=uploaded_language_code2, media_type=media_type,
                       percent_score=100, sonarr_series_id=episode_metadata['sonarrSeriesId'],
                       sonarr_episode_id=episode_metadata['sonarrEpisodeId'])
    else:
        movie_metadata = database.execute("SELECT radarrId FROM table_movies WHERE path = ?",
                                          (path_mappings.path_replace_reverse_movie(path),),
                                          only_one=True)
        series_id = ""
        episode_id = movie_metadata['radarrId']
        sync_subtitles(video_path=path, srt_path=subtitle_path, srt_lang=uploaded_language_code2, media_type=media_type,
                       percent_score=100, radarr_id=movie_metadata['radarrId'])

    if use_postprocessing :
        command = pp_replace(postprocessing_cmd, path, subtitle_path, uploaded_language,
                             uploaded_language_code2, uploaded_language_code3, audio_language,
                             audio_language_code2, audio_language_code3, forced, 100, "1", "manual", series_id, episode_id)
        postprocessing(command, path)

    if media_type == 'series':
        reversed_path = path_mappings.path_replace_reverse(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse(subtitle_path)
        notify_sonarr(episode_metadata['sonarrSeriesId'])
    else:
        reversed_path = path_mappings.path_replace_reverse_movie(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse_movie(subtitle_path)
        notify_radarr(movie_metadata['radarrId'])

    return message, reversed_path, reversed_subtitles_path


def series_download_subtitles(no):
    episodes_details = database.execute("SELECT table_episodes.path, table_episodes.missing_subtitles, monitored, "
                                        "table_episodes.sonarrEpisodeId, table_episodes.scene_name, table_shows.tags, "
                                        "table_shows.seriesType, table_episodes.audio_language, table_shows.title, "
                                        "table_episodes.season, table_episodes.episode, table_episodes.title as episodeTitle "
                                        "FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = "
                                        "table_episodes.sonarrSeriesId WHERE table_episodes.sonarrSeriesId=? and "
                                        "missing_subtitles!='[]'" + get_exclusion_clause('series'), (no,))
    if not episodes_details:
        logging.debug("BAZARR no episode for that sonarrSeriesId can be found in database:", str(no))
        return

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    count_episodes_details = len(episodes_details)

    for i, episode in enumerate(episodes_details, 1):
        if providers_list:
            show_progress(id='series_search_progress_{}'.format(no),
                          header='Searching missing subtitles...',
                          name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['title'],
                                                                     episode['season'],
                                                                     episode['episode'],
                                                                     episode['episodeTitle']),
                          value=i,
                          count=count_episodes_details)

            for language in ast.literal_eval(episode['missing_subtitles']):
                if language is not None:
                    audio_language_list = get_audio_profile_languages(episode_id=episode['sonarrEpisodeId'])
                    if len(audio_language_list) > 0:
                        audio_language = audio_language_list[0]['name']
                    else:
                        audio_language = 'None'

                    result = download_subtitle(path_mappings.path_replace(episode['path']),
                                               language.split(':')[0],
                                               audio_language,
                                               "True" if language.endswith(':hi') else "False",
                                               "True" if language.endswith(':forced') else "False",
                                               providers_list,
                                               providers_auth,
                                               str(episode['scene_name']),
                                               episode['title'],
                                               'series')
                    if result is not None:
                        message = result[0]
                        path = result[1]
                        forced = result[5]
                        if result[8]:
                            language_code = result[2] + ":hi"
                        elif forced:
                            language_code = result[2] + ":forced"
                        else:
                            language_code = result[2]
                        provider = result[3]
                        score = result[4]
                        subs_id = result[6]
                        subs_path = result[7]
                        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
                        history_log(1, no, episode['sonarrEpisodeId'], message, path, language_code, provider, score,
                                    subs_id, subs_path)
                        send_notifications(no, episode['sonarrEpisodeId'], message)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    show_progress(id='series_search_progress_{}'.format(no),
                  header='Searching missing subtitles...',
                  name='Completed successfully',
                  value=count_episodes_details,
                  count=count_episodes_details)

    hide_progress(id='series_search_progress_{}'.format(no))

    


def episode_download_subtitles(no):
    episodes_details = database.execute("SELECT table_episodes.path, table_episodes.missing_subtitles, monitored, "
                                        "table_episodes.sonarrEpisodeId, table_episodes.scene_name, table_shows.tags, "
                                        "table_shows.title, table_shows.sonarrSeriesId, table_episodes.audio_language, "
                                        "table_shows.seriesType FROM table_episodes LEFT JOIN table_shows on "
                                        "table_episodes.sonarrSeriesId = table_shows.sonarrSeriesId WHERE sonarrEpisodeId=?" +
                                        get_exclusion_clause('series'), (no,))
    if not episodes_details:
        logging.debug("BAZARR no episode with that sonarrEpisodeId can be found in database:", str(no))
        return

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for episode in episodes_details:
        if providers_list:
            for language in ast.literal_eval(episode['missing_subtitles']):
                if language is not None:
                    audio_language_list = get_audio_profile_languages(episode_id=episode['sonarrEpisodeId'])
                    if len(audio_language_list) > 0:
                        audio_language = audio_language_list[0]['name']
                    else:
                        audio_language = 'None'

                    result = download_subtitle(path_mappings.path_replace(episode['path']),
                                               language.split(':')[0],
                                               audio_language,
                                               "True" if language.endswith(':hi') else "False",
                                               "True" if language.endswith(':forced') else "False",
                                               providers_list,
                                               providers_auth,
                                               str(episode['scene_name']),
                                               episode['title'],
                                               'series')
                    if result is not None:
                        message = result[0]
                        path = result[1]
                        forced = result[5]
                        if result[8]:
                            language_code = result[2] + ":hi"
                        elif forced:
                            language_code = result[2] + ":forced"
                        else:
                            language_code = result[2]
                        provider = result[3]
                        score = result[4]
                        subs_id = result[6]
                        subs_path = result[7]
                        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
                        history_log(1, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message, path,
                                    language_code, provider, score, subs_id, subs_path)
                        send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message)
        else:
            logging.info("BAZARR All providers are throttled")
            break


def movies_download_subtitles(no):
    movies = database.execute(
        "SELECT path, missing_subtitles, audio_language, radarrId, sceneName, title, tags, "
        "monitored FROM table_movies WHERE radarrId=?" + get_exclusion_clause('movie'), (no,))
    if not len(movies):
        logging.debug("BAZARR no movie with that radarrId can be found in database:", str(no))
        return
    else:
        movie = movies[0]

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    if ast.literal_eval(movie['missing_subtitles']):
        count_movie = len(ast.literal_eval(movie['missing_subtitles']))
    else:
        count_movie = 0

    for i, language in enumerate(ast.literal_eval(movie['missing_subtitles']), 1):
        if providers_list:
            show_progress(id='movie_search_progress_{}'.format(no),
                          header='Searching missing subtitles...',
                          name=movie['title'],
                          value=i,
                          count=count_movie)

            if language is not None:
                audio_language_list = get_audio_profile_languages(movie_id=movie['radarrId'])
                if len(audio_language_list) > 0:
                    audio_language = audio_language_list[0]['name']
                else:
                    audio_language = 'None'

                result = download_subtitle(path_mappings.path_replace_movie(movie['path']),
                                           language.split(':')[0],
                                           audio_language,
                                           "True" if language.endswith(':hi') else "False",
                                           "True" if language.endswith(':forced') else "False",
                                           providers_list,
                                           providers_auth,
                                           str(movie['sceneName']),
                                           movie['title'],
                                           'movie')
                if result is not None:
                    message = result[0]
                    path = result[1]
                    forced = result[5]
                    if result[8]:
                        language_code = result[2] + ":hi"
                    elif forced:
                        language_code = result[2] + ":forced"
                    else:
                        language_code = result[2]
                    provider = result[3]
                    score = result[4]
                    subs_id = result[6]
                    subs_path = result[7]
                    store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
                    history_log_movie(1, no, message, path, language_code, provider, score, subs_id, subs_path)
                    send_notifications_movie(no, message)
        else:
            logging.info("BAZARR All providers are throttled")
            break

    show_progress(id='movie_search_progress_{}'.format(no),
                  header='Searching missing subtitles...',
                  name='Completed successfully',
                  value=count_movie,
                  count=count_movie)

    hide_progress(id='movie_search_progress_{}'.format(no))


def wanted_download_subtitles(path):
    episodes_details = database.execute("SELECT table_episodes.path, table_episodes.missing_subtitles, "
                                        "table_episodes.sonarrEpisodeId, table_episodes.sonarrSeriesId, "
                                        "table_episodes.audio_language, table_episodes.scene_name,"
                                        "table_episodes.failedAttempts, table_shows.title "
                                        "FROM table_episodes LEFT JOIN table_shows on "
                                        "table_episodes.sonarrSeriesId = table_shows.sonarrSeriesId "
                                        "WHERE table_episodes.path=? and table_episodes.missing_subtitles!='[]'",
                                        (path_mappings.path_replace_reverse(path),))

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for episode in episodes_details:
        attempt = episode['failedAttempts']
        if type(attempt) == str:
            attempt = ast.literal_eval(attempt)
        for language in ast.literal_eval(episode['missing_subtitles']):
            if attempt is None:
                attempt = []
                attempt.append([language, time.time()])
            else:
                att = list(zip(*attempt))[0]
                if language not in att:
                    attempt.append([language, time.time()])

            database.execute("UPDATE table_episodes SET failedAttempts=? WHERE sonarrEpisodeId=?",
                             (str(attempt), episode['sonarrEpisodeId']))

            for i in range(len(attempt)):
                if attempt[i][0] == language:
                    if search_active(attempt[i][1]):
                        audio_language_list = get_audio_profile_languages(episode_id=episode['sonarrEpisodeId'])
                        if len(audio_language_list) > 0:
                            audio_language = audio_language_list[0]['name']
                        else:
                            audio_language = 'None'

                        result = download_subtitle(path_mappings.path_replace(episode['path']),
                                                   language.split(':')[0],
                                                   audio_language,
                                                   "True" if language.endswith(':hi') else "False",
                                                   "True" if language.endswith(':forced') else "False",
                                                   providers_list,
                                                   providers_auth,
                                                   str(episode['scene_name']),
                                                   episode['title'],
                                                   'series')
                        if result is not None:
                            message = result[0]
                            path = result[1]
                            forced = result[5]
                            if result[8]:
                                language_code = result[2] + ":hi"
                            elif forced:
                                language_code = result[2] + ":forced"
                            else:
                                language_code = result[2]
                            provider = result[3]
                            score = result[4]
                            subs_id = result[6]
                            subs_path = result[7]
                            store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
                            history_log(1, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message, path,
                                        language_code, provider, score, subs_id, subs_path)
                            event_stream(type='episode-wanted', action='delete', payload=episode['sonarrEpisodeId'])
                            send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message)
                    else:
                        logging.debug(
                            'BAZARR Search is not active for episode ' + episode['path'] + ' Language: ' + attempt[i][
                                0])


def wanted_download_subtitles_movie(path):
    movies_details = database.execute(
        "SELECT path, missing_subtitles, radarrId, audio_language, sceneName, "
        "failedAttempts, title FROM table_movies WHERE path = ? "
        "AND missing_subtitles != '[]'", (path_mappings.path_replace_reverse_movie(path),))

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for movie in movies_details:
        attempt = movie['failedAttempts']
        if type(attempt) == str:
            attempt = ast.literal_eval(attempt)
        for language in ast.literal_eval(movie['missing_subtitles']):
            if attempt is None:
                attempt = []
                attempt.append([language, time.time()])
            else:
                att = list(zip(*attempt))[0]
                if language not in att:
                    attempt.append([language, time.time()])

            database.execute("UPDATE table_movies SET failedAttempts=? WHERE radarrId=?",
                             (str(attempt), movie['radarrId']))

            for i in range(len(attempt)):
                if attempt[i][0] == language:
                    if search_active(attempt[i][1]) is True:
                        audio_language_list = get_audio_profile_languages(movie_id=movie['radarrId'])
                        if len(audio_language_list) > 0:
                            audio_language = audio_language_list[0]['name']
                        else:
                            audio_language = 'None'

                        result = download_subtitle(path_mappings.path_replace_movie(movie['path']),
                                                   language.split(':')[0],
                                                   audio_language,
                                                   "True" if language.endswith(':hi') else "False",
                                                   "True" if language.endswith(':forced') else "False",
                                                   providers_list,
                                                   providers_auth,
                                                   str(movie['sceneName']),
                                                   movie['title'],
                                                   'movie')
                        if result is not None:
                            message = result[0]
                            path = result[1]
                            forced = result[5]
                            if result[8]:
                                language_code = result[2] + ":hi"
                            elif forced:
                                language_code = result[2] + ":forced"
                            else:
                                language_code = result[2]
                            provider = result[3]
                            score = result[4]
                            subs_id = result[6]
                            subs_path = result[7]
                            store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
                            history_log_movie(1, movie['radarrId'], message, path, language_code, provider, score,
                                              subs_id, subs_path)
                            event_stream(type='movie-wanted', action='delete', payload=movie['radarrId'])
                            send_notifications_movie(movie['radarrId'], message)
                    else:
                        logging.info(
                            'BAZARR Search is not active for this Movie ' + movie['path'] + ' Language: ' + attempt[i][
                                0])


def wanted_search_missing_subtitles_series():
    episodes = database.execute("SELECT table_episodes.path, table_shows.tags, table_episodes.monitored, "
                                "table_shows.title, table_episodes.season, table_episodes.episode, table_episodes.title"
                                " as episodeTitle, table_shows.seriesType FROM table_episodes INNER JOIN table_shows on"
                                " table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE missing_subtitles !="
                                " '[]'" + get_exclusion_clause('series'))
    # path_replace
    dict_mapper.path_replace(episodes)

    count_episodes = len(episodes)
    for i, episode in enumerate(episodes, 1):
        show_progress(id='wanted_episodes_progress',
                      header='Searching subtitles...',
                      name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['title'],
                                                                 episode['season'],
                                                                 episode['episode'],
                                                                 episode['episodeTitle']),
                      value=i,
                      count=count_episodes)

        providers = get_providers()
        if providers:
            wanted_download_subtitles(episode['path'])
        else:
            logging.info("BAZARR All providers are throttled")
            return

    show_progress(id='wanted_episodes_progress',
                  header='Searching subtitles...',
                  name='Completed successfully',
                  value=count_episodes,
                  count=count_episodes)

    hide_progress(id='wanted_episodes_progress')

    logging.info('BAZARR Finished searching for missing Series Subtitles. Check History for more information.')


def wanted_search_missing_subtitles_movies():
    movies = database.execute("SELECT path, tags, monitored, title FROM table_movies WHERE missing_subtitles != '[]'" +
                              get_exclusion_clause('movie'))
    # path_replace
    dict_mapper.path_replace_movie(movies)

    count_movies = len(movies)
    for i, movie in enumerate(movies, 1):
        show_progress(id='wanted_movies_progress',
                      header='Searching subtitles...',
                      name=movie['title'],
                      value=i,
                      count=count_movies)

        providers = get_providers()
        if providers:
            wanted_download_subtitles_movie(movie['path'])
        else:
            logging.info("BAZARR All providers are throttled")
            return

    show_progress(id='wanted_movies_progress',
                  header='Searching subtitles...',
                  name='Completed successfully',
                  value=count_movies,
                  count=count_movies)

    hide_progress(id='wanted_movies_progress')
    
    logging.info('BAZARR Finished searching for missing Movies Subtitles. Check History for more information.')


def search_active(timestamp):
    if settings.general.getboolean('adaptive_searching'):
        search_deadline = timedelta(weeks=3)
        search_delta = timedelta(weeks=1)
        aa = datetime.fromtimestamp(float(timestamp))
        attempt_datetime = datetime.strptime(str(aa).split(".")[0], '%Y-%m-%d %H:%M:%S')
        attempt_search_deadline = attempt_datetime + search_deadline
        today = datetime.today()
        attempt_age_in_days = (today.date() - attempt_search_deadline.date()).days
        if today.date() <= attempt_search_deadline.date():
            return True
        elif attempt_age_in_days % search_delta.days == 0:
            return True
        else:
            return False
    else:
        return True


def convert_to_guessit(guessit_key, attr_from_db):
    try:
        return guessit(attr_from_db)[guessit_key]
    except KeyError:
        return attr_from_db


def refine_from_db(path, video):
    if isinstance(video, Episode):
        data = database.execute(
            "SELECT table_shows.title as seriesTitle, table_episodes.season, table_episodes.episode, "
            "table_episodes.title as episodeTitle, table_shows.year, table_shows.tvdbId, "
            "table_shows.alternateTitles, table_episodes.format, table_episodes.resolution, "
            "table_episodes.video_codec, table_episodes.audio_codec, table_episodes.path, table_shows.imdbId "
            "FROM table_episodes INNER JOIN table_shows on "
            "table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId "
            "WHERE table_episodes.path = ?", (path_mappings.path_replace_reverse(path),), only_one=True)

        if data:
            video.series = re.sub(r'\s(\(\d\d\d\d\))', '', data['seriesTitle'])
            video.season = int(data['season'])
            video.episode = int(data['episode'])
            video.title = data['episodeTitle']
            # Commented out because Sonarr provided so much bad year
            # if data['year']:
            #     if int(data['year']) > 0: video.year = int(data['year'])
            video.series_tvdb_id = int(data['tvdbId'])
            video.alternative_series = ast.literal_eval(data['alternateTitles'])
            if data['imdbId'] and not video.series_imdb_id:
                video.series_imdb_id = data['imdbId']
            if not video.source:
                video.source = convert_to_guessit('source', str(data['format']))
            if not video.resolution:
                video.resolution = str(data['resolution'])
            if not video.video_codec:
                if data['video_codec']: video.video_codec = convert_to_guessit('video_codec', data['video_codec'])
            if not video.audio_codec:
                if data['audio_codec']: video.audio_codec = convert_to_guessit('audio_codec', data['audio_codec'])
    elif isinstance(video, Movie):
        data = database.execute("SELECT title, year, alternativeTitles, format, resolution, video_codec, audio_codec, "
                                "imdbId FROM table_movies WHERE path = ?",
                                (path_mappings.path_replace_reverse_movie(path),), only_one=True)

        if data:
            video.title = re.sub(r'\s(\(\d\d\d\d\))', '', data['title'])
            # Commented out because Radarr provided so much bad year
            # if data['year']:
            #     if int(data['year']) > 0: video.year = int(data['year'])
            if data['imdbId'] and not video.imdb_id:
                video.imdb_id = data['imdbId']
            video.alternative_titles = ast.literal_eval(data['alternativeTitles'])
            if not video.source:
                if data['format']: video.source = convert_to_guessit('source', data['format'])
            if not video.resolution:
                if data['resolution']: video.resolution = data['resolution']
            if not video.video_codec:
                if data['video_codec']: video.video_codec = convert_to_guessit('video_codec', data['video_codec'])
            if not video.audio_codec:
                if data['audio_codec']: video.audio_codec = convert_to_guessit('audio_codec', data['audio_codec'])

    return video


def refine_from_ffprobe(path, video):
    if isinstance(video, Movie):
        file_id = database.execute("SELECT movie_file_id FROM table_shows WHERE path = ?",
                                   (path_mappings.path_replace_reverse_movie(path),), only_one=True)
    else:
        file_id = database.execute("SELECT episode_file_id, file_size FROM table_episodes WHERE path = ?",
                                   (path_mappings.path_replace_reverse(path),), only_one=True)

    if not isinstance(file_id, dict):
        return video

    if isinstance(video, Movie):
        data = parse_video_metadata(file=path, file_size=file_id['file_size'],
                                    movie_file_id=file_id['movie_file_id'])
    else:
        data = parse_video_metadata(file=path, file_size=file_id['file_size'],
                                    episode_file_id=file_id['episode_file_id'])

    if not data['ffprobe']:
        logging.debug("No FFprobe available in cache for this file: {}".format(path))
        return video

    logging.debug('FFprobe found: %s', data['ffprobe'])

    if 'video' not in data['ffprobe']:
        logging.debug('BAZARR FFprobe was unable to find video tracks in the file!')
    else:
        if 'resolution' in data['ffprobe']['video'][0]:
            if not video.resolution:
                video.resolution = data['ffprobe']['video'][0]['resolution']
        if 'codec' in data['ffprobe']['video'][0]:
            if not video.video_codec:
                video.video_codec = data['ffprobe']['video'][0]['codec']
        if 'frame_rate' in data['ffprobe']['video'][0]:
            if not video.fps:
                if isinstance(data['ffprobe']['video'][0]['frame_rate'], float):
                    video.fps = data['ffprobe']['video'][0]['frame_rate']
                else:
                    video.fps = data['ffprobe']['video'][0]['frame_rate'].magnitude

    if 'audio' not in data['ffprobe']:
        logging.debug('BAZARR FFprobe was unable to find audio tracks in the file!')
    else:
        if 'codec' in data['ffprobe']['audio'][0]:
            if not video.audio_codec:
                video.audio_codec = data['ffprobe']['audio'][0]['codec']
        for track in data['ffprobe']['audio']:
            if 'language' in track:
                video.audio_languages.add(track['language'].alpha3)

    return video


def upgrade_subtitles():
    days_to_upgrade_subs = settings.general.days_to_upgrade_subs
    minimum_timestamp = ((datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                         datetime(1970, 1, 1)).total_seconds()

    if settings.general.getboolean('upgrade_manual'):
        query_actions = [1, 2, 3, 4, 6]
    else:
        query_actions = [1, 3]

    if settings.general.getboolean('use_sonarr'):
        upgradable_episodes = database.execute("SELECT table_history.video_path, table_history.language, "
                                               "table_history.score, table_shows.tags, table_shows.profileId, "
                                               "table_episodes.audio_language, table_episodes.scene_name, "
                                               "table_episodes.title, table_episodes.sonarrSeriesId, table_history.action, "
                                               "table_history.subtitles_path, table_episodes.sonarrEpisodeId, "
                                               "MAX(table_history.timestamp) as timestamp, table_episodes.monitored, "
                                               "table_episodes.season, table_episodes.episode, table_shows.title as seriesTitle, "
                                               "table_shows.seriesType FROM table_history INNER JOIN table_shows on "
                                               "table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN "
                                               "table_episodes on table_episodes.sonarrEpisodeId = "
                                               "table_history.sonarrEpisodeId WHERE action IN "
                                               "(" + ','.join(map(str, query_actions)) + ") AND timestamp > ? AND "
                                               "score is not null" + get_exclusion_clause('series') + " GROUP BY "
                                               "table_history.video_path, table_history.language",
                                               (minimum_timestamp,))
        upgradable_episodes_not_perfect = []
        for upgradable_episode in upgradable_episodes:
            if upgradable_episode['timestamp'] > minimum_timestamp:
                try:
                    int(upgradable_episode['score'])
                except ValueError:
                    pass
                else:
                    if int(upgradable_episode['score']) < 360 or (settings.general.getboolean('upgrade_manual') and
                                                                  upgradable_episode['action'] in [2, 4, 6]):
                        upgradable_episodes_not_perfect.append(upgradable_episode)

        episodes_to_upgrade = []
        for episode in upgradable_episodes_not_perfect:
            if os.path.exists(path_mappings.path_replace(episode['subtitles_path'])) and int(episode['score']) < 357:
                episodes_to_upgrade.append(episode)

        count_episode_to_upgrade = len(episodes_to_upgrade)

    if settings.general.getboolean('use_radarr'):
        upgradable_movies = database.execute("SELECT table_history_movie.video_path, table_history_movie.language, "
                                             "table_history_movie.score, table_movies.profileId, table_history_movie.action, "
                                             "table_history_movie.subtitles_path, table_movies.audio_language, "
                                             "table_movies.sceneName, table_movies.title, table_movies.radarrId, "
                                             "MAX(table_history_movie.timestamp) as timestamp, table_movies.tags, "
                                             "table_movies.monitored FROM table_history_movie INNER JOIN table_movies "
                                             "on table_movies.radarrId = table_history_movie.radarrId WHERE action  IN "
                                             "(" + ','.join(map(str, query_actions)) + ") AND timestamp > ? AND score "
                                             "is not null" + get_exclusion_clause('movie') + " GROUP BY "
                                             "table_history_movie.video_path, table_history_movie.language",
                                             (minimum_timestamp,))
        upgradable_movies_not_perfect = []
        for upgradable_movie in upgradable_movies:
            if upgradable_movie['timestamp'] > minimum_timestamp:
                try:
                    int(upgradable_movie['score'])
                except ValueError:
                    pass
                else:
                    if int(upgradable_movie['score']) < 120 or (settings.general.getboolean('upgrade_manual') and
                                                                upgradable_movie['action'] in [2, 4, 6]):
                        upgradable_movies_not_perfect.append(upgradable_movie)

        movies_to_upgrade = []
        for movie in upgradable_movies_not_perfect:
            if os.path.exists(path_mappings.path_replace_movie(movie['subtitles_path'])) and int(movie['score']) < 117:
                movies_to_upgrade.append(movie)

        count_movie_to_upgrade = len(movies_to_upgrade)

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    if settings.general.getboolean('use_sonarr'):
        for i, episode in enumerate(episodes_to_upgrade, 1):
            show_progress(id='upgrade_episodes_progress',
                          header='Upgrading episodes subtitles...',
                          name='{0} - S{1:02d}E{2:02d} - {3}'.format(episode['seriesTitle'],
                                                                     episode['season'],
                                                                     episode['episode'],
                                                                     episode['title']),
                          value=i,
                          count=count_episode_to_upgrade)

            providers = get_providers()
            if not providers:
                logging.info("BAZARR All providers are throttled")
                return
            if episode['language'].endswith('forced'):
                language = episode['language'].split(':')[0]
                is_forced = "True"
                is_hi = "False"
            elif episode['language'].endswith('hi'):
                language = episode['language'].split(':')[0]
                is_forced = "False"
                is_hi = "True"
            else:
                language = episode['language'].split(':')[0]
                is_forced = "False"
                is_hi = "False"

            audio_language_list = get_audio_profile_languages(episode_id=episode['sonarrEpisodeId'])
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            result = download_subtitle(path_mappings.path_replace(episode['video_path']),
                                       language,
                                       audio_language,
                                       is_hi,
                                       is_forced,
                                       providers_list,
                                       providers_auth,
                                       str(episode['scene_name']),
                                       episode['title'],
                                       'series',
                                       forced_minimum_score=int(episode['score']),
                                       is_upgrade=True)
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = result[2] + ":hi"
                elif forced:
                    language_code = result[2] + ":forced"
                else:
                    language_code = result[2]
                provider = result[3]
                score = result[4]
                subs_id = result[6]
                subs_path = result[7]
                store_subtitles(episode['video_path'], path_mappings.path_replace(episode['video_path']))
                history_log(3, episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message, path,
                            language_code, provider, score, subs_id, subs_path)
                send_notifications(episode['sonarrSeriesId'], episode['sonarrEpisodeId'], message)

        show_progress(id='upgrade_episodes_progress',
                      header='Upgrading episodes subtitles...',
                      name='Completed successfully',
                      value=count_episode_to_upgrade,
                      count=count_episode_to_upgrade)

        hide_progress(id='upgrade_episodes_progress')

    if settings.general.getboolean('use_radarr'):
        for i, movie in enumerate(movies_to_upgrade, 1):
            show_progress(id='upgrade_movies_progress',
                          header='Upgrading movies subtitles...',
                          name=movie['title'],
                          value=i,
                          count=count_movie_to_upgrade)

            providers = get_providers()
            if not providers:
                logging.info("BAZARR All providers are throttled")
                return
            if not providers:
                logging.info("BAZARR All providers are throttled")
                return
            if movie['language'].endswith('forced'):
                language = movie['language'].split(':')[0]
                is_forced = "True"
                is_hi = "False"
            elif movie['language'].endswith('hi'):
                language = movie['language'].split(':')[0]
                is_forced = "False"
                is_hi = "True"
            else:
                language = movie['language'].split(':')[0]
                is_forced = "False"
                is_hi = "False"

            audio_language_list = get_audio_profile_languages(movie_id=movie['radarrId'])
            if len(audio_language_list) > 0:
                audio_language = audio_language_list[0]['name']
            else:
                audio_language = 'None'

            result = download_subtitle(path_mappings.path_replace_movie(movie['video_path']),
                                       language,
                                       audio_language,
                                       is_hi,
                                       is_forced,
                                       providers_list,
                                       providers_auth,
                                       str(movie['sceneName']),
                                       movie['title'],
                                       'movie',
                                       forced_minimum_score=int(movie['score']),
                                       is_upgrade=True)
            if result is not None:
                message = result[0]
                path = result[1]
                forced = result[5]
                if result[8]:
                    language_code = result[2] + ":hi"
                elif forced:
                    language_code = result[2] + ":forced"
                else:
                    language_code = result[2]
                provider = result[3]
                score = result[4]
                subs_id = result[6]
                subs_path = result[7]
                store_subtitles_movie(movie['video_path'],
                                      path_mappings.path_replace_movie(movie['video_path']))
                history_log_movie(3, movie['radarrId'], message, path, language_code, provider, score, subs_id, subs_path)
                send_notifications_movie(movie['radarrId'], message)

        show_progress(id='upgrade_movies_progress',
                      header='Upgrading movies subtitles...',
                      name='Completed successfully',
                      value=count_movie_to_upgrade,
                      count=count_movie_to_upgrade)

        hide_progress(id='upgrade_movies_progress')

    logging.info('BAZARR Finished searching for Subtitles to upgrade. Check History for more information.')


def postprocessing(command, path):
    try:
        encoding = getpreferredencoding()
        if os.name == 'nt':
            codepage = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, encoding=getpreferredencoding())
            # wait for the process to terminate
            out_codepage, err_codepage = codepage.communicate()
            encoding = out_codepage.split(':')[-1].strip()

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, encoding=encoding)
        # wait for the process to terminate
        out, err = process.communicate()

        out = out.replace('\n', ' ').replace('\r', ' ')

    except Exception as e:
        logging.error('BAZARR Post-processing failed for file ' + path + ' : ' + repr(e))
    else:
        if out == "":
            logging.info(
                'BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
        elif err:
            logging.error(
                'BAZARR Post-processing result for file ' + path + ' : ' + err.replace('\n', ' ').replace('\r', ' '))
        else:
            logging.info('BAZARR Post-processing result for file ' + path + ' : ' + out)


def sync_subtitles(video_path, srt_path, srt_lang, media_type, percent_score, sonarr_series_id=None,
                   sonarr_episode_id=None, radarr_id=None):
    if settings.subsync.getboolean('use_subsync'):
        if media_type == 'series':
            use_subsync_threshold = settings.subsync.getboolean('use_subsync_threshold')
            subsync_threshold = settings.subsync.subsync_threshold
        else:
            use_subsync_threshold = settings.subsync.getboolean('use_subsync_movie_threshold')
            subsync_threshold = settings.subsync.subsync_movie_threshold

        if not use_subsync_threshold or (use_subsync_threshold and percent_score < float(subsync_threshold)):
            subsync.sync(video_path=video_path, srt_path=srt_path, srt_lang=srt_lang, media_type=media_type,
                         sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id, radarr_id=radarr_id)
            return True
        else:
            logging.debug("BAZARR subsync skipped because subtitles score isn't below this "
                          "threshold value: " + subsync_threshold + "%")
    return False


def _get_download_code3(subtitle):
    custom = CustomLanguage.from_value(subtitle.language, "language")
    if custom is None:
        return subtitle.language.alpha3
    return custom.alpha3


def _get_lang_obj(alpha3):
    sub = CustomLanguage.from_value(alpha3, "alpha3")
    if sub is None:
        return Language(alpha3)

    return sub.subzero_language()
