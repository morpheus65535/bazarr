# -*- coding: utf-8 -*-
# License: GPL

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from typing import List, Optional

from babelfish import Language
from babelfish.exceptions import LanguageError
import pysubs2

__version__ = "0.1.2"

logger = logging.getLogger(__name__)

# Paths to executables
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", "ffprobe")
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "ffmpeg")

FFMPEG_STATS = True
FF_LOG_LEVEL = "quiet"


class FeseError(Exception):
    pass


class ExtractionError(FeseError):
    pass


class InvalidFile(FeseError):
    pass


class InvalidStream(FeseError):
    pass


class InvalidSource(FeseError):
    pass


class ConversionError(FeseError):
    pass


class LanguageNotFound(FeseError):
    pass


# Extensions

SRT = "srt"
ASS = "ass"


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
        if self._content_type is not None:
            return f"-{self._content_type}"

        return ""

    def __str__(self):
        return self.suffix.lstrip("-").upper() or "GENERIC"


class FFprobeSubtitleStream:
    """Base class for FFprobe (FFmpeg) extractable subtitle streams."""

    def __init__(self, stream: dict):
        """
        :raises: LanguageNotFound
        """
        self.index = int(stream.get("index", 0))
        self.codec_name = stream.get("codec_name", "Unknown")
        self.extension = _subtitle_extensions.get(self.codec_name, self.codec_name)
        self.r_frame_rate = stream.get("r_frame_rate")
        self.avg_frame_rate = stream.get("avg_frame_rate")
        self.time_base = stream.get("time_base")
        self.tags = stream.get("tags", {})
        self.start_time = float(stream.get("start_time", 0))

        self.duration, self.duration_ts = 0, 0

        # some subtitles streams miss the duration_ts field and only have tags->DURATION field
        # fixme: we still don't know if "DURATION" is a common tag/key
        if "DURATION" in self.tags:
            try:
                h, m, s = self.tags["DURATION"].split(":")
            except ValueError:
                pass
            else:
                self.duration = float(s) + float(m) * 60 + float(h) * 60 * 60
                self.duration_ts = int(self.duration * 1000)
        else:
            try:
                self.duration = float(stream.get("duration", 0))
                self.duration_ts = int(stream.get("duration_ts", 0))
            # some subtitles streams miss a duration completely and has "N/A" as value
            except ValueError:
                pass

        self.start_pts = int(stream.get("start_pts", 0))

        self.disposition = FFprobeSubtitleDisposition(stream.get("disposition", {}))

        if self.tags:
            self.disposition.update_from_tags(self.tags)

        self.language: Language = self._language()

    @property
    def suffix(self):
        lang = self.language.alpha2
        if self.language.country is not None:
            lang = f"{lang}-{self.language.country}"

        return f"{lang}{self.disposition.suffix}.{self.extension}"

    def _language(self) -> Language:
        og_lang = self.tags.get("language")
        last_exc = None

        if og_lang is not None:
            if og_lang in _extra_languages:
                extra = _extra_languages[og_lang]
                title = self.tags.get("title", "n/a").lower()
                if any(possible in title for possible in extra["matches"]):
                    logger.debug("Found extra language %s", extra["language_args"])
                    return Language(*extra["language_args"])

            try:
                lang = Language.fromalpha3b(og_lang)
                # Test for suffix
                assert lang.alpha2

                return lang
            except LanguageError as error:
                last_exc = error
                logger.debug("Error with '%s' language: %s", og_lang, error)

        raise LanguageNotFound(
            f"Couldn't detect language for stream: {self.tags}"
        ) from last_exc

    def __repr__(self) -> str:
        return f"<{self.codec_name.upper()}: {self.language}@{self.disposition}>"


