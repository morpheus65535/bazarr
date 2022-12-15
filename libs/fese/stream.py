# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import timedelta
import logging

from babelfish import Language

from .disposition import FFprobeSubtitleDisposition
from .exceptions import UnsupportedCodec
from .tags import FFprobeGenericSubtitleTags

logger = logging.getLogger(__name__)


class FFprobeSubtitleStream:
    """Base class for FFprobe (FFmpeg) extractable subtitle streams."""

    def __init__(self, stream: dict):
        """
        :raises: LanguageNotFound, UnsupportedCodec
        """
        self.index = int(stream["index"])
        self.codec_name = stream.get("codec_name", "Unknown")

        try:
            self._codec = _codecs[self.codec_name]
        except KeyError:
            raise UnsupportedCodec(f"{self.codec_name} is not supported")

        self.r_frame_rate = stream.get("r_frame_rate")
        self.avg_frame_rate = stream.get("avg_frame_rate")
        self.start_time = timedelta(seconds=float(stream.get("start_time", 0)))
        self.start_pts = timedelta(milliseconds=int(stream.get("start_pts", 0)))
        self.duration_ts = timedelta(milliseconds=int(stream.get("duration_ts", 0)))
        self.duration = timedelta(seconds=float(stream.get("duration", 0)))

        self.tags = FFprobeGenericSubtitleTags.detect_cls_from_data(
            stream.get("tags", {})
        )
        self.disposition = FFprobeSubtitleDisposition(stream.get("disposition", {}))

        self.disposition.update_from_tags(stream.get("tags", {}) or {})

    def convert_args(self, convert_format, outfile):
        """
        convert_format: Union[str, None] = the codec format to convert. if None is set, defaults
        to 'convert_default_format' codec's key
        outfile: str = output file

        raises UnsupportedCodec if convert_format doesn't exist or if the codec doesn't
        support conversion
        """
        convert_format = convert_format or self._codec["convert_default_format"]

        if convert_format is None or not any(
            convert_format == item["copy_format"] for item in _codecs.values()
        ):
            raise UnsupportedCodec(f"Unknown convert format: {convert_format}")

        if not self._codec["convert"]:
            raise UnsupportedCodec(
                f"{self.codec_name} codec doesn't support conversion"
            )

        return ["-map", f"0:{self.index}", "-f", convert_format, outfile]

    def copy_args(self, outfile):
        "raises UnsupportedCodec if the codec doesn't support copy"
        if not self._codec["copy"] or not self._codec["copy_format"]:
            raise UnsupportedCodec(f"{self.codec_name} doesn't support copy")

        return [
            "-map",
            f"0:{self.index}",
            "-c:s",
            "copy",
            "-f",
            self._codec["copy_format"],
            outfile,
        ]

    @property
    def language(self):
        # Legacy
        return self.tags.language

    @language.setter
    def language(self, value: Language):
        self.tags.language = value

    @property
    def extension(self):
        return self._codec["copy_format"] or self._codec["convert_default_format"] or ""

    @property
    def convert_default_format(self):
        return self._codec["convert_default_format"]

    @property
    def type(self):
        return self._codec["type"]

    @property
    def suffix(self):
        return ".".join(
            item
            for item in (self.tags.suffix, self.disposition.suffix, self.extension)
            if item
        )

    def __repr__(self) -> str:
        return f"<{self.codec_name.upper()}: {self.tags}@{self.disposition}>"


_codecs = {
    "ass": {
        "type": "text",
        "copy": True,
        "copy_format": "ass",
        "convert": True,
        "convert_default_format": "srt",
    },
    "subrip": {
        "type": "text",
        "copy": True,
        "copy_format": "srt",
        "convert": True,
        "convert_default_format": "srt",
    },
    "webvtt": {
        "type": "text",
        "copy": True,
        "copy_format": "webvtt",
        "convert": True,
        "convert_default_format": "srt",
    },
    "mov_text": {
        "type": "text",
        "copy": False,
        "copy_format": None,
        "convert": True,
        "convert_default_format": "srt",
    },
    "hdmv_pgs_subtitle": {
        "type": "bitmap",
        "copy": True,
        "copy_format": "sup",
        "convert": False,
        "convert_default_format": None,
    },
    "dvb_subtitle": {
        "type": "bitmap",
        "copy": True,
        "copy_format": "sup",
        "convert": False,
        "convert_default_format": None,
    },
    "dvd_subtitle": {
        "type": "bitmap",
        "copy": True,
        "copy_format": "sup",
        "convert": False,
        "convert_default_format": None,
    },
}
