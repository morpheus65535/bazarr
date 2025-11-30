# -*- coding: utf-8 -*-

import functools
import hashlib
import logging
import os
import re
import shutil
import tempfile
from typing import List

from babelfish import language_converters
from fese import container
from fese import FFprobeSubtitleStream
from fese import FFprobeVideoContainer
from fese import tags
from fese.exceptions import ExtractionError
from fese.exceptions import InvalidSource
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import blacklist_on
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

# Replace Babelfish's Language with Subzero's Language
tags.Language = Language


class EmbeddedSubtitle(Subtitle):
    provider_name = "embeddedsubtitles"
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, stream, container, matches, media_type):
        super().__init__(stream.language, stream.disposition.hearing_impaired)
        if stream.disposition.forced:
            self.language = Language.rebuild(stream.language, forced=True)

        self.stream: FFprobeSubtitleStream = stream
        self.container: FFprobeVideoContainer = container
        self.forced = stream.disposition.forced
        self.page_link = self.container.path
        self.release_info = _get_pretty_release_name(stream, container)
        self.media_type = media_type

        self._matches: set = matches

    def get_matches(self, video):
        if self.language.hi:
            self._matches.add("hearing_impaired")

        self._matches.add("hash")

        return self._matches

    @property
    def id(self):
        return f"{self.container.path}_{self.stream.index}"


_ALLOWED_CODECS = ("ass", "subrip", "webvtt", "mov_text")


class EmbeddedSubtitlesProvider(Provider):
    provider_name = "embeddedsubtitles"

    languages = {Language("por", "BR"), Language("spa", "MX"), Language("zho", "TW")} | {
        Language.fromalpha2(l) for l in language_converters["alpha2"].codes
    }
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))

    video_types = (Episode, Movie)
    subtitle_class = EmbeddedSubtitle
    _blacklist = set()

    def __init__(
        self,
        included_codecs=None,
        cache_dir=None,
        ffprobe_path=None,
        ffmpeg_path=None,
        hi_fallback=False,
        timeout=600,
        unknown_as_fallback=False,
        fallback_lang="en",
    ):
        self._included_codecs = set(included_codecs or _ALLOWED_CODECS)

        for codec in self._included_codecs:
            if codec not in _ALLOWED_CODECS:
                logger.warning("Unallowed codec: %s", codec)

        self._cache_dir = os.path.join(
            cache_dir or tempfile.gettempdir(), self.__class__.__name__.lower()
        )
        self._hi_fallback = hi_fallback
        self._unknown_as_fallback = unknown_as_fallback
        self._fallback_lang = fallback_lang
        self._cached_paths = {}
        self._timeout = int(timeout)

        container.FFPROBE_PATH = ffprobe_path or container.FFPROBE_PATH
        container.FFMPEG_PATH = ffmpeg_path or container.FFMPEG_PATH

        if logger.getEffectiveLevel() == logging.DEBUG:
            container.FF_LOG_LEVEL = "warning"
        else:
            # Default is True
            container.FFMPEG_STATS = False

        tags.LANGUAGE_FALLBACK = (
            self._fallback_lang
            if self._unknown_as_fallback and self._fallback_lang
            else None
        )
        logger.debug("Language fallback set: %s", tags.LANGUAGE_FALLBACK)

    def initialize(self):
        os.makedirs(self._cache_dir, exist_ok=True)

    def terminate(self):
        # Remove leftovers
        shutil.rmtree(self._cache_dir, ignore_errors=True)

    def query(self, path: str, languages, media_type):
        video = _get_memoized_video_container(path)

        try:
            streams = list(_filter_subtitles(video.get_subtitles()))
        except InvalidSource as error:
            logger.error("Error trying to get subtitles for %s: %s", video, error)

            self._blacklist.add(path)
            streams = []

        _rebuild_langs(streams)

        streams = _discard_possible_incomplete_subtitles(streams)

        if not streams:
            logger.debug("No subtitles found for container: %s", video)

        if self._hi_fallback:
            _check_hi_fallback(streams, languages)

        only_forced = all(lang.forced for lang in languages)
        also_forced = any(lang.forced for lang in languages)

        allowed_streams = []

        for stream in streams:
            if stream.codec_name not in self._included_codecs:
                logger.debug("Ignoring codec %s [%s]", stream, self._included_codecs)
                continue

            if stream.language not in languages:
                logger.debug("%r not in %r", stream.language, languages)
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

    @blacklist_on(ExtractionError)
    def download_subtitle(self, subtitle: EmbeddedSubtitle):
        try:
            path = self._get_subtitle_path(subtitle)
        except KeyError:  # TODO: add MustGetBlacklisted support
            logger.error("Couldn't get subtitle path")
            return None

        modifiers = _type_modifiers.get(subtitle.stream.codec_name) or set()
        logger.debug("Found modifiers for %s type: %s", subtitle.stream, modifiers)

        for mod in modifiers:
            logger.debug("Running %s modifier for %s", mod, path)
            try:
                mod(path, path)
            except Exception as error:
                logger.debug("'%s' raised running modifier", error)

        if os.path.exists(path):
            with open(path, "rb") as sub:
                subtitle.content = sub.read()
        else:
            logger.error("%s not found in filesystem", path)

    def _get_subtitle_path(self, subtitle: EmbeddedSubtitle):
        container = subtitle.container

        # Check if the container is not already in the instance
        if container.path not in self._cached_paths:
            # Extract all subittle streams to avoid reading the entire
            # container over and over
            subs = list(_filter_subtitles(container.get_subtitles()))

            extracted = container.copy_subtitles(
                subs,
                self._cache_dir,
                timeout=self._timeout,
                fallback_to_convert=True,
                basename_callback=_basename_callback,
                progress_callback=lambda d: logger.debug("Progress: %s", d),
            )
            # Add the extracted paths to the containter path key
            self._cached_paths[container.path] = extracted

        cached_path = self._cached_paths[container.path]
        # Get the subtitle file by index
        return cached_path[subtitle.stream.index]

    def _is_path_valid(self, path):
        if path in self._blacklist:
            logger.debug("Blacklisted path: %s", path)
            return False

        if not os.path.isfile(path):
            logger.debug("Inexistent file: %s", path)
            return False

        return True


