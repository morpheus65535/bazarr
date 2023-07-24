# -*- coding: utf-8 -*-

import logging
import re

logger = logging.getLogger(__name__)


class FFprobeSubtitleDisposition:
    def __init__(self, data: dict):
        self.default = False
        self.generic = False
        self.dub = False
        self.original = False
        self.comment = False
        self.lyrics = False
        self.karaoke = False
        self.forced = False
        self.hearing_impaired = False
        self.visual_impaired = False
        self.clean_effects = False
        self.attached_pic = False
        self.timed_thumbnails = False
        self._content_type = None

        for key, val in data.items():
            if hasattr(self, key):
                setattr(self, key, bool(val))

        for key in _content_types.keys():
            if getattr(self, key, None):
                self._content_type = key

    def update_from_tags(self, tags):
        tag_title = tags.get("title")
        if tag_title is None:
            logger.debug("Title not found. Marking as generic")
            self.generic = True
            return None

        l_tag_title = tag_title.lower()

        for key, val in _content_types.items():
            if val.search(l_tag_title) is not None:
                logger.debug("Found %s: %s", key, l_tag_title)
                self._content_type = key
                setattr(self, key, True)
                return None

        logger.debug("Generic disposition title found: %s", l_tag_title)
        self.generic = True
        return None

    @property
    def suffix(self):
        return self._content_type or ""

    def language_kwargs(self):
        return {
            "hi": self._content_type == "hearing_impaired" or self.hearing_impaired,
            "forced": self._content_type == "forced" or self.forced,
        }

    def __str__(self):
        return self.suffix.upper() or "GENERIC"


_content_types = {
    "hearing_impaired": re.compile(r"sdh|hearing impaired|cc"),
    "forced": re.compile(r"forced|non[- ]english"),
    "comment": re.compile(r"comment"),
    "visual_impaired": re.compile(r"signs|visual impair"),
    "karaoke": re.compile(r"karaoke|songs"),
}
