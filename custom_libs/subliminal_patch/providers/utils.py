from collections import namedtuple
from difflib import SequenceMatcher
import io
import logging
import os
import re
import tempfile
from typing import Iterable, Union
import zipfile

from guessit import guessit
import pysubs2
import rarfile
from subliminal.subtitle import fix_line_ending
from subliminal_patch.exceptions import MustGetBlacklisted
from subliminal_patch.core import Episode
from subliminal_patch.subtitle import guess_matches

from ._agent_list import FIRST_THOUSAND_OR_SO_USER_AGENTS

USER_AGENTS = FIRST_THOUSAND_OR_SO_USER_AGENTS

logger = logging.getLogger(__name__)


_MatchingSub = namedtuple("_MatchingSub", ("file", "priority", "context"))


def blacklist_on(*exc_types):
    "Raise MustGetBlacklisted if any of the exc_types are raised."

    def decorator(method):
        def wrapper(self, subtitle):
            try:
                return method(self, subtitle)
            except exc_types:
                logger.error("Sending blacklist exception", exc_info=True)
                raise MustGetBlacklisted(subtitle.id, subtitle.media_type)

        return wrapper

    return decorator


def _get_matching_sub(
    sub_names, forced=False, episode=None, episode_title=None, **kwargs
):
    guess_options = {"single_value": True}
    if episode is not None:
        guess_options["type"] = "episode"  # type: ignore

    matching_subs = []

    for sub_name in sub_names:
        if not forced and os.path.splitext(sub_name.lower())[0].endswith("forced"):
            logger.debug("Ignoring forced subtitle: %s", sub_name)
            continue

        # If it's a movie then get the first subtitle
        if episode is None and episode_title is None:
            logger.debug("Movie subtitle found: %s", sub_name)
            matching_subs.append(_MatchingSub(sub_name, 2, "Movie subtitle"))
            break

        guess = guessit(sub_name, options=guess_options)

        matched_episode_num = guess.get("episode")
        if not matched_episode_num:
            logger.debug("No episode number found in file: %s", sub_name)

        if episode_title is not None:
            from_name = _analize_sub_name(sub_name, episode_title)
            if from_name is not None:
                matching_subs.append(from_name)

        if episode == matched_episode_num:
            logger.debug("Episode matched from number: %s", sub_name)
            matching_subs.append(_MatchingSub(sub_name, 2, "Episode number matched"))

    if matching_subs:
        matching_subs.sort(key=lambda x: x.priority, reverse=True)
        logger.debug("Matches: %s", matching_subs)
        return matching_subs[0].file
    else:
        logger.debug("Nothing matched")
        return None


def _analize_sub_name(sub_name: str, title_: str):
    titles = re.split(r"[\s_\.\+]?[.-][\s_\.\+]?", os.path.splitext(sub_name)[0])

    for title in titles:
        title = title.strip()
        ratio = SequenceMatcher(None, title.lower(), title_.lower()).ratio()

        if ratio > 0.85:
            logger.debug(
                "Episode title matched: '%s' -> '%s' [%s]", title, sub_name, ratio
            )

            # Avoid false positives with short titles
            if len(title_) > 4 and ratio >= 0.98:
                return _MatchingSub(sub_name, 3, "Perfect title ratio")

            return _MatchingSub(sub_name, 1, "Normal title ratio")

    logger.debug("No episode title matched from file: %s", sub_name)
    return None


def get_subtitle_from_archive(
    archive, forced=False, episode=None, get_first_subtitle=False, **kwargs
):
    "Get subtitle from Rarfile/Zipfile object. Return None if nothing is found."
    subs_in_archive = [
        name
        for name in archive.namelist()
        if name.endswith((".srt", ".sub", ".ssa", ".ass"))
    ]

    if not subs_in_archive:
        logger.info("No subtitles found in archive")
        return None

    logger.debug("Subtitles in archive: %s", subs_in_archive)

    if len(subs_in_archive) == 1 or get_first_subtitle:
        logger.debug("Getting first subtitle in archive: %s", subs_in_archive)
        return fix_line_ending(archive.read(subs_in_archive[0]))

    matching_sub = _get_matching_sub(subs_in_archive, forced, episode, **kwargs)

    if matching_sub is not None:
        logger.info("Using %s from archive", matching_sub)
        return fix_line_ending(archive.read(matching_sub))

    logger.debug("No subtitle found in archive")
    return None


def is_episode(content):
    return "episode" in guessit(content, {"type": "episode"})


_ENCS = ("utf-8", "ascii", "iso-8859-1", "iso-8859-2", "iso-8859-5", "cp1252")


def _zip_from_subtitle_file(content):
    with tempfile.NamedTemporaryFile(prefix="spsub", suffix=".srt") as tmp_f:
        tmp_f.write(content)
        sub = None
        for enc in _ENCS:
            try:
                logger.debug("Trying %s encoding", enc)
                sub = pysubs2.load(tmp_f.name, encoding=enc)
            except Exception as error:
                logger.debug("%s: %s", type(error).__name__, error)
                continue
            else:
                break

        if sub is not None:
            logger.debug("Identified subtitle file: %s", sub)
            zip_obj = zipfile.ZipFile(io.BytesIO(), mode="x")
            zip_obj.write(tmp_f.name, os.path.basename(tmp_f.name))
            return zip_obj

        logger.debug("Couldn't load subtitle file")
        return None


def get_archive_from_bytes(content: bytes):
    """Get RarFile/ZipFile object from bytes. A ZipFile instance will be returned
    if a subtitle-like stream is found. Return None if something else is found."""
    archive_stream = io.BytesIO(content)

    if rarfile.is_rarfile(archive_stream):
        logger.debug("Identified rar archive")
        return rarfile.RarFile(archive_stream)
    elif zipfile.is_zipfile(archive_stream):
        logger.debug("Identified zip archive")
        return zipfile.ZipFile(archive_stream)

    logger.debug("No compression format found. Trying with subtitle-like files")
    return _zip_from_subtitle_file(content)


def update_matches(
    matches,
    video,
    release_info: Union[str, Iterable[str]],
    split="\n",
    **guessit_options,
):
    """Update matches set from release info string or Iterable.

    Use the split parameter to iterate over the set delimiter; set None to avoid split.
    """

    guessit_options["type"] = "episode" if isinstance(video, Episode) else "movie"

    logger.debug("Guessit options to update matches: %s", guessit_options)

    if isinstance(release_info, str):
        release_info = release_info.split(split)

    for release in release_info:
        for release_split in release.split(split):
            logger.debug("Updating matches from release info: %s", release)
            matches |= guess_matches(
                video, guessit(release_split.strip(), guessit_options)
            )
            logger.debug("New matches: %s", matches)

    return matches
