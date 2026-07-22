# coding=utf-8

import logging
import os
import subprocess

from fese import container, FFprobeVideoContainer
from subzero.language import Language
from subliminal_patch.core import get_subtitle_path
from subliminal_patch.score import MAX_SCORES

from app.config import settings
from app.database import (TableShows, TableEpisodes, TableEpisodesSubtitles, TableMovies, TableMoviesSubtitles,
                          database, select)
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from app.notifier import send_notifications, send_notifications_movie
from jellyfin.operations import jellyfin_refresh_item
from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2
from plex.operations import plex_refresh_item
from radarr.history import history_log_movie
from radarr.notify import notify_radarr
from sonarr.history import history_log
from sonarr.notify import notify_sonarr
from subtitles.indexer.movies import store_subtitles_movie
from subtitles.indexer.series import store_subtitles
from subtitles.processing import ProcessSubtitlesResult
from utilities.autopulse_webhook import call_external_webhook
from utilities.binaries import get_binary
from utilities.helper import get_target_folder
from utilities.path_mappings import path_mappings
from utilities.post_processing import set_chmod


class EmbeddedSubtitlesExtractionError(Exception):
    """Base exception raised when an embedded subtitles track cannot be extracted."""


class SubtitlesNotFoundError(EmbeddedSubtitlesExtractionError):
    """Raised when no subtitles record matches the provided id and media type."""


class NotAnEmbeddedSubtitlesError(EmbeddedSubtitlesExtractionError):
    """Raised when the subtitles record is an external file rather than an embedded track."""


class BitmapSubtitlesNotSupportedError(EmbeddedSubtitlesExtractionError):
    """Raised when the embedded track is image/bitmap based and cannot be extracted to text."""


# ffmpeg subtitles codec name -> external file extension. Only text-based codecs that ffmpeg
# can copy without conversion are listed, so the original subtitles format is preserved.
_CODEC_TO_EXTENSION = {
    "ass": "ass",
    "subrip": "srt",
    "webvtt": "vtt",
}


def _language_from_alpha2(code2):
    """Build a subzero Language from a stored alpha2 code (e.g. 'en', 'pt-BR')."""
    alpha3 = alpha3_from_alpha2(code2)
    custom = CustomLanguage.from_value(alpha3, "alpha3")
    if custom is None:
        return Language(alpha3)
    return custom.subzero_language()


