# coding=utf-8

import enzyme
from enzyme.exceptions import MalformedMKVError
import logging
import os
import datetime
from knowit import api
from subliminal.cache import region

FFPROBE_CACHE_EXPIRATION_TIME = datetime.timedelta(weeks=2).total_seconds()

_FFPROBE_SPECIAL_LANGS = {
    "zho": {
        "list": ["cht", "tc", "traditional", "zht", "hant", "big5", u"繁", u"雙語"],
        "alpha3": "zht",
    },
    "por": {
        "list": ["pt-br", "pob", "pb", "brazilian", "brasil", "brazil"],
        "alpha3": "pob",
    },
}


class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = None

    @region.cache_on_arguments(expiration_time=FFPROBE_CACHE_EXPIRATION_TIME)
    # file_size, episode_file_id and movie_file_id are used for cache identification. DO NOT REMOVE!
    def list_languages(self, file, file_size, episode_file_id=None, movie_file_id=None):
        from utils import get_binary

        if self.ffprobe is None:  # Don't call get_binary if already set
            self.ffprobe = get_binary("ffprobe")

        subtitles_list = []
        if self.ffprobe:
            subtitles_list += self._ffprobe_scan(file)
        elif file.endswith(".mkv"):
            subtitles_list += self._mkv_fallback(file)

        return subtitles_list

    def _ffprobe_scan(self, file):
        api.initialize({"provider": "ffmpeg", "ffmpeg": self.ffprobe})
        data = api.know(file)

        if "subtitle" in data:
            for detected_language in data["subtitle"]:
                if not "language" in detected_language:
                    continue

                # Avoid commentary subtitles
                name = detected_language.get("name", "").lower()
                if "commentary" in name:
                    logging.debug("Ignoring commentary subtitle: %s", name)
                    continue

                language = self._handle_alpha3(detected_language)

                forced = detected_language.get("forced", False)
                hearing_impaired = detected_language.get("hearing_impaired", False)
                codec = detected_language.get("format")  # or None
                yield [language, forced, hearing_impaired, codec]

    @staticmethod
    def _handle_alpha3(detected_language: dict):
        alpha3 = detected_language["language"].alpha3
        name = detected_language.get("name")

        lang_dict = _FFPROBE_SPECIAL_LANGS.get(alpha3)
        if lang_dict is None or name is None:
            return alpha3  # The original alpha3

        if any(ext in name for ext in lang_dict["list"]):
            return lang_dict["alpha3"]  # Guessed alpha from _FFPROBE_OTHER_LANGS

        return alpha3  # In any case

    @staticmethod
    def _mkv_fallback(file):
        with open(file, "rb") as f:
            try:
                mkv = enzyme.MKV(f)
            except MalformedMKVError:
                logging.error(
                    "BAZARR cannot analyze this MKV with our built-in "
                    "MKV parser, you should install ffmpeg: " + file
                )
            else:
                for subtitle_track in mkv.subtitle_tracks:
                    hearing_impaired = False
                    if subtitle_track.name:
                        hearing_impaired = "sdh" in subtitle_track.name.lower()
                    yield [
                        subtitle_track.language,
                        subtitle_track.forced,
                        hearing_impaired,
                        subtitle_track.codec_id,
                    ]


embedded_subs_reader = EmbeddedSubsReader()
