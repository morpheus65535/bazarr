# -*- coding: utf-8 -*-
from __future__ import division
from datetime import datetime, timedelta
import logging
import os

from guessit import guessit

logger = logging.getLogger(__name__)

#: Video extensions
VIDEO_EXTENSIONS = ('.3g2', '.3gp', '.3gp2', '.3gpp', '.60d', '.ajp', '.asf', '.asx', '.avchd', '.avi', '.bik',
                    '.bix', '.box', '.cam', '.dat', '.divx', '.dmf', '.dv', '.dvr-ms', '.evo', '.flc', '.fli',
                    '.flic', '.flv', '.flx', '.gvi', '.gvp', '.h264', '.m1v', '.m2p', '.m2ts', '.m2v', '.m4e',
                    '.m4v', '.mjp', '.mjpeg', '.mjpg', '.mkv', '.moov', '.mov', '.movhd', '.movie', '.movx', '.mp4',
                    '.mpe', '.mpeg', '.mpg', '.mpv', '.mpv2', '.mxf', '.nsv', '.nut', '.ogg', '.ogm' '.ogv', '.omf',
                    '.ps', '.qt', '.ram', '.rm', '.rmvb', '.swf', '.ts', '.vfw', '.vid', '.video', '.viv', '.vivo',
                    '.vob', '.vro', '.wm', '.wmv', '.wmx', '.wrap', '.wvx', '.wx', '.x264', '.xvid')


class Video(object):
    """Base class for videos.

    Represent a video, existing or not.

    :param str name: name or path of the video.
    :param str format: format of the video (HDTV, WEB-DL, BluRay, ...).
    :param str release_group: release group of the video.
    :param str resolution: resolution of the video stream (480p, 720p, 1080p or 1080i).
    :param str video_codec: codec of the video stream.
    :param str audio_codec: codec of the main audio stream.
    :param str imdb_id: IMDb id of the video.
    :param dict hashes: hashes of the video file by provider names.
    :param int size: size of the video file in bytes.
    :param set subtitle_languages: existing subtitle languages.

    """
    def __init__(self, name, format=None, release_group=None, resolution=None, video_codec=None, audio_codec=None,
                 imdb_id=None, hashes=None, size=None, subtitle_languages=None):
        #: Name or path of the video
        self.name = name

        #: Format of the video (HDTV, WEB-DL, BluRay, ...)
        self.format = format

        #: Release group of the video
        self.release_group = release_group

        #: Resolution of the video stream (480p, 720p, 1080p or 1080i)
        self.resolution = resolution

        #: Codec of the video stream
        self.video_codec = video_codec

        #: Codec of the main audio stream
        self.audio_codec = audio_codec

        #: IMDb id of the video
        self.imdb_id = imdb_id

        #: Hashes of the video file by provider names
        self.hashes = hashes or {}

        #: Size of the video file in bytes
        self.size = size

        #: Existing subtitle languages
        self.subtitle_languages = subtitle_languages or set()

    @property
    def exists(self):
        """Test whether the video exists"""
        return os.path.exists(self.name)

    @property
    def age(self):
        """Age of the video"""
        if self.exists:
            return datetime.utcnow() - datetime.utcfromtimestamp(os.path.getmtime(self.name))

        return timedelta()

    @classmethod
    def fromguess(cls, name, guess):
        """Create an :class:`Episode` or a :class:`Movie` with the given `name` based on the `guess`.

        :param str name: name of the video.
        :param dict guess: guessed data.
        :raise: :class:`ValueError` if the `type` of the `guess` is invalid

        """
        if guess['type'] == 'episode':
            return Episode.fromguess(name, guess)

        if guess['type'] == 'movie':
            return Movie.fromguess(name, guess)

        raise ValueError('The guess must be an episode or a movie guess')

    @classmethod
    def fromname(cls, name):
        """Shortcut for :meth:`fromguess` with a `guess` guessed from the `name`.

        :param str name: name of the video.

        """
        return cls.fromguess(name, guessit(name))

    def __repr__(self):
        return '<%s [%r]>' % (self.__class__.__name__, self.name)

    def __hash__(self):
        return hash(self.name)


class Episode(Video):
    """Episode :class:`Video`.

    :param str series: series of the episode.
    :param int season: season number of the episode.
    :param int episode: episode number of the episode.
    :param str title: title of the episode.
    :param int year: year of the series.
    :param bool original_series: whether the series is the first with this name.
    :param int tvdb_id: TVDB id of the episode.
    :param \*\*kwargs: additional parameters for the :class:`Video` constructor.

    """
    def __init__(self, name, series, season, episode, title=None, year=None, original_series=True, tvdb_id=None,
                 series_tvdb_id=None, series_imdb_id=None, **kwargs):
        super(Episode, self).__init__(name, **kwargs)

        #: Series of the episode
        self.series = series

        #: Season number of the episode
        self.season = season

        #: Episode number of the episode
        self.episode = episode

        #: Title of the episode
        self.title = title

        #: Year of series
        self.year = year

        #: The series is the first with this name
        self.original_series = original_series

        #: TVDB id of the episode
        self.tvdb_id = tvdb_id

        #: TVDB id of the series
        self.series_tvdb_id = series_tvdb_id

        #: IMDb id of the series
        self.series_imdb_id = series_imdb_id

    @classmethod
    def fromguess(cls, name, guess):
        if guess['type'] != 'episode':
            raise ValueError('The guess must be an episode guess')

        if 'title' not in guess or 'episode' not in guess:
            raise ValueError('Insufficient data to process the guess')

        return cls(name, guess['title'], guess.get('season', 1), guess['episode'], title=guess.get('episode_title'),
                   year=guess.get('year'), format=guess.get('format'), original_series='year' not in guess,
                   release_group=guess.get('release_group'), resolution=guess.get('screen_size'),
                   video_codec=guess.get('video_codec'), audio_codec=guess.get('audio_codec'))

    @classmethod
    def fromname(cls, name):
        return cls.fromguess(name, guessit(name, {'type': 'episode'}))

    def __repr__(self):
        if self.year is None:
            return '<%s [%r, %dx%d]>' % (self.__class__.__name__, self.series, self.season, self.episode)

        return '<%s [%r, %d, %dx%d]>' % (self.__class__.__name__, self.series, self.year, self.season, self.episode)


class Movie(Video):
    """Movie :class:`Video`.

    :param str title: title of the movie.
    :param int year: year of the movie.
    :param \*\*kwargs: additional parameters for the :class:`Video` constructor.

    """
    def __init__(self, name, title, year=None, **kwargs):
        super(Movie, self).__init__(name, **kwargs)

        #: Title of the movie
        self.title = title

        #: Year of the movie
        self.year = year

    @classmethod
    def fromguess(cls, name, guess):
        if guess['type'] != 'movie':
            raise ValueError('The guess must be a movie guess')

        if 'title' not in guess:
            raise ValueError('Insufficient data to process the guess')

        return cls(name, guess['title'], format=guess.get('format'), release_group=guess.get('release_group'),
                   resolution=guess.get('screen_size'), video_codec=guess.get('video_codec'),
                   audio_codec=guess.get('audio_codec'), year=guess.get('year'))

    @classmethod
    def fromname(cls, name):
        return cls.fromguess(name, guessit(name, {'type': 'movie'}))

    def __repr__(self):
        if self.year is None:
            return '<%s [%r]>' % (self.__class__.__name__, self.title)

        return '<%s [%r, %d]>' % (self.__class__.__name__, self.title, self.year)
