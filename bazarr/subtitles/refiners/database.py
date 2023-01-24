# coding=utf-8
# fmt: off

import ast
import re

from subliminal import Episode, Movie

from utilities.path_mappings import path_mappings
from app.database import TableShows, TableEpisodes, TableMovies

from .utils import convert_to_guessit


_TITLE_RE = re.compile(r'\s(\(\d{4}\))')


def refine_from_db(path, video):
    if isinstance(video, Episode):
        data = TableEpisodes.select(TableShows.title.alias('seriesTitle'),
                                    TableEpisodes.season,
                                    TableEpisodes.episode,
                                    TableEpisodes.title.alias('episodeTitle'),
                                    TableShows.year,
                                    TableShows.tvdbId,
                                    TableShows.alternateTitles,
                                    TableEpisodes.format,
                                    TableEpisodes.resolution,
                                    TableEpisodes.video_codec,
                                    TableEpisodes.audio_codec,
                                    TableEpisodes.path,
                                    TableShows.imdbId)\
            .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .where((TableEpisodes.path == path_mappings.path_replace_reverse(path)))\
            .dicts()

        if len(data):
            data = data[0]
            video.series = _TITLE_RE.sub('', data['seriesTitle'])
            video.season = int(data['season'])
            video.episode = int(data['episode'])
            video.title = data['episodeTitle']

            # Only refine year as a fallback
            if not video.year and data['year']:
                if int(data['year']) > 0:
                    video.year = int(data['year'])

            video.series_tvdb_id = int(data['tvdbId'])
            video.alternative_series = ast.literal_eval(data['alternateTitles'])
            if data['imdbId'] and not video.series_imdb_id:
                video.series_imdb_id = data['imdbId']
            if not video.source:
                video.source = convert_to_guessit('source', str(data['format']))
            if not video.resolution:
                video.resolution = str(data['resolution'])
            if not video.video_codec:
                if data['video_codec']:
                    video.video_codec = convert_to_guessit('video_codec', data['video_codec'])
            if not video.audio_codec:
                if data['audio_codec']:
                    video.audio_codec = convert_to_guessit('audio_codec', data['audio_codec'])
    elif isinstance(video, Movie):
        data = TableMovies.select(TableMovies.title,
                                  TableMovies.year,
                                  TableMovies.alternativeTitles,
                                  TableMovies.format,
                                  TableMovies.resolution,
                                  TableMovies.video_codec,
                                  TableMovies.audio_codec,
                                  TableMovies.imdbId)\
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path))\
            .dicts()

        if len(data):
            data = data[0]
            video.title = _TITLE_RE.sub('', data['title'])

            # Only refine year as a fallback
            if not video.year and data['year']:
                if int(data['year']) > 0:
                    video.year = int(data['year'])

            if data['imdbId'] and not video.imdb_id:
                video.imdb_id = data['imdbId']
            video.alternative_titles = ast.literal_eval(data['alternativeTitles'])
            if not video.source:
                if data['format']:
                    video.source = convert_to_guessit('source', data['format'])
            if not video.resolution:
                if data['resolution']:
                    video.resolution = data['resolution']
            if not video.video_codec:
                if data['video_codec']:
                    video.video_codec = convert_to_guessit('video_codec', data['video_codec'])
            if not video.audio_codec:
                if data['audio_codec']:
                    video.audio_codec = convert_to_guessit('audio_codec', data['audio_codec'])

    return video
