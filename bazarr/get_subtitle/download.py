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

from config import settings, get_array_from
from helper import path_mappings, pp_replace, get_target_folder, force_unicode
from get_languages import alpha3_from_alpha2, alpha2_from_alpha3, alpha2_from_language, alpha3_from_language, \
    language_from_alpha3
from database import TableEpisodes, TableMovies
from analytics import track_event
from score import movie_score, series_score
from utils import notify_sonarr, notify_radarr
from event_handler import event_stream
from .pool import update_pools, _get_pool
from .utils import get_video, _get_lang_obj, _get_scores, _get_download_code3
from .sync import sync_subtitles
from .post_processing import postprocessing


@update_pools
def generate_subtitles(path, languages, audio_language, sceneName, title, media_type,
                       forced_minimum_score=None, is_upgrade=False, profile_id=None):
    if not languages:
        return None

    if settings.general.getboolean('utf8_encode'):
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"

    language_set = set()

    if not isinstance(languages, (set, list)):
        languages = [languages]

    pool = _get_pool(media_type, profile_id)
    providers = pool.providers

    for language in languages:
        lang, hi_item, forced_item = language
        logging.debug('BAZARR Searching subtitles for this file: ' + path)
        if hi_item == "True":
            hi = "force HI"
        else:
            hi = "force non-HI"

        # Fixme: This block should be updated elsewhere
        if forced_item == "True":
            pool.provider_configs['podnapisi']['only_foreign'] = True
            pool.provider_configs['subscene']['only_foreign'] = True
            pool.provider_configs['opensubtitles']['only_foreign'] = True
        else:
            pool.provider_configs['podnapisi']['only_foreign'] = False
            pool.provider_configs['subscene']['only_foreign'] = False
            pool.provider_configs['opensubtitles']['only_foreign'] = False

        # Always use alpha2 in API Request
        lang = alpha3_from_alpha2(lang)

        lang_obj = _get_lang_obj(lang)

        if forced_item == "True":
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
        handler = series_score if media_type == "series" else movie_score
        min_score, max_score, scores = _get_scores(media_type, minimum_score_movie, minimum_score)

        if providers:
            if forced_minimum_score:
                min_score = int(forced_minimum_score) + 1
            downloaded_subtitles = download_best_subtitles({video}, language_set, pool,
                                                           int(min_score), hi,
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
                                           percent_score=percent_score,
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
                                           percent_score=percent_score,
                                           radarr_id=movie_metadata['radarrId'])

                        if use_postprocessing is True:
                            command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                 downloaded_language_code2, downloaded_language_code3, audio_language,
                                                 audio_language_code2, audio_language_code3, subtitle.language.forced,
                                                 percent_score, subtitle_id, downloaded_provider, series_id, episode_id,
                                                 subtitle.language.hi)

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
                            event_stream(type='series', action='update', payload=episode_metadata['sonarrSeriesId'])
                            event_stream(type='episode-wanted', action='delete',
                                         payload=episode_metadata['sonarrEpisodeId'])

                        else:
                            reversed_path = path_mappings.path_replace_reverse_movie(path)
                            reversed_subtitles_path = path_mappings.path_replace_reverse_movie(downloaded_path)
                            notify_radarr(movie_metadata['radarrId'])
                            event_stream(type='movie-wanted', action='delete', payload=movie_metadata['radarrId'])

                        track_event(category=downloaded_provider, action=action, label=downloaded_language)

                        yield message, reversed_path, downloaded_language_code2, downloaded_provider, subtitle.score, \
                            subtitle.language.forced, subtitle.id, reversed_subtitles_path, subtitle.language.hi

        if not saved_any:
            logging.debug('BAZARR No Subtitles were found for this file: ' + path)
            return None

    subliminal.region.backend.sync()

    logging.debug('BAZARR Ended searching Subtitles for file: ' + path)
