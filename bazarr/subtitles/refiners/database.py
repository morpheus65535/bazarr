# coding=utf-8
# fmt: off

import ast
import re

from subliminal import Episode, Movie

from utilities.path_mappings import path_mappings
from app.database import TableShows, TableEpisodes, TableMovies, database, select

from .utils import convert_to_guessit


_TITLE_RE = re.compile(r'\s(\(\d{4}\))')


def refine_from_db(path, video):
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

            video.series_tvdb_id = int(data.tvdbId)
            video.alternative_series = ast.literal_eval(data.alternativeTitles)
            if data.imdbId and not video.series_imdb_id:
                video.series_imdb_id = data.imdbId
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
