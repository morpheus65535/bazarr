# coding=utf-8

from datetime import datetime
from typing import TypedDict
from typing_extensions import NotRequired

import msgspec

from utilities.arr_types import Language, FileQuality, DisplayText
from utilities.json_types import JsonValue


class MovieMediaInfo(msgspec.Struct):
    videoFormat: str | None = None
    videoCodec: str | None = None
    videoCodecID: str | None = None
    videoCodecLibrary: str | None = None
    audioFormat: str | None = None
    audioCodec: str | None = None
    audioCodecID: str | None = None
    audioProfile: str | None = None
    audioAdditionalFeatures: str | None = None
    audioLanguages: str | None = None


class MovieFile(msgspec.Struct, kw_only=True):
    id: int
    path: str
    size: int | str | float
    quality: FileQuality
    sceneName: str | None = None
    languages: list[Language] | None = None
    mediaInfo: MovieMediaInfo | None = None

    def __post_init__(self) -> None:
        if movie_file_size(self.size) is None:
            raise ValueError('Invalid movie file size')


class MovieImage(msgspec.Struct):
    url: str


class MovieTitle(msgspec.Struct):
    title: str | None


class MovieLanguage(msgspec.Struct):
    name: str | None = None


class Movie(msgspec.Struct, kw_only=True):
    id: int
    title: str
    tmdbId: int | str | bool
    year: int | str | bool
    sortTitle: str
    monitored: bool
    hasFile: bool
    tags: list[int]
    movieFile: MovieFile | None = None
    images: list[MovieImage] | None = None
    overview: DisplayText = DisplayText('')
    alternativeTitles: list[MovieTitle] | None = None
    alternateTitles: list[MovieTitle] | None = None
    imdbId: str | None = None
    originalLanguage: MovieLanguage | None = None
    qualityProfileId: int | msgspec.UnsetType = msgspec.UNSET


class MovieValues(TypedDict):
    radarrId: int
    title: str
    path: str
    tmdbId: str
    poster: str
    fanart: str
    audio_language: str
    sceneName: str | None
    monitored: str
    year: str
    sortTitle: str
    alternativeTitles: str | None
    format: str
    resolution: str | None
    video_codec: str | None
    audio_codec: str | None
    overview: str
    imdbId: str | None
    movie_file_id: int
    tags: str
    file_size: int
    originalLanguage: str | None
    profileId: NotRequired[int | None]
    created_at_timestamp: NotRequired[datetime]
    updated_at_timestamp: NotRequired[datetime]


def movie_file_size(value: JsonValue) -> int | None:
    if not isinstance(value, (int, str, float)) or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (ValueError, OverflowError):
        return None
