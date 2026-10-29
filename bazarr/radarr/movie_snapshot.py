# coding=utf-8

from datetime import datetime
from dataclasses import dataclass
from typing import Annotated, TypedDict
from typing_extensions import NotRequired

from pydantic import Field, StrictBool, StrictInt

from utilities.arr_types import Language, FileQuality, DisplayText, RadarrFileSizeBytes, Year, OmittedInt
from utilities.arr_decoding import InvalidAsNone


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
    id: Annotated[StrictInt, Field(gt=0)]
    path: str
    size: RadarrFileSizeBytes

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError('Movie file path is empty')


@dataclass(frozen=True, slots=True)
class IncompleteMovie:
    id: InvalidAsNone[StrictInt] = None
    hasFile: InvalidAsNone[StrictBool] = None
    movieFile: InvalidAsNone[FileState] = None


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
