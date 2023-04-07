# coding=utf-8
# fmt: off

import logging

from app.config import settings
from utilities.path_mappings import path_mappings
from utilities.post_processing import pp_replace, set_chmod
from languages.get_languages import alpha2_from_alpha3, alpha2_from_language, alpha3_from_language, language_from_alpha3
from app.database import TableEpisodes, TableMovies
from utilities.analytics import event_tracker
from radarr.notify import notify_radarr
from sonarr.notify import notify_sonarr
from app.event_handler import event_stream

from .utils import _get_download_code3
from .post_processing import postprocessing


class ProcessSubtitlesResult:
    def __init__(self, message, reversed_path, downloaded_language_code2, downloaded_provider, score, forced,
                 subtitle_id, reversed_subtitles_path, hearing_impaired):
        self.message = message
        self.path = reversed_path
        self.provider = downloaded_provider
        self.score = score
        self.subs_id = subtitle_id
        self.subs_path = reversed_subtitles_path

        if hearing_impaired:
            self.language_code = downloaded_language_code2 + ":hi"
        elif forced:
            self.language_code = downloaded_language_code2 + ":forced"
        else:
            self.language_code = downloaded_language_code2


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
            .get_or_none()
        if not episode_metadata:
            return
        series_id = episode_metadata['sonarrSeriesId']
        episode_id = episode_metadata['sonarrEpisodeId']

        from .sync import sync_subtitles
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
            .get_or_none()
        if not movie_metadata:
            return
        series_id = ""
        episode_id = movie_metadata['radarrId']

        from .sync import sync_subtitles
        sync_subtitles(video_path=path, srt_path=downloaded_path,
                       forced=subtitle.language.forced,
                       srt_lang=downloaded_language_code2, media_type=media_type,
                       percent_score=percent_score,
                       radarr_id=movie_metadata['radarrId'])

    if use_postprocessing is True:
        command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language, downloaded_language_code2,
                             downloaded_language_code3, audio_language, audio_language_code2, audio_language_code3,
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
            set_chmod(subtitles_path=downloaded_path)
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

    event_tracker.track(provider=downloaded_provider, action=action, language=downloaded_language)

    return ProcessSubtitlesResult(message=message,
                                  reversed_path=reversed_path,
                                  downloaded_language_code2=downloaded_language_code2,
                                  downloaded_provider=downloaded_provider,
                                  score=subtitle.score,
                                  forced=subtitle.language.forced,
                                  subtitle_id=subtitle.id,
                                  reversed_subtitles_path=reversed_subtitles_path,
                                  hearing_impaired=subtitle.language.hi)
