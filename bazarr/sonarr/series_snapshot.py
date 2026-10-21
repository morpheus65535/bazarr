# coding=utf-8

from datetime import datetime
from typing import TypedDict
from typing_extensions import NotRequired

import msgspec


class SeriesImage(msgspec.Struct):
    coverType: str
    url: str


class AlternateTitle(msgspec.Struct):
    title: str | None = None


class SeriesLanguage(msgspec.Struct):
    name: str | None = None


class Series(msgspec.Struct, kw_only=True):
    id: int
    title: str
    path: str
    tvdbId: int
    sortTitle: str
    year: int | str | bool
    seriesType: str
    monitored: bool
    images: list[SeriesImage]
    alternateTitles: list[AlternateTitle] | None
    tags: list[int]
    overview: str | None = ''
    imdbId: str | None = None
    tmdbId: str | None = None
    ended: bool = False
    lastAired: str | None = None
    originalLanguage: SeriesLanguage | None = None
    qualityProfileId: int | msgspec.UnsetType = msgspec.UNSET
    languageProfileId: int | msgspec.UnsetType = msgspec.UNSET


class SeriesValues(TypedDict):
    title: str
    path: str
    tvdbId: int
    sonarrSeriesId: int
    overview: str | None
    poster: str
    fanart: str
    audio_language: str
    sortTitle: str
    year: str
    alternativeTitles: str
    tags: str
    seriesType: str
    imdbId: str | None
    monitored: str
    ended: str
    lastAired: str | None
    originalLanguage: str | None
    profileId: NotRequired[int | None]
    updated_at_timestamp: NotRequired[datetime]
    created_at_timestamp: NotRequired[datetime]
