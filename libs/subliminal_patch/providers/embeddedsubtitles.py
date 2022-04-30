# -*- coding: utf-8 -*-

import functools
import logging
import os
import shutil
import tempfile

from babelfish import language_converters
import fese
from fese import check_integrity
from fese import FFprobeSubtitleStream
from fese import FFprobeVideoContainer
from fese import InvalidFile
from fese import to_srt
from subliminal.subtitle import fix_line_ending
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.exceptions import MustGetBlacklisted
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

# Replace Babelfish's Language with Subzero's Language
fese.Language = Language


class EmbeddedSubtitle(Subtitle):
    provider_name = "embeddedsubtitles"
    hash_verifiable = False

    def __init__(self, stream, container, matches, media_type):
        super().__init__(stream.language, stream.disposition.hearing_impaired)
        if stream.disposition.forced:
            self.language = Language.rebuild(stream.language, forced=True)

        self.stream: FFprobeSubtitleStream = stream
        self.container: FFprobeVideoContainer = container
        self.forced = stream.disposition.forced
        self.page_link = self.container.path
        self.release_info = os.path.basename(self.page_link)
        self.media_type = media_type

        self._matches: set = matches

    def get_matches(self, video):
        if self.hearing_impaired:
            self._matches.add("hearing_impaired")

        self._matches.add("hash")
        return self._matches

    @property
    def id(self):
        return f"{self.container.path}_{self.stream.index}"


class EmbeddedSubtitlesProvider(Provider):
    provider_name = "embeddedsubtitles"

    languages = {Language("por", "BR"), Language("spa", "MX")} | {
        Language.fromalpha2(l) for l in language_converters["alpha2"].codes
    }
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))

    video_types = (Episode, Movie)
    subtitle_class = EmbeddedSubtitle
    _blacklist = set()

    def __init__(
        self,
        include_ass=True,
        include_srt=True,
        cache_dir=None,
        ffprobe_path=None,
        ffmpeg_path=None,
        hi_fallback=False,
        mergerfs_mode=False,
        timeout=600,
    ):
        self._include_ass = include_ass
        self._include_srt = include_srt
        self._cache_dir = os.path.join(
            cache_dir or tempfile.gettempdir(), self.__class__.__name__.lower()
        )
        self._hi_fallback = hi_fallback
        self._cached_paths = {}
        self._mergerfs_mode = mergerfs_mode
        self._timeout = float(timeout)

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

    def query(self, path: str, languages, media_type):
        video = _get_memoized_video_container(path)

        try:
            streams = filter(_check_allowed_extensions, video.get_subtitles())
        except fese.InvalidSource as error:
            logger.error("Error trying to get subtitles for %s: %s", video, error)
            self._blacklist.add(path)
            streams = []

        if not streams:
            logger.debug("No subtitles found for container: %s", video)

        only_forced = all(lang.forced for lang in languages)
        also_forced = any(lang.forced for lang in languages)

        allowed_streams = []

        for stream in streams:
            if not self._include_ass and stream.extension == "ass":
                logger.debug("Ignoring ASS: %s", stream)
                continue

            if not self._include_srt and stream.extension == "srt":
                logger.debug("Ignoring SRT: %s", stream)
                continue

            if stream.language not in languages:
                continue

            disposition = stream.disposition

            if only_forced and not disposition.forced:
                continue

            if (
                disposition.generic
                or disposition.hearing_impaired
                or (disposition.forced and also_forced)
            ):
                logger.debug("Appending subtitle: %s", stream)
                allowed_streams.append(stream)
            else:
                logger.debug("Ignoring unwanted subtitle: %s", stream)

        if self._hi_fallback:
            _check_hi_fallback(allowed_streams, languages)

        logger.debug("Cache info: %s", _get_memoized_video_container.cache_info())

        return [
            EmbeddedSubtitle(stream, video, {"hash"}, media_type)
            for stream in allowed_streams
        ]

    def list_subtitles(self, video, languages):
        if not self._is_path_valid(video.original_path):
            logger.debug("Ignoring video: %s", video)
            return []

        return self.query(
            video.original_path,
            languages,
            "series" if isinstance(video, Episode) else "movie",
        )

    def download_subtitle(self, subtitle):
        path = self._get_subtitle_path(subtitle)
        with open(path, "rb") as sub:
            content = sub.read()
            subtitle.content = fix_line_ending(content)

    def _get_subtitle_path(self, subtitle: EmbeddedSubtitle):
        container = subtitle.container

        # Check if the container is not already in the instance
        if container.path not in self._cached_paths:
            # Extract all subittle streams to avoid reading the entire
            # container over and over
            streams = filter(_check_allowed_extensions, container.get_subtitles())
            extracted = container.extract_subtitles(
                list(streams), self._cache_dir, timeout=self._timeout
            )
            # Add the extracted paths to the containter path key
            self._cached_paths[container.path] = extracted

        cached_path = self._cached_paths[container.path]
        # Get the subtitle file by index
        subtitle_path = cached_path[subtitle.stream.index]

        try:
            check_integrity(subtitle.stream, subtitle_path)
        except InvalidFile as error:
            raise MustGetBlacklisted(subtitle.id, subtitle.media_type) from error

        # Convert to SRT if the subtitle is ASS
        new_subtitle_path = to_srt(subtitle_path, remove_source=True)
        if new_subtitle_path != subtitle_path:
            cached_path[subtitle.stream.index] = new_subtitle_path

        return new_subtitle_path

    def _is_path_valid(self, path):
        if path in self._blacklist:
            logger.debug("Blacklisted path: %s", path)
            return False

        if not os.path.isfile(path):
            logger.debug("Inexistent file: %s", path)
            return False

        if self._mergerfs_mode and _is_fuse_rclone_mount(path):
            logger.debug("Potential cloud file: %s", path)
            return False

        return True


class _MemoizedFFprobeVideoContainer(FFprobeVideoContainer):
    # 128 is the default value for maxsize since Python 3.8. We ste it here for previous versions.
    @functools.lru_cache(maxsize=128)
    def get_subtitles(self, *args, **kwargs):
        return super().get_subtitles(*args, **kwargs)


@functools.lru_cache(maxsize=8096)
def _get_memoized_video_container(path: str):
    return _MemoizedFFprobeVideoContainer(path)


def _check_allowed_extensions(subtitle: FFprobeSubtitleStream):
    return subtitle.extension in ("ass", "srt")


def _check_hi_fallback(streams, languages):
    for language in languages:
        compatible_streams = [
            stream for stream in streams if stream.language == language
        ]
        if len(compatible_streams) == 1:
            stream = compatible_streams[0]
            logger.debug("HI fallback: updating %s HI to False", stream)
            stream.disposition.hearing_impaired = False

        elif all(stream.disposition.hearing_impaired for stream in streams):
            for stream in streams:
                logger.debug("HI fallback: updating %s HI to False", stream)
                stream.disposition.hearing_impaired = False

        else:
            logger.debug("HI fallback not needed: %s", compatible_streams)


def _is_fuse_rclone_mount(path: str):
    # Experimental!

    # This function only makes sense if you are combining a rclone mount with a local mount
    # with mergerfs or similar tools. Don't use it otherwise.

    # It tries to guess whether a file is a cloud mount by the length
    # of the inode number. See the following links for reference.

    # https://forum.rclone.org/t/fuse-inode-number-aufs/215/5
    # https://pkg.go.dev/bazil.org/fuse/fs?utm_source=godoc#GenerateDynamicInode
    return len(str(os.stat(path).st_ino)) > 18
