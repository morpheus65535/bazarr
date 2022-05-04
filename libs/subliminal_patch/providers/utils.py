import io
import logging
import os
import zipfile

import rarfile

from guessit import guessit

from subliminal.subtitle import fix_line_ending

from subliminal_patch.core import Episode
from subliminal_patch.subtitle import guess_matches

from ._agent_list import FIRST_THOUSAND_OR_SO_USER_AGENTS


logger = logging.getLogger(__name__)


def _get_matching_sub(sub_names, forced=False, episode=None):
    matching_sub = None

    guess_options = {"single_value": True}
    if episode is not None:
        guess_options["type"] = "episode"  # type: ignore

    for sub_name in sub_names:
        if not forced and os.path.splitext(sub_name.lower())[0].endswith("forced"):
            logger.debug("Ignoring forced subtitle: %s", sub_name)
            continue

        # If it's a movie then get the first subtitle
        if episode is None:
            logger.debug("Movie subtitle found: %s", sub_name)
            matching_sub = sub_name
            break

        guess = guessit(sub_name, options=guess_options)

        if guess.get("episode") is None:
            logger.debug("No episode info found in file: %s", sub_name)
            continue

        if episode == guess["episode"]:
            logger.debug("Episode matched: %s", sub_name)
            matching_sub = sub_name
            break

        logger.debug("Ignoring incorrect episode: %s", sub_name)

    return matching_sub


def get_subtitle_from_archive(
    archive, forced=False, episode=None, get_first_subtitle=False
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

    matching_sub = _get_matching_sub(subs_in_archive, forced, episode)

    if matching_sub is not None:
        logger.info("Using %s from archive", matching_sub)
        return fix_line_ending(archive.read(matching_sub))

    logger.debug("No subtitle found in archive")
    return None


def get_archive_from_bytes(content: bytes):
    """Get RarFile/ZipFile object from bytes. Return None is something else
    is found."""
    # open the archive
    archive_stream = io.BytesIO(content)
    if rarfile.is_rarfile(archive_stream):
        logger.debug("Identified rar archive")
        return rarfile.RarFile(archive_stream)
    elif zipfile.is_zipfile(archive_stream):
        logger.debug("Identified zip archive")
        return zipfile.ZipFile(archive_stream)

    logger.debug("Unknown compression format")
    return None


def update_matches(matches, video, release_info: str, **guessit_options):
    "Update matches set from release info string. New lines are iterated."
    guessit_options["type"] = "episode" if isinstance(video, Episode) else "movie"
    logger.debug("Guessit options to update matches: %s", guessit_options)

    for release in release_info.split("\n"):
        logger.debug("Updating matches from release info: %s", release)
        matches |= guess_matches(video, guessit(release.strip(), guessit_options))
        logger.debug("New matches: %s", matches)

    return matches
