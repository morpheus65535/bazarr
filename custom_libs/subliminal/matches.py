# -*- coding: utf-8 -*-
from rebulk.loose import ensure_list

from .score import get_equivalent_release_groups, score_keys
from .video import Episode, Movie
from .utils import sanitize, sanitize_release_group


def series_matches(video, title=None, **kwargs):
    """Whether the `video` matches the series title.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str title: the series name.
    :return: whether there's a match
    :rtype: bool

    """
    if isinstance(video, Episode):
        return video.series and sanitize(title) in (
            sanitize(name) for name in [video.series] + video.alternative_series
        )


def title_matches(video, title=None, episode_title=None, **kwargs):
    """Whether the movie matches the movie `title` or the series matches the `episode_title`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str title: the movie title.
    :param str episode_title: the series episode title.
    :return: whether there's a match
    :rtype: bool

    """
    if isinstance(video, Episode):
        return video.title and sanitize(episode_title) == sanitize(video.title)
    if isinstance(video, Movie):
        return video.title and sanitize(title) == sanitize(video.title)


def season_matches(video, season=None, **kwargs):
    """Whether the episode matches the `season`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param int season: the episode season.
    :return: whether there's a match
    :rtype: bool

    """
    if isinstance(video, Episode):
        return video.season and season == video.season


def episode_matches(video, episode=None, **kwargs):
    """Whether the episode matches the `episode`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param episode: the episode season.
    :type: list of int or int
    :return: whether there's a match
    :rtype: bool

    """
    if isinstance(video, Episode):
        return video.episodes and ensure_list(episode) == video.episodes


def year_matches(video, year=None, partial=False, **kwargs):
    """Whether the video matches the `year`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param int year: the video year.
    :param bool partial: whether or not the guess is partial.
    :return: whether there's a match
    :rtype: bool

    """
    if video.year and year == video.year:
        return True
    if isinstance(video, Episode):
        # count "no year" as an information
        return not partial and video.original_series and not year


def country_matches(video, country=None, partial=False, **kwargs):
    """Whether the video matches the `country`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param country: the video country.
    :type country: :class:`~babelfish.country.Country`
    :param bool partial: whether or not the guess is partial.
    :return: whether there's a match
    :rtype: bool

    """
    if video.country and country == video.country:
        return True

    if isinstance(video, Episode):
        # count "no country" as an information
        return not partial and video.original_series and not country

    if isinstance(video, Movie):
        # count "no country" as an information
        return not video.country and not country


def release_group_matches(video, release_group=None, **kwargs):
    """Whether the video matches the `release_group`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str release_group: the video release group.
    :return: whether there's a match
    :rtype: bool

    """
    return (video.release_group and release_group and
            any(r in sanitize_release_group(release_group)
                for r in get_equivalent_release_groups(sanitize_release_group(video.release_group))))


def streaming_service_matches(video, streaming_service=None, **kwargs):
    """Whether the video matches the `streaming_service`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str streaming_service: the video streaming service
    :return: whether there's a match
    :rtype: bool

    """
    return video.streaming_service and streaming_service == video.streaming_service


def resolution_matches(video, screen_size=None, **kwargs):
    """Whether the video matches the `resolution`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str screen_size: the video resolution
    :return: whether there's a match
    :rtype: bool

    """
    return video.resolution and screen_size == video.resolution


def source_matches(video, source=None, **kwargs):
    """Whether the video matches the `source`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str source: the video source
    :return: whether there's a match
    :rtype: bool

    """
    return video.source and source == video.source


def video_codec_matches(video, video_codec=None, **kwargs):
    """Whether the video matches the `video_codec`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str video_codec: the video codec
    :return: whether there's a match
    :rtype: bool

    """
    return video.video_codec and video_codec == video.video_codec


def audio_codec_matches(video, audio_codec=None, **kwargs):
    """Whether the video matches the `audio_codec`.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param str audio_codec: the video audio codec
    :return: whether there's a match
    :rtype: bool

    """
    return video.audio_codec and audio_codec == video.audio_codec


#: Available matches functions
matches_manager = {
    'series': series_matches,
    'title': title_matches,
    'season': season_matches,
    'episode': episode_matches,
    'year': year_matches,
    'country': country_matches,
    'release_group': release_group_matches,
    'streaming_service': streaming_service_matches,
    'resolution': resolution_matches,
    'source': source_matches,
    'video_codec': video_codec_matches,
    'audio_codec': audio_codec_matches
}


def guess_matches(video, guess, partial=False):
    """Get matches between a `video` and a `guess`.

    If a guess is `partial`, the absence information won't be counted as a match.

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param guess: the guess.
    :type guess: dict
    :param bool partial: whether or not the guess is partial.
    :return: matches between the `video` and the `guess`.
    :rtype: set

    """
    matches = set()
    for key in score_keys:
        if key in matches_manager and matches_manager[key](video, partial=partial, **guess):
            matches.add(key)

    return matches
