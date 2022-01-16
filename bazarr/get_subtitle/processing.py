# coding=utf-8
# fmt: off

import logging

from config import settings
from helper import path_mappings, pp_replace
from get_languages import alpha2_from_alpha3, alpha2_from_language, alpha3_from_language, language_from_alpha3
from database import TableEpisodes, TableMovies
from analytics import track_event
from utils import notify_sonarr, notify_radarr
from event_handler import event_stream
from .utils import _get_download_code3
from .sync import sync_subtitles
from .post_processing import postprocessing


def process_subtitle(subtitle, media_type, audio_language, path, max_score, is_upgrade=False, is_manual=False):
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd

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
    elif is_manual:
        action = "manually downloaded"
    else:
        action = "downloaded"

    percent_score = round(subtitle.score * 100 / max_score, 2)
    message = downloaded_language + modifier_string + " subtitles " + action + " from " + \
        downloaded_provider + " with a score of " + str(percent_score) + "%."

    if media_type == 'series':
        episode_metadata = TableEpisodes.select(TableEpisodes.sonarrSeriesId,
                                                TableEpisodes.sonarrEpisodeId) \
            .where(TableEpisodes.path == path_mappings.path_replace_reverse(path)) \
            .dicts() \
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
        movie_metadata = TableMovies.select(TableMovies.radarrId) \
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path)) \
            .dicts() \
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

    return message, reversed_path, downloaded_language_code2, downloaded_provider, subtitle.score, \
        subtitle.language.forced, subtitle.id, reversed_subtitles_path, subtitle.language.hi
