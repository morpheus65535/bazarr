# -*- coding: utf-8 -*-
# License: GPL

from __future__ import annotations

import json
import logging
import os
import subprocess

from .exceptions import ExtractionError
from .exceptions import InvalidSource
from .exceptions import LanguageNotFound
from .exceptions import UnsupportedCodec
from .stream import FFprobeSubtitleStream

logger = logging.getLogger(__name__)

# Paths to executables
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", "ffprobe")
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "ffmpeg")

FFMPEG_STATS = True
FF_LOG_LEVEL = "quiet"


class FFprobeVideoContainer:
    def __init__(self, path: str):
        self.path = path

    @property
    def extension(self):
        return os.path.splitext(self.path)[-1].lstrip(".")

    def get_subtitles(self, timeout: int = 600):
        """Factory function to create subtitle (stream) instances from FFprobe.

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
            except (LanguageNotFound, UnsupportedCodec) as error:
                logger.debug("Ignoring %s: %s", stream.get("codec_name"), error)

        if not subs:
            logger.debug("Source doesn't have any subtitle valid streams")
            return []

        logger.debug("Found subtitle streams: %s", subs)
        return subs

    def extract_subtitles(
        self,
        subtitles,
        custom_dir=None,
        overwrite=True,
        timeout=600,
        convert_format=None,
    ):
        """Extracts a list of subtitles converting them. Returns a dictionary of the
        extracted filenames by index.

        Most bitmap subtitles will raise UnsupportedCodec as they don't support conversion.
        For such formats use copy instead.

        :param subtitles: a list of FFprobeSubtitle instances
        :param custom_dir: a custom directory to save the subtitles. Defaults to
        same directory as the media file
        :param overwrite: overwrite files with the same name (default: True)
        :param timeout: subprocess timeout in seconds (default: 600)
        :param convert_format: format to convert selected subtitles. Defaults to
        srt
        :raises: ExtractionError, UnsupportedCodec, OSError
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
            extension_to_use = convert_format or subtitle.convert_default_format

            sub_path = (
                f"{os.path.splitext(self.path)[0]}.{subtitle.suffix}.{extension_to_use}"
            )
            if custom_dir is not None:
                sub_path = os.path.join(custom_dir, os.path.basename(sub_path))

            if not overwrite and sub_path in collected_paths:
                sub_path = f"{os.path.splitext(sub_path)[0]}.{len(collected_paths):02}.{extension_to_use}"

            if not overwrite and os.path.isfile(sub_path):
                logger.debug("Ignoring path (OVERWRITE TRUE): %s", sub_path)
                continue

            extract_command.extend(subtitle.convert_args(convert_format, sub_path))

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
                logger.warning("%s was not extracted", path)

        return items

    def copy_subtitles(
        self,
        subtitles,
        custom_dir=None,
        overwrite=True,
        timeout=600,
        fallback_to_convert=True,
    ):
        """Extracts a list of subtitles with ffmpeg's copy method. Returns a dictionary
        of the extracted filenames by index.

        :param subtitles: a list of FFprobeSubtitle instances
        :param custom_dir: a custom directory to save the subtitles. Defaults to
        same directory as the media file
        :param overwrite: overwrite files with the same name (default: True)
        :param timeout: subprocess timeout in seconds (default: 600)
        :param fallback_to_convert: fallback to stream's default convert format if it is
        incompatible with copy
        :raises: ExtractionError, UnsupportedCodec, OSError
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
            sub_path = f"{os.path.splitext(self.path)[0]}.{subtitle.suffix}.{subtitle.extension}"
            if custom_dir is not None:
                sub_path = os.path.join(custom_dir, os.path.basename(sub_path))

            if not overwrite and sub_path in collected_paths:
                sub_path = f"{os.path.splitext(sub_path)[0]}.{len(collected_paths):02}.{subtitle.extension}"

            if not overwrite and os.path.isfile(sub_path):
                logger.debug("Ignoring path (OVERWRITE TRUE): %s", sub_path)
                continue

            try:
                extract_command.extend(subtitle.copy_args(sub_path))
            except UnsupportedCodec:
                if fallback_to_convert:
                    logger.warning(
                        "%s incompatible with copy. Using fallback", subtitle
                    )
                    extract_command.extend(subtitle.convert_args(None, sub_path))
                else:
                    raise

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
                logger.warning("%s was not extracted", path)

        return items

    def __repr__(self) -> str:
        return f"<FFprobeVideoContainer {self.extension}: {self.path}>"


_ffprobe_exceptions = (
    subprocess.SubprocessError,
    json.JSONDecodeError,
    FileNotFoundError,
    KeyError,
)
