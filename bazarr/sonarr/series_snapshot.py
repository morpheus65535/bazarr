# coding=utf-8

from datetime import datetime
from dataclasses import dataclass
from typing import Annotated, TypedDict
from typing_extensions import NotRequired

from pydantic import Strict, StrictBool, StrictInt

from utilities.external_ids import TmdbId
from utilities.arr_types import Year, OmittedInt


@dataclass(slots=True)
class SeriesImage:
    coverType: str
    url: str


@dataclass(slots=True)
class AlternateTitle:
    title: str | None = None


@dataclass(slots=True)
class SeriesLanguage:
    name: str | None = None


@dataclass(slots=True, kw_only=True)
class Series:
    id: StrictInt
    title: str
    path: str
    tvdbId: StrictInt
    sortTitle: str
    year: Year | None
    seriesType: str
    monitored: StrictBool
    images: list[SeriesImage]
    alternateTitles: list[AlternateTitle] | None
    tags: list[StrictInt]
    overview: str | None = ''
    imdbId: str | None = None
    tmdbId: Annotated[TmdbId, Strict()] | None = None
    ended: StrictBool = False
    lastAired: str | None = None
    originalLanguage: SeriesLanguage | None = None
    qualityProfileId: OmittedInt = None
    languageProfileId: OmittedInt = None


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
    tmdbId: TmdbId | None
    monitored: str
    ended: str
    lastAired: str | None
    originalLanguage: str | None
    profileId: NotRequired[int | None]
    updated_at_timestamp: NotRequired[datetime]
    created_at_timestamp: NotRequired[datetime]
