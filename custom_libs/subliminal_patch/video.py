# coding=utf-8

from __future__ import absolute_import
import os

from subliminal.video import Video as Video_


class Video(Video_):
    is_special = False
    fps = None
    plexapi_metadata = None
    hints = None
    season_fully_aired = None
    audio_languages = None
    external_subtitle_languages = None
    info_url = None

    def __init__(
        self,
        name,
        source=None,
        release_group=None,
        resolution=None,
        video_codec=None,
        audio_codec=None,
        imdb_id=None,
        hashes=None,
        size=None,
        subtitle_languages=None,
        audio_languages=None,
        streaming_service=None,
        edition=None,
        other=None,
        info_url=None,
        series_anidb_id=None,
        series_anidb_episode_id=None,
        series_anidb_season_episode_offset=None,
        anilist_id=None,
        **kwargs
    ):
        super(Video, self).__init__(
            name,
            source=source,
            release_group=release_group,
            resolution=resolution,
            video_codec=video_codec,
            audio_codec=audio_codec,
            imdb_id=imdb_id,
            hashes=hashes,
            size=size,
            subtitle_languages=subtitle_languages,
        )
        self.original_name = os.path.basename(name)
        self.plexapi_metadata = {}
        self.hints = {}
        self.audio_languages = audio_languages or set()
        self.external_subtitle_languages = set()
        self.streaming_service = streaming_service
        self.edition = edition
        self.original_path = name
        self.other = other
        self.info_url = info_url
        self.series_anidb_series_id = series_anidb_id,
        self.series_anidb_episode_id = series_anidb_episode_id,
        self.series_anidb_season_episode_offset = series_anidb_season_episode_offset,
        self.anilist_id = anilist_id,
