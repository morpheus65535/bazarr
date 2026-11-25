# coding=utf-8
# fmt: off

import ast
import re

from subliminal import Episode, Movie

from utilities.path_mappings import path_mappings
from app.database import TableShows, TableEpisodes, TableMovies, TableSportsEvents, TableSportsLeagues, database, \
    select

from .utils import convert_to_guessit


_TITLE_RE = re.compile(r'\s(\(\d{4}\))')


def refine_from_db(path, video):
    """Refine a guessed video with the series or movie metadata stored in the database.

    :param str path: path of the video file as known to Bazarr.
    :param video: video to refine, either an ``Episode`` or a ``Movie``.
    :return: the refined video.
    """
    if isinstance(video, Episode):
        data = database.execute(
            select(TableShows.title.label('seriesTitle'),
                   TableEpisodes.season,
                   TableEpisodes.episode,
                   TableEpisodes.title.label('episodeTitle'),
                   TableShows.year,
                   TableShows.tvdbId,
                   TableShows.alternativeTitles,
                   TableEpisodes.format,
                   TableEpisodes.resolution,
                   TableEpisodes.video_codec,
                   TableEpisodes.audio_codec,
                   TableEpisodes.path,
                   TableShows.imdbId,
                   TableShows.tmdbId,
                   TableEpisodes.sonarrSeriesId,
                   TableEpisodes.sonarrEpisodeId,
                   TableEpisodes.absoluteEpisode)
            .select_from(TableEpisodes)
            .join(TableShows)
            .where((TableEpisodes.path == path_mappings.path_replace_reverse(path)))) \
            .first()

        if data:
            video.series = _TITLE_RE.sub('', data.seriesTitle)
            video.season = int(data.season)
            video.episode = int(data.episode)
            video.absolute_episode = int(data.absoluteEpisode) if data.absoluteEpisode else None
            video.title = data.episodeTitle

            # Only refine year as a fallback
            if not video.year and data.year:
                if int(data.year) > 0:
                    video.year = int(data.year)

            # A library entry can legitimately have no TVDB mapping.  Keep
            # the guessed/refined value in that case instead of aborting all
            # video metadata processing for the file.
            if data.tvdbId:
                video.series_tvdb_id = int(data.tvdbId)
            video.alternative_series = ast.literal_eval(data.alternativeTitles)
            if data.imdbId and not video.series_imdb_id:
                video.series_imdb_id = data.imdbId
            if data.tmdbId and not video.series_tmdb_id:
                video.series_tmdb_id = data.tmdbId
            if not video.source:
                video.source = convert_to_guessit('source', str(data.format))
            if not video.resolution:
                video.resolution = str(data.resolution)
            if not video.video_codec:
                if data.video_codec:
                    video.video_codec = convert_to_guessit('video_codec', data.video_codec)
            if not video.audio_codec:
                if data.audio_codec:
                    video.audio_codec = convert_to_guessit('audio_codec', data.audio_codec)

            video.sonarrSeriesId = data.sonarrSeriesId
            video.sonarrEpisodeId = data.sonarrEpisodeId
        else:
            _refine_from_sports_event(path, video)
    elif isinstance(video, Movie):
        data = database.execute(
            select(TableMovies.title,
                   TableMovies.year,
                   TableMovies.alternativeTitles,
                   TableMovies.format,
                   TableMovies.resolution,
                   TableMovies.video_codec,
                   TableMovies.audio_codec,
                   TableMovies.imdbId,
                   TableMovies.tmdbId,
                   TableMovies.radarrId)
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path))) \
            .first()

        if data:
            video.title = _TITLE_RE.sub('', data.title)

            # Only refine year as a fallback
            if not video.year and data.year:
                if int(data.year) > 0:
                    video.year = int(data.year)

            if data.imdbId and not video.imdb_id:
                video.imdb_id = data.imdbId
            if data.tmdbId and not video.tmdb_id:
                video.tmdb_id = data.tmdbId
 
            video.alternative_titles = ast.literal_eval(data.alternativeTitles)
            if not video.source:
                if data.format:
                    video.source = convert_to_guessit('source', data.format)
            if not video.resolution:
                if data.resolution:
                    video.resolution = data.resolution
            if not video.video_codec:
                if data.video_codec:
                    video.video_codec = convert_to_guessit('video_codec', data.video_codec)
            if not video.audio_codec:
                if data.audio_codec:
                    video.audio_codec = convert_to_guessit('audio_codec', data.audio_codec)

            video.radarrId = data.radarrId

    return video


def _refine_from_sports_event(path, video):
    """Refine an episode with the sports event stored for this path, if there is one.

    A sports file is searched as an episode. Without this, the series, season and episode come from guessit, which
    reads them from the folder names and gets them wrong.

    :param str path: path of the video file as known to Bazarr.
    :param video: the ``Episode`` to refine in place.
    """
    data = database.execute(
        select(TableSportsLeagues.title.label('leagueTitle'),
               TableSportsEvents.title.label('eventTitle'),
               TableSportsEvents.season,
               TableSportsEvents.episode,
               TableSportsEvents.format,
               TableSportsEvents.resolution,
               TableSportsEvents.video_codec,
               TableSportsEvents.audio_codec,
               TableSportsEvents.sportarrLeagueId,
               TableSportsEvents.id)
        .select_from(TableSportsEvents)
        .join(TableSportsLeagues)
        .where(TableSportsEvents.path == path_mappings.path_replace_reverse_sports(path))) \
        .first()

    if not data:
        return

    video.series = data.leagueTitle
    video.season = int(data.season)
    video.episode = int(data.episode)
    video.title = data.eventTitle
    # A league has no alternative titles and no tvdb, imdb or tmdb id.
    video.alternative_series = []
    if not video.source and data.format:
        video.source = convert_to_guessit('source', str(data.format))
    if not video.resolution and data.resolution:
        video.resolution = str(data.resolution)
    if not video.video_codec and data.video_codec:
        video.video_codec = convert_to_guessit('video_codec', data.video_codec)
    if not video.audio_codec and data.audio_codec:
        video.audio_codec = convert_to_guessit('audio_codec', data.audio_codec)

    video.sportarrLeagueId = data.sportarrLeagueId
    video.sportsEventId = data.id
