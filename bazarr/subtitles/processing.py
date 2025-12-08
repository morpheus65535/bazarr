# coding=utf-8
# fmt: off

import logging

from app.config import settings, sync_checker as _defaul_sync_checker
from utilities.path_mappings import path_mappings
from utilities.post_processing import pp_replace, set_chmod
from utilities.autopulse_webhook import call_external_webhook
from languages.get_languages import alpha2_from_alpha3, alpha2_from_language, alpha3_from_language, language_from_alpha3
from app.database import TableShows, TableEpisodes, TableMovies, database, select
from utilities.analytics import event_tracker
from radarr.notify import notify_radarr
from sonarr.notify import notify_sonarr
from plex.operations import plex_set_movie_added_date_now, plex_update_library, plex_set_episode_added_date_now, plex_refresh_item
from app.event_handler import event_stream

from .utils import _get_download_code3
from .post_processing import postprocessing
from .utils import _get_scores


class ProcessSubtitlesResult:
    def __init__(self, message, reversed_path, downloaded_language_code2, downloaded_provider, score, forced,
                 subtitle_id, reversed_subtitles_path, hearing_impaired, matched=None, not_matched=None):
        self.message = message
        self.path = reversed_path
        self.provider = downloaded_provider
        self.score = score
        self.subs_id = subtitle_id
        self.subs_path = reversed_subtitles_path
        self.matched = matched
        self.not_matched = not_matched

        if hearing_impaired:
            self.language_code = f"{downloaded_language_code2}:hi"
        elif forced:
            self.language_code = f"{downloaded_language_code2}:forced"
        else:
            self.language_code = downloaded_language_code2


def process_subtitle(subtitle, media_type, audio_language, path, max_score, is_upgrade=False, is_manual=False,
                     job_id=None):
    use_postprocessing = settings.general.use_postprocessing
    postprocessing_cmd = settings.general.postprocessing_cmd

    downloaded_provider = subtitle.provider_name
    uploader = subtitle.uploader
    release_info = subtitle.release_info
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
    logging.debug(f'BAZARR Subtitles file saved to disk: {downloaded_path}')
    if is_upgrade:
        action = "upgraded"
    elif is_manual:
        action = "manually downloaded"
    else:
        action = "downloaded"

    percent_score = round(subtitle.score * 100 / max_score, 2)
    message = (f"{downloaded_language}{modifier_string} subtitles {action} from {downloaded_provider} with a score of "
               f"{percent_score}%.")

    sync_checker = _defaul_sync_checker
    logging.debug("Sync checker: %s", sync_checker)

    if media_type == 'series':
        episode_metadata = database.execute(
            select(TableShows.imdbId, TableEpisodes.sonarrSeriesId, TableEpisodes.sonarrEpisodeId,
                   TableEpisodes.season, TableEpisodes.episode)
                .join(TableShows)\
                .where(TableEpisodes.path == path_mappings.path_replace_reverse(path)))\
            .first()
        if not episode_metadata:
            return
        series_id = episode_metadata.sonarrSeriesId
        episode_id = episode_metadata.sonarrEpisodeId

        if sync_checker(subtitle) is True:
            from .sync import sync_subtitles
            sync_subtitles(video_path=path, srt_path=downloaded_path,
                           forced=subtitle.language.forced,
                           hi=subtitle.language.hi,
                           srt_lang=downloaded_language_code2,
                           percent_score=percent_score,
                           sonarr_series_id=episode_metadata.sonarrSeriesId,
                           sonarr_episode_id=episode_metadata.sonarrEpisodeId,
                           job_id=job_id,
                           job_sub_function=True)
    else:
        movie_metadata = database.execute(
            select(TableMovies.radarrId, TableMovies.imdbId)
                .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path)))\
            .first()
        if not movie_metadata:
            return
        series_id = ""
        episode_id = movie_metadata.radarrId

        if sync_checker(subtitle) is True:
            from .sync import sync_subtitles
            sync_subtitles(video_path=path, srt_path=downloaded_path,
                           forced=subtitle.language.forced,
                           hi=subtitle.language.hi,
                           srt_lang=downloaded_language_code2,
                           percent_score=percent_score,
                           radarr_id=movie_metadata.radarrId,
                           job_id=job_id,
                           job_sub_function=True)

    if use_postprocessing is True:
        command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language, downloaded_language_code2,
                             downloaded_language_code3, audio_language, audio_language_code2, audio_language_code3,
                             percent_score, subtitle_id, downloaded_provider, uploader, release_info, series_id,
                             episode_id)

        if media_type == 'series':
            use_pp_threshold = settings.general.use_postprocessing_threshold
            pp_threshold = int(settings.general.postprocessing_threshold)
        else:
            use_pp_threshold = settings.general.use_postprocessing_threshold_movie
            pp_threshold = int(settings.general.postprocessing_threshold_movie)

        if not use_pp_threshold or (use_pp_threshold and percent_score < pp_threshold):
            logging.debug(f"BAZARR Using post-processing command: {command}")
            postprocessing(command, path)
            set_chmod(subtitles_path=downloaded_path)
        else:
            logging.debug(f"BAZARR post-processing skipped because subtitles score isn't below this "
                          f"threshold value: {pp_threshold}%")

    if media_type == 'series':
        reversed_path = path_mappings.path_replace_reverse(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse(downloaded_path)
        notify_sonarr(episode_metadata.sonarrSeriesId)
        event_stream(type='series', action='update', payload=episode_metadata.sonarrSeriesId)
        event_stream(type='episode-wanted', action='delete',
                     payload=episode_metadata.sonarrEpisodeId)
        if settings.general.use_plex is True:
            if settings.plex.update_series_library is True:
                # Use specific item refresh instead of full library scan
                plex_refresh_item(episode_metadata.imdbId, is_movie=False, 
                                season=episode_metadata.season, episode=episode_metadata.episode)
            if settings.plex.set_episode_added is True:
                plex_set_episode_added_date_now(episode_metadata)

    else:
        reversed_path = path_mappings.path_replace_reverse_movie(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse_movie(downloaded_path)
        notify_radarr(movie_metadata.radarrId)
        event_stream(type='movie-wanted', action='delete', payload=movie_metadata.radarrId)
        if settings.general.use_plex is True:
            if settings.plex.set_movie_added is True:
                plex_set_movie_added_date_now(movie_metadata)
            if settings.plex.update_movie_library is True:
                # Use specific item refresh instead of full library scan
                plex_refresh_item(movie_metadata.imdbId, is_movie=True)

    # Call external webhook after all processing is complete if enabled
    call_external_webhook(
        subtitle_path=downloaded_path,
        media_path=path,
        language=downloaded_language,
        media_type=media_type
    )

    event_tracker.track_subtitles(provider=downloaded_provider, action=action, language=downloaded_language)

    return ProcessSubtitlesResult(message=message,
                                  reversed_path=reversed_path,
                                  downloaded_language_code2=downloaded_language_code2,
                                  downloaded_provider=downloaded_provider,
                                  score=subtitle.score,
                                  forced=subtitle.language.forced,
                                  subtitle_id=subtitle.id,
                                  reversed_subtitles_path=reversed_subtitles_path,
                                  hearing_impaired=subtitle.language.hi,
                                  matched=list(subtitle.matches or []),
                                  not_matched=_get_not_matched(subtitle, media_type)),


def _get_not_matched(subtitle, media_type):
    _, _, scores = _get_scores(media_type)

    if subtitle.matches and isinstance(subtitle.matches, set) and 'hash' not in subtitle.matches:
        return list(set(scores) - set(subtitle.matches))
    else:
        return []
