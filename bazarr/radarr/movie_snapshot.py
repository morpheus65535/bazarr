# coding=utf-8

from datetime import datetime
from dataclasses import dataclass
from typing import TypedDict
from typing_extensions import NotRequired

from pydantic import StrictBool, StrictInt

from utilities.arr_types import Language, FileQuality, DisplayText, RadarrFileSizeBytes, Year, OmittedInt
from utilities.json_types import JsonValue


@dataclass(slots=True)
class MovieMediaInfo:
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


@dataclass(slots=True, kw_only=True)
class MovieFile:
    id: StrictInt
    path: str
    size: RadarrFileSizeBytes
    quality: FileQuality
    sceneName: str | None = None
    languages: list[Language] | None = None
    mediaInfo: MovieMediaInfo | None = None

    def __post_init__(self) -> None:
        if self.id <= 0 or not self.path.strip():
            raise ValueError('Invalid movie file identity')


@dataclass(slots=True)
class MovieImage:
    url: str


@dataclass(slots=True)
class MovieTitle:
    title: str | None


@dataclass(slots=True)
class MovieLanguage:
    name: str | None = None


@dataclass(slots=True, kw_only=True)
class Movie:
    id: StrictInt
    title: str
    tmdbId: StrictInt | str | StrictBool
    year: Year | None
    sortTitle: str
    monitored: StrictBool
    hasFile: StrictBool
    tags: list[StrictInt]
    movieFile: MovieFile | None = None
    images: list[MovieImage] | None = None
    overview: DisplayText = ''
    alternativeTitles: list[MovieTitle] | None = None
    alternateTitles: list[MovieTitle] | None = None
    imdbId: str | None = None
    originalLanguage: MovieLanguage | None = None
    qualityProfileId: OmittedInt = None


@dataclass(frozen=True, slots=True)
class FileState:
    id: int
    path: str
    size: int


@dataclass(frozen=True, slots=True)
class IncompleteMovie:
    id: int | None
    hasFile: bool | None
    movieFile: FileState | None

    @classmethod
    def from_value(cls, value: JsonValue) -> 'IncompleteMovie':
        if not isinstance(value, dict):
            return cls(None, None, None)
        identifier, has_file = value.get('id'), value.get('hasFile')
        raw_file = value.get('movieFile')
        file = None
        if isinstance(raw_file, dict):
            file_id, path = raw_file.get('id'), raw_file.get('path')
            size = movie_file_size(raw_file.get('size'))
            if type(file_id) is int and file_id > 0 and isinstance(path, str) and path.strip() and size is not None:
                file = FileState(file_id, path, size)
        return cls(identifier if type(identifier) is int else None,
                   has_file if isinstance(has_file, bool) else None, file)


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
