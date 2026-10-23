# coding=utf-8

from datetime import datetime
from dataclasses import dataclass
from typing import Annotated, TypedDict
from typing_extensions import NotRequired

from pydantic import Field, StrictBool, StrictInt

from utilities.arr_types import Language, FileQuality, OmittedInt


@dataclass(slots=True)
class MediaInfo:
    videoCodec: str | None = None
    audioCodec: str | None = None


@dataclass(slots=True, kw_only=True)
class EpisodeFile:
    id: Annotated[StrictInt, Field(gt=0)]
    path: str
    size: Annotated[StrictInt, Field(ge=0)]
    quality: FileQuality
    sceneName: str | None = None
    language: Language | None = None
    languages: list[Language] | None = None
    mediaInfo: MediaInfo | None = None

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError('Episode file path is empty')


@dataclass(slots=True, kw_only=True)
class Episode:
    id: Annotated[StrictInt, Field(gt=0)]
    seriesId: Annotated[StrictInt, Field(gt=0)]
    title: str
    hasFile: StrictBool
    monitored: StrictBool
    seasonNumber: StrictInt
    episodeNumber: StrictInt
    episodeFileId: OmittedInt = None
    episodeFile: EpisodeFile | None = None
    absoluteEpisodeNumber: StrictInt | None = None
    tvdbId: StrictInt | None = None


class EpisodeValues(TypedDict):
    sonarrSeriesId: int
    sonarrEpisodeId: int
    title: str
    path: str
    season: int
    episode: int
    sceneName: str | None
    monitored: str
    format: str
    resolution: str | None
    video_codec: str | None
    audio_codec: str | None
    episode_file_id: int
    audio_language: str
    file_size: int
    absoluteEpisode: int | None
    tvdbId: int | None
    created_at_timestamp: NotRequired[datetime]
    updated_at_timestamp: NotRequired[datetime]


def complete_episode_snapshot(episodes: list[Episode], episode_files: list[EpisodeFile] | None = None,
                              *, separate_files: bool = False) -> list[Episode] | None:
    files_by_id: dict[int, EpisodeFile] = {}
    if separate_files:
        if episode_files is None:
            return None
        for file in episode_files:
            if file.id in files_by_id:
                return None
            files_by_id[file.id] = file
    seen_ids: set[int] = set()
    for episode in episodes:
        if episode.id in seen_ids:
            return None
        seen_ids.add(episode.id)
        if not episode.hasFile:
            continue
        if separate_files:
            file_id = episode.episodeFileId
            if file_id is None or file_id not in files_by_id:
                return None
        elif episode.episodeFile is None:
            return None
    if separate_files:
        for episode in episodes:
            if episode.hasFile:
                file_id = episode.episodeFileId
                if file_id is None:
                    return None
                episode.episodeFile = files_by_id[file_id]
    return episodes
