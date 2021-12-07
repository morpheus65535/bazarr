# -*- coding: utf-8 -*-

import logging
import os
import shutil
import tempfile

from babelfish import language_converters
import fese
from fese import check_integrity
from fese import FFprobeSubtitleStream
from fese import FFprobeVideoContainer
from fese import to_srt
from subliminal.subtitle import fix_line_ending
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

# Replace Babelfish's Language with Subzero's Language
fese.Language = Language


class EmbeddedSubtitle(Subtitle):
    provider_name = "embeddedsubtitles"
    hash_verifiable = False

    def __init__(self, stream, container, matches):
        super().__init__(stream.language, stream.disposition.hearing_impaired)
        self._stream: FFprobeSubtitleStream = stream
        self._container: FFprobeVideoContainer = container
        self._matches: set = matches
        self.page_link = self._container.path
        self.release_info = os.path.basename(self.page_link)

    def get_matches(self, video):
        if self.hearing_impaired:
            self._matches.add("hearing_impaired")

        self._matches.add("hash")
        return self._matches

    @property
    def id(self):
        return f"{self._container.path}_{self._stream.index}"


class EmbeddedSubtitlesProvider(Provider):
    provider_name = "embeddedsubtitles"

    languages = {Language("por", "BR"), Language("spa", "MX")} | {
        Language.fromalpha2(l) for l in language_converters["alpha2"].codes
    }
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))

    # TODO: add forced support
    # languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))

    video_types = (Episode, Movie)
    subtitle_class = EmbeddedSubtitle

    def __init__(
        self, include_ass=True, cache_dir=None, ffprobe_path=None, ffmpeg_path=None
    ):
        self._include_ass = include_ass
        self._cache_dir = cache_dir or os.path.join(
            tempfile.gettempdir(), self.__class__.__name__.lower()
        )
        self._cached_paths = {}

        fese.FFPROBE_PATH = ffprobe_path or fese.FFPROBE_PATH
        fese.FFMPEG_PATH = ffmpeg_path or fese.FFMPEG_PATH

        if logger.getEffectiveLevel() == logging.DEBUG:
            fese.FF_LOG_LEVEL = "warning"
        else:
            # Default is True
            fese.FFMPEG_STATS = False

    def initialize(self):
        os.makedirs(self._cache_dir, exist_ok=True)

    def terminate(self):
        # Remove leftovers
        shutil.rmtree(self._cache_dir, ignore_errors=True)

    def query(self, path: str, languages):
        video = FFprobeVideoContainer(path)

        try:
            streams = video.get_subtitles()
        except fese.InvalidSource as error:
            logger.error("Error trying to get subtitles for %s: %s", video, error)
            streams = []

        if not streams:
            logger.debug("No subtitles found for container: %s", video)

        subtitles = []

        for stream in streams:
            # Only subrip and ass are currently supported
            if stream.codec_name not in ("subrip", "ass"):
                logger.debug("Ignoring codec: %s", stream)
                continue

            if not self._include_ass and stream.codec_name == "ass":
                logger.debug("Ignoring ASS subtitle: %s", stream)
                continue

            if stream.language not in languages:
                continue

            disposition = stream.disposition
            if disposition.generic or disposition.hearing_impaired:
                logger.debug("Appending subtitle: %s", stream)
                subtitles.append(EmbeddedSubtitle(stream, video, {"hash"}))
            else:
                logger.debug("Ignoring unwanted subtitle: %s", stream)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video.name, languages)

    def download_subtitle(self, subtitle):
        path = self._get_subtitle_path(subtitle)
        with open(path, "rb") as sub:
            content = sub.read()
            subtitle.content = fix_line_ending(content)

    def _get_subtitle_path(self, subtitle: EmbeddedSubtitle):
        container = subtitle._container

        # Check if the container is not already in the instance
        if container.path not in self._cached_paths:
            # Extract all subittle streams to avoid reading the entire
            # container over and over
            extracted = container.extract_subtitles(
                container.get_subtitles(), self._cache_dir
            )
            # Add the extracted paths to the containter path key
            self._cached_paths[container.path] = extracted

        cached_path = self._cached_paths[container.path]
        # Get the subtitle file by index
        subtitle_path = cached_path[subtitle._stream.index]

        check_integrity(subtitle._stream, subtitle_path)

        # Convert to SRT if the subtitle is ASS
        new_subtitle_path = to_srt(subtitle_path, remove_source=True)
        if new_subtitle_path != subtitle_path:
            cached_path[subtitle._stream.index] = new_subtitle_path

        return new_subtitle_path