class _MemoizedFFprobeVideoContainer(FFprobeVideoContainer):
    def get_subtitles(self, *args, **kwargs):
        return super().get_subtitles(*args, **kwargs)


@functools.lru_cache(maxsize=8096)
def _get_memoized_video_container(path: str):
    return _MemoizedFFprobeVideoContainer(path)


def _filter_subtitles(subtitles: List[FFprobeSubtitleStream]):
    for subtitle in subtitles:
        if subtitle.codec_name not in _ALLOWED_CODECS:
            logger.debug("Unallowed codec: %s", subtitle)
            continue

        if subtitle.tags.language_fallback is True and any(
            (subtitle.language == sub.language) and (subtitle.index != sub.index)
            for sub in subtitles
        ):
            logger.debug("Not using language fallback. Language already found")
            continue

        yield subtitle


def _check_hi_fallback(streams, languages):
    for language in languages:
        logger.debug("Checking HI fallback for '%r' language", language)

        streams_ = [
            stream for stream in streams if stream.language.alpha3 == language.alpha3 and stream.language.forced == language.forced
        ]
        if len(streams_) == 1 and streams_[0].disposition.hearing_impaired:
            stream_ = streams_[0]
            logger.debug(
                "HI fallback: updating %s HI to False (only subtitle found is HI)",
                stream_,
            )
            stream_.disposition.hearing_impaired = False
            stream_.disposition.generic = True
            stream_.language.hi = False

        elif all(stream.disposition.hearing_impaired for stream in streams_):
            for stream in streams_:
                logger.debug(
                    "HI fallback: updating %s HI to False (all subtitles are HI)",
                    stream,
                )
                stream.disposition.hearing_impaired = False
                stream.disposition.generic = True
                stream.language.hi = False

        elif any(stream.disposition.hearing_impaired for stream in streams_):
            logger.debug(
                "HI fallback not needed: %r (There's already one non-hi stream)",
                streams_,
            )
        else:
            logger.debug("Unknown use-case: %r. Not doing anything.", streams_)


def _rebuild_langs(streams):
    for stream in streams:
        kwargs = stream.disposition.language_kwargs()
        stream.language = Language.rebuild(stream.language, **kwargs)

        logger.debug("Rebuild language: %r", stream.language)


def _discard_possible_incomplete_subtitles(streams):
    """Check frame properties from subtitle streams in order to find
    supposedly incomplete subtitles"""
    try:
        max_frames = max(stream.tags.frames for stream in streams)
    except ValueError:
        return []

    # Blatantly assume there's nothing to discard as some ffprobe streams don't
    # have number_of_frames tags
    if not max_frames:
        logger.debug("No max frames. Assuming good subtitles.")
        return streams

    logger.debug("Checking possible incomplete subtitles (max frames: %d)", max_frames)

    valid_streams = []

    for stream in streams:
        # 500 < 1200
        if not stream.language.forced and stream.tags.frames < max_frames // 3:
            logger.debug(
                "Possible bad subtitle found: %s (%s frames - %s frames)",
                stream,
                stream.tags.frames,
                max_frames,
            )
            continue

        valid_streams.append(stream)

    return valid_streams


def _get_pretty_release_name(stream, container):
    bname = os.path.basename(container.path)
    return f"{os.path.splitext(bname)[0]}.{stream.suffix}"


def _basename_callback(path: str):
    path, ext = os.path.splitext(path)
    return hashlib.md5(path.encode()).hexdigest() + ext


# TODO: improve this
_SIGNS_LINE_RE = re.compile(r",([\w|_]{,15}(fx|karaoke))", flags=re.IGNORECASE)


def _clean_ass_subtitles(path, output_path):
    """An attempt to ignore extraneous lines from ASS anime subtitles. Experimental."""

    clean_lines = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for line in lines:
            if _SIGNS_LINE_RE.search(line) is None:
                clean_lines.append(line)

    logger.debug("Cleaned lines: %d", abs(len(lines) - len(clean_lines)))

    with open(output_path, "w", encoding="utf-8", errors="ignore") as f:
        f.writelines(clean_lines)
        logger.debug("Lines written to output path: %s", output_path)


_type_modifiers = {"ass": {_clean_ass_subtitles}}
