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

from get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2, alpha2_from_language, \
    alpha3_from_language
from config import settings, get_array_from
from helper import path_mappings, pp_replace, get_target_folder, force_unicode
from utils import notify_sonarr, notify_radarr
from database import get_profiles_list, TableEpisodes, TableMovies
from analytics import track_event
from score import movie_score, series_score
from .pool import update_pools, _get_pool, _init_pool
from .utils import get_video, _get_lang_obj, _get_scores, _get_download_code3
from .sync import sync_subtitles
from .post_processing import postprocessing


@update_pools
def manual_search(path, profile_id, providers, providers_auth, sceneName, title, media_type):
    logging.debug('BAZARR Manually searching subtitles for this file: ' + path)

    final_subtitles = []

    initial_language_set = set()
    language_set = set()

    # where [3] is items list of dict(id, lang, forced, hi)
    language_items = get_profiles_list(profile_id=int(profile_id))['items']
    pool = _get_pool(media_type, profile_id)

    for language in language_items:
        forced = language['forced']
        hi = language['hi']
        language = language['language']

        lang = alpha3_from_alpha2(language)

        lang_obj = _get_lang_obj(lang)

        if forced == "True":
            lang_obj = Language.rebuild(lang_obj, forced=True)

            pool.provider_configs['podnapisi']['also_foreign'] = True
            pool.provider_configs['opensubtitles']['also_foreign'] = True

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
    if providers:
        video = get_video(force_unicode(path), title, sceneName, providers=providers,
                          media_type=media_type)
    else:
        logging.info("BAZARR All providers are throttled")
        return None
    if video:
        handler = series_score if media_type == "series" else movie_score
        min_score, max_score, scores = _get_scores(media_type, minimum_score_movie, minimum_score)

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

                score, score_without_hash = compute_score(matches, s, video, hearing_impaired=initial_hi, score_obj=handler)
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
def manual_download_subtitle(path, language, audio_language, hi, forced, subtitle, provider, providers_auth, sceneName,
                             title, media_type, profile_id):
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
        min_score, max_score, scores = _get_scores(media_type)
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

            except Exception:
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
                            episode_metadata = TableEpisodes.select(TableEpisodes.sonarrSeriesId,
                                                                    TableEpisodes.sonarrEpisodeId)\
                                .where(TableEpisodes.path == path_mappings.path_replace_reverse(path))\
                                .dicts()\
                                .get()
                            series_id = episode_metadata['sonarrSeriesId']
                            episode_id = episode_metadata['sonarrEpisodeId']
                            sync_subtitles(video_path=path, srt_path=downloaded_path,
                                           forced=subtitle.language.forced,
                                           srt_lang=downloaded_language_code2, media_type=media_type,
                                           percent_score=score,
                                           sonarr_series_id=episode_metadata['sonarrSeriesId'],
                                           sonarr_episode_id=episode_metadata['sonarrEpisodeId'])
                        else:
                            movie_metadata = TableMovies.select(TableMovies.radarrId)\
                                .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path))\
                                .dicts()\
                                .get()
                            series_id = ""
                            episode_id = movie_metadata['radarrId']
                            sync_subtitles(video_path=path, srt_path=downloaded_path,
                                           forced=subtitle.language.forced,
                                           srt_lang=downloaded_language_code2, media_type=media_type,
                                           percent_score=score, radarr_id=movie_metadata['radarrId'])

                        if use_postprocessing:
                            percent_score = round(subtitle.score * 100 / max_score, 2)
                            command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                 downloaded_language_code2, downloaded_language_code3, audio_language,
                                                 audio_language_code2, audio_language_code3, subtitle.language.forced,
                                                 percent_score, subtitle_id, downloaded_provider, series_id, episode_id,
                                                 subtitle.language.hi)

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
                        "BAZARR Tried to manually download a Subtitles for file: " + path
                        + " but we weren't able to do (probably throttled by " + str(subtitle.provider_name)
                        + ". Please retry later or select a Subtitles from another provider.")
                    return None

    subliminal.region.backend.sync()

    logging.debug('BAZARR Ended manually downloading Subtitles for file: ' + path)
