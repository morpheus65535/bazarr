# coding=utf-8

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

    def __init__(self, name, format=None, release_group=None, resolution=None, video_codec=None, audio_codec=None,
                 imdb_id=None, hashes=None, size=None, subtitle_languages=None, audio_languages=None):
        super(Video, self).__init__(name, format=format, release_group=release_group, resolution=resolution,
                                    video_codec=video_codec, audio_codec=audio_codec, imdb_id=imdb_id, hashes=hashes,
                                    size=size, subtitle_languages=subtitle_languages)
        self.original_name = os.path.basename(name)
        self.plexapi_metadata = {}
        self.hints = {}
        self.audio_languages = audio_languages or set()
        self.external_subtitle_languages = set()
