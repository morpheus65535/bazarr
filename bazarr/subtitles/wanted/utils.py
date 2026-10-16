# coding=utf-8

from typing import Protocol

from subtitles.adaptive_searching import get_active_search_languages
from subtitles.serialization import parse_missing_subtitles, missing_subtitle_to_language_tuple


class WantedMedia(Protocol):
    path: str | None
    missing_subtitles_calculated: bool
    audio_language: str | None
    sceneName: str | None
    title: str | None
    profileId: int | None
    has_indexed_subtitles: bool
    has_incomplete_embedded_subtitles: bool


class WantedMovie(WantedMedia, Protocol):
    radarrId: int


class WantedEpisode(WantedMedia, Protocol):
    sonarrEpisodeId: int
    sonarrSeriesId: int
    season: int | None
    episode: int | None
    episodeTitle: str | None


def get_due_missing_languages(missing_subtitles, failed_attempts, adaptive_search_policy=None):
    desired_languages = parse_missing_subtitles(missing_subtitles)
    if not desired_languages:
        return []

    return get_active_search_languages(
        desired_languages,
        failed_attempts,
        adaptive_search_policy=adaptive_search_policy,
    )


def get_language_search_items(missing_languages):
    return [missing_subtitle_to_language_tuple(language) for language in missing_languages]