def extract_embedded_subtitle(subtitles_id, media_type, job_id=None):
    """Extract an embedded subtitles track to an external subtitles file.

    Look up the subtitles record identified by ``subtitles_id`` (the primary key of the row in
    the episodes/movies subtitles table), locate its embedded track in the media file and extract
    it with ffmpeg -- preserving the original format and extension -- saving it following the
    user's subtitles location settings, then reindex it.

    :param subtitles_id: primary key of the subtitles record to extract
    :param media_type: "episode" or "movie"
    :param job_id: the job id of the job that is extracting the subtitles
    :returns: the path of the extracted subtitles file
    :raises SubtitlesNotFoundError: no matching subtitles record was found
    :raises NotAnEmbeddedSubtitlesError: the record points to an external subtitles file
    :raises BitmapSubtitlesNotSupportedError: the track is image/bitmap based
    :raises EmbeddedSubtitlesExtractionError: any other extraction failure
    :raises OSError: the media file is missing or ffmpeg cannot write the output file
    """
    if not job_id:
        jobs_queue.add_job_from_function("Extracting embedded subtitles", is_progress=False)
        return False

    # Look up the subtitles record together with its media file path
    if media_type == 'episode':
        data = database.execute(
            select(TableEpisodesSubtitles.embedded_track_id,
                   TableEpisodesSubtitles.language,
                   TableEpisodesSubtitles.forced,
                   TableEpisodesSubtitles.hi,
                   TableEpisodesSubtitles.sonarrEpisodeId,
                   TableEpisodesSubtitles.sonarrSeriesId,
                   TableEpisodes.path,
                   TableShows.title.label('seriesTitle'),
                   TableShows.year,
                   TableShows.imdbId,
                   TableShows.tvdbId,
                   TableEpisodes.season,
                   TableEpisodes.episode,
                   TableEpisodes.title,
                   TableEpisodes.audio_language,)
            .join(TableEpisodes, TableEpisodes.sonarrEpisodeId == TableEpisodesSubtitles.sonarrEpisodeId)
            .join(TableShows, TableShows.sonarrSeriesId == TableEpisodes.sonarrSeriesId)
            .where(TableEpisodesSubtitles.id == subtitles_id)) \
            .first()
    else:
        data = database.execute(
            select(TableMoviesSubtitles.embedded_track_id,
                   TableMoviesSubtitles.language,
                   TableMoviesSubtitles.forced,
                   TableMoviesSubtitles.hi,
                   TableMoviesSubtitles.radarrId,
                   TableMovies.path,
                   TableMovies.title,
                   TableMovies.year,
                   TableMovies.imdbId,
                   TableMovies.tmdbId,
                   TableMovies.audio_language,)
            .join(TableMovies, TableMovies.radarrId == TableMoviesSubtitles.radarrId)
            .where(TableMoviesSubtitles.id == subtitles_id)) \
            .first()

    if not data:
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract a non-existing subtitles record "
                                                               f"{subtitles_id}")
        raise SubtitlesNotFoundError(f"No {media_type} subtitles record found with id {subtitles_id}")
    else:
        if media_type == 'episode':
            media_title = f'{data.seriesTitle} - S{data.season:02d}E{data.episode:02d} - {data.title}'
        else:
            media_title = f'{data.title} ({data.year})'

        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Extracting embedded subtitles for {media_title}")

    if data.embedded_track_id is None:
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract a non-embedded subtitles track "
                                                               f"{subtitles_id}")
        raise NotAnEmbeddedSubtitlesError(f"Subtitles record {subtitles_id} is not an embedded track")

    # Resolve the local media file path
    if media_type == 'episode':
        video_path = path_mappings.path_replace(data.path)
        media_id = data.sonarrEpisodeId
    else:
        video_path = path_mappings.path_replace_movie(data.path)
        media_id = data.radarrId

    if not os.path.isfile(video_path):
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract embedded subtitles for video file "
                                                               f"{video_path}")
        raise OSError(f"Media file not found: {video_path}")

    # Read the subtitles streams from the media file and find the requested track
    container.FFPROBE_PATH = get_binary("ffprobe")
    container.FFMPEG_PATH = get_binary("ffmpeg")

    streams = FFprobeVideoContainer(video_path).get_subtitles()
    stream = next((s for s in streams if s.index == data.embedded_track_id), None)
    if stream is None:
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract an unknown embedded subtitles track "
                                                               f"in {video_path}")
        raise EmbeddedSubtitlesExtractionError(
            f"Embedded track {data.embedded_track_id} not found in {video_path}")

    # Only text-based subtitles can be extracted; reject image/bitmap based tracks
    extension = _CODEC_TO_EXTENSION.get(stream.codec_name)
    if extension is None:
        if stream.type != "text":
            jobs_queue.update_job_name(job_id=job_id,
                                       new_job_name=f"Failed to extract an image-based embedded subtitles track "
                                                    f"{stream.codec_name} in {video_path}")
            raise BitmapSubtitlesNotSupportedError(
                f"Image based ({stream.codec_name}) embedded subtitles cannot be extracted")
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract an unsupported embedded subtitles "
                                                               f"codec {stream.codec_name}")
        raise EmbeddedSubtitlesExtractionError(f"Unsupported embedded subtitles codec: {stream.codec_name}")

    # Build the destination path following the user's subtitles location settings
    language = _language_from_alpha2(data.language)
    subtitles_path = get_subtitle_path(video_path,
                                       language=language,
                                       extension=f".{extension}",
                                       forced_tag=data.forced,
                                       hi_tag=data.hi)
    target_folder = get_target_folder(video_path)
    if target_folder:
        subtitles_path = os.path.join(target_folder, os.path.basename(subtitles_path))

    # Extract the track with ffmpeg, copying the stream to preserve its original format
    command = [container.FFMPEG_PATH, "-y", "-v", "error", "-i", video_path] + stream.copy_args(subtitles_path)
    logging.debug(f"BAZARR extracting embedded subtitles track {stream.index} ({stream.codec_name}) "
                  f"to {subtitles_path}")
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode(errors='ignore').strip() if error.stderr else ''
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract embedded subtitles "
                                                               f"{stderr or error}")
        raise EmbeddedSubtitlesExtractionError(f"ffmpeg failed to extract embedded subtitles: {stderr or error}") \
            from error

    if not os.path.isfile(subtitles_path):
        jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Failed to extract embedded subtitles since file is "
                                                               f"missing: {subtitles_path}")
        raise EmbeddedSubtitlesExtractionError(f"Extracted subtitles file is missing: {subtitles_path}")

    # Set permissions, reindex the newly created external subtitles and notify the UI
    set_chmod(subtitles_path)

    if media_type == 'episode':
        store_subtitles(media_id)
    else:
        store_subtitles_movie(media_id)
    event_stream(type=media_type, payload=media_id)

    # Log the extraction to the history database (action 7 == extracted)
    modifier = " HI" if data.hi else " forced" if data.forced else ""
    if media_type == 'episode':
        reversed_video_path = path_mappings.path_replace_reverse(video_path)
        reversed_subtitles_path = path_mappings.path_replace_reverse(subtitles_path)
    else:
        reversed_video_path = path_mappings.path_replace_reverse_movie(video_path)
        reversed_subtitles_path = path_mappings.path_replace_reverse_movie(subtitles_path)

    result = ProcessSubtitlesResult(
        message=f"{language_from_alpha2(data.language)}{modifier} subtitles extracted from embedded track "
                f"{data.embedded_track_id}.",
        reversed_path=reversed_video_path,
        downloaded_language_code2=data.language,
        downloaded_provider=None,
        score=None,
        forced=data.forced,
        subtitle_id=f"{video_path}_{stream.index}",
        reversed_subtitles_path=reversed_subtitles_path,
        hearing_impaired=data.hi)

    if media_type == 'episode':
        history_log(7, data.sonarrSeriesId, media_id, result, fake_score=MAX_SCORES['episode'])
        event_stream(type="episode-history")
    else:
        history_log_movie(7, media_id, result, fake_score=MAX_SCORES['movie'])
        event_stream(type="movie-history")

    # Notify apprise
    if media_type == 'episode':
        send_notifications(data.sonarrSeriesId, media_id, result.message)
    else:
        send_notifications_movie(media_id, result.message)

    # Notify media downloader so they update their library so the newly extracted subtitles are picked up
    if media_type == 'episode':
        notify_sonarr(data.sonarrSeriesId)
    else:
        notify_radarr(media_id)

    # Refresh the media servers so the newly extracted subtitles are picked up
    if media_type == 'episode':
        if settings.general.use_plex and settings.plex.update_series_library:
            plex_refresh_item(data.imdbId, is_movie=False, season=data.season, episode=data.episode)
        if settings.general.use_jellyfin and settings.jellyfin.update_series_library:
            jellyfin_refresh_item(data.imdbId, is_movie=False, season=data.season, episode=data.episode,
                                  tvdb_id=data.tvdbId)
    else:
        if settings.general.use_plex and settings.plex.update_movie_library:
            plex_refresh_item(data.imdbId, is_movie=True)
        if settings.general.use_jellyfin and settings.jellyfin.update_movie_library:
            jellyfin_refresh_item(data.imdbId, is_movie=True, tmdb_id=data.tmdbId)

    # Call external webhook after all processing is complete if enabled
    call_external_webhook(
        subtitle_path=subtitles_path,
        media_path=video_path,
        language=language,
        media_type=media_type
    )

    logging.debug(f"BAZARR extracted embedded subtitles to {subtitles_path}")
    jobs_queue.update_job_name(job_id=job_id, new_job_name=f"Extracted {subtitles_path}")
    return subtitles_path