class FFprobeVideoContainer:
    def __init__(self, path: str):
        self.path = path

    @property
    def extension(self):
        return os.path.splitext(self.path)[-1].lstrip(".")

    def get_subtitles(self, timeout: int = 600) -> List[FFprobeSubtitleStream]:
        """Factory function to create subtitle instances from FFprobe.

        :param timeout: subprocess timeout in seconds (default: 600)
        :raises: InvalidSource"""

        ff_command = [
            FFPROBE_PATH,
            "-v",
            FF_LOG_LEVEL,
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            self.path,
        ]
        try:
            result = subprocess.run(
                ff_command, stdout=subprocess.PIPE, check=True, timeout=timeout
            )
            streams = json.loads(result.stdout)["streams"]
        except _ffprobe_exceptions as error:
            raise InvalidSource(
                f"{error} trying to get information from {self.path}"
            ) from error  # We want to see the traceback

        subs = []
        for stream in streams:
            if stream.get("codec_type", "n/a") != "subtitle":
                continue
            try:
                subs.append(FFprobeSubtitleStream(stream))
            except LanguageNotFound:
                pass

        if not subs:
            logger.debug("Source doesn't have any subtitle valid streams")
            return []

        logger.debug("Found subtitle streams: %s", subs)
        return subs

    def extract_subtitles(
        self,
        subtitles: List[FFprobeSubtitleStream],
        custom_dir=None,
        overwrite=True,
        timeout=600,
    ):
        """Extracts a list of subtitles. Returns a dictionary of the extracted
        filenames by index.

        :param subtitles: a list of FFprobeSubtitle instances
        :param custom_dir: a custom directory to save the subtitles. Defaults to
        same directory as the media file
        :param overwrite: overwrite files with the same name (default: True)
        :param timeout: subprocess timeout in seconds (default: 600)
        :raises: ExtractionError, OSError
        """
        extract_command = [FFMPEG_PATH, "-v", FF_LOG_LEVEL]
        if FFMPEG_STATS:
            extract_command.append("-stats")
        extract_command.extend(["-y", "-i", self.path])

        if custom_dir is not None:
            # May raise OSError
            os.makedirs(custom_dir, exist_ok=True)

        items = {}
        collected_paths = set()

        for subtitle in subtitles:
            sub_path = f"{os.path.splitext(self.path)[0]}.{subtitle.suffix}"
            if custom_dir is not None:
                sub_path = os.path.join(custom_dir, os.path.basename(sub_path))

            if sub_path in collected_paths:
                sub_path = (
                    f"{sub_path.rstrip(f'.{subtitle.suffix}')}"
                    f"-{len(collected_paths)}.{subtitle.suffix}"
                )

            if not overwrite and os.path.isfile(sub_path):
                logger.debug("Ignoring path (OVERWRITE TRUE): %s", sub_path)
                continue

            extract_command.extend(
                ["-map", f"0:{subtitle.index}", "-c", "copy", sub_path]
            )
            logger.debug("Appending subtitle path: %s", sub_path)

            collected_paths.add(sub_path)

            items[subtitle.index] = sub_path

        if not items:
            logger.debug("No subtitles to extract")
            return {}

        logger.debug("Extracting subtitle with command %s", " ".join(extract_command))

        try:
            subprocess.run(extract_command, timeout=timeout, check=True)
        except (subprocess.SubprocessError, FileNotFoundError) as error:
            raise ExtractionError(f"Error calling ffmpeg: {error}") from error

        for path in items.values():
            if not os.path.isfile(path):
                logger.debug("%s was not extracted", path)

        return items

    def __repr__(self) -> str:
        return f"<FFprobeVideoContainer {self.extension}: {self.path}>"


def check_integrity(
    subtitle: FFprobeSubtitleStream, path: str, sec_offset_threshold=900
):
    """A relative check for the integriy of a file. This can be used to find a failed
    ffmpeg extraction where the final file might not be complete or might be corrupted.
    Currently, only ASS and Subrip are supported.

    :param subtitle: FFprobeSubtitle instance
    :param path: the path of the subtitle file (ass or srt)
    :param sec_offset_threshold: the maximum seconds offset to determine if the file is complete
    :raises: InvalidFile
    """
    if subtitle.extension not in (ASS, SRT):
        raise InvalidFile(f"Extension not supported: {subtitle.extension}")

    try:
        sub = pysubs2.load(path)
    except (pysubs2.Pysubs2Error, UnicodeError, OSError, FileNotFoundError) as error:
        raise InvalidFile(error) from error
    else:
        # ignore the duration check if the stream has no duration listed at all
        if subtitle.duration_ts:
            off = abs(int(sub[-1].end) - subtitle.duration_ts)
            if off > abs(sec_offset_threshold) * 1000:
                raise InvalidFile(
                    f"The last subtitle timestamp ({sub[-1].end/1000} sec) is {off/1000} sec ahead"
                    f" from the subtitle stream total duration ({subtitle.duration} sec)"
                )
            logger.debug("Integrity check passed (%d sec offset)", off / 1000)
        else:
            logger.warning(
                "Ignoring duration check, subtitle stream has bad duration values: %s",
                subtitle,
            )


def to_srt(
    source: str, output: Optional[str] = None, remove_source: bool = False
) -> str:
    """Convert a subtitle to SubRip. Currently, only ASS is supported. SubRip
    files will be silently ignored.

    raises: ConversionError, OSError"""
    if source.endswith(".srt"):
        return source

    split_path = os.path.splitext(source)

    if split_path[-1] not in (".ass"):
        raise ConversionError(
            f"No converter found for extension: {split_path[-1]}"
        ) from None

    output = output or f"{split_path[0]}.srt"

    try:
        parsed = pysubs2.load(source)
        parsed.save(output)
    except (pysubs2.Pysubs2Error, UnicodeError) as error:
        raise ConversionError(f"Exception converting {output}: {error}") from error

    logger.debug("Converted: %s", output)

    if remove_source and source != output:
        try:
            os.remove(source)
        except OSError as error:
            logger.debug("Can't remove source: %s (%s)", source, error)

    return output


_subtitle_extensions = {
    "subrip": "srt",
    "ass": "ass",
    "hdmv_pgs_subtitle": "sup",
    "pgs": "sup",
}


_content_types = {
    "hearing_impaired": re.compile(r"sdh|hearing impaired"),
    "forced": re.compile(r"forced"),
    "comment": re.compile(r"comment"),
    "visual_impaired": re.compile(r"signs|visual impair"),
    "karaoke": re.compile(r"karaoke|songs"),
}


_ffprobe_exceptions = (
    subprocess.SubprocessError,
    json.JSONDecodeError,
    FileNotFoundError,
    KeyError,
)

_extra_languages = {
    "spa": {
        "matches": (
            "es-la",
            "spa-la",
            "spl",
            "mx",
            "latin",
            "mexic",
            "argent",
            "latam",
        ),
        "language_args": ("spa", "MX"),
    },
    "por": {
        "matches": ("pt-br", "pob", "pb", "brazilian", "brasil", "brazil"),
        "language_args": ("por", "BR"),
    },
}
