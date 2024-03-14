# coding=utf-8

from __future__ import absolute_import
import re
import time
import logging
import traceback
import types
import os
from six.moves.http_client import ResponseNotReady

from guessit import guessit
from subliminal.exceptions import ServiceUnavailable, DownloadLimitExceeded, ConfigurationError, AuthenticationError
from subliminal.providers.opensubtitles import Unauthorized
from subliminal.subtitle import fix_line_ending
from subliminal_patch.exceptions import TooManyRequests

logger = logging.getLogger(__name__)


clean_whitespace_re = re.compile(r'\s+')


class PunctuationMixin(object):
    """
    provider mixin

    fixes show ids for stuff like "Mr. Petterson", as our matcher already sees it as "Mr Petterson" but addic7ed doesn't
    """

    def clean_punctuation(self, s):
        return s.replace(".", "").replace(":", "").replace("'", "").replace("&", "").replace("-", "")

    def clean_whitespace(self, s):
        return clean_whitespace_re.sub("", s)

    def full_clean(self, s):
        return self.clean_whitespace(self.clean_punctuation(s))


class ProviderRetryMixin(object):
    def retry(self, f, amount=2, exc=Exception, retry_timeout=10):
        i = 0
        while i <= amount:
            try:
                return f()
            except (Unauthorized, ServiceUnavailable, TooManyRequests, DownloadLimitExceeded, ResponseNotReady,
                    ConfigurationError, AuthenticationError):
                raise
            except exc:
                formatted_exc = traceback.format_exc()
                i += 1
                if i == amount:
                    raise

            logger.debug(u"Retrying %s, try: %i/%i, exception: %s" % (self.__class__.__name__, i, amount, formatted_exc))
            time.sleep(retry_timeout)


class ProviderSubtitleArchiveMixin(object):
    """
    handles ZipFile and RarFile archives
    needs subtitle.episode, subtitle.season, subtitle.matches, subtitle.releases and subtitle.asked_for_episode to work
    """
    def get_subtitle_from_archive(self, subtitle, archive):
        # extract subtitle's content
        subs_in_archive = []
        for name in archive.namelist():
            for ext in (".srt", ".sub", ".ssa", ".ass"):
                if name.endswith(ext):
                    subs_in_archive.append(name)

        # select the correct subtitle file
        matching_sub = None
        subs_unsure = []
        subs_fallback = []
        if len(subs_in_archive) == 1:
            matching_sub = subs_in_archive[0]
        else:
            logger.debug("Subtitles in archive: %s", subs_in_archive)

            for sub_name in subs_in_archive:
                guess = guessit(sub_name)

                sub_name_lower = sub_name.lower()

                # consider subtitle valid if:
                # - episode and season match
                # - source matches (if it was matched before)
                # - release group matches (and we asked for one and it was matched, or it was not matched)
                # - not asked for forced and "forced" not in filename
                is_episode = subtitle.asked_for_episode

                if not subtitle.language.forced:
                    base, ext = os.path.splitext(sub_name_lower)
                    if base.endswith("forced") or "forced" in guess.get("release_group", ""):
                        continue

                episodes = guess.get("episode")

                if not isinstance(episodes, list):
                    episodes = [episodes]

                episode_matches = False
                if is_episode:
                    episode_matches = episodes is not None and any(subtitle.episode == epi for epi in episodes)

                if not is_episode or (
                        (
                                subtitle.episode in episodes
                                or (subtitle.is_pack and subtitle.asked_for_episode in episodes)
                        ) and guess.get("season") == subtitle.season):

                    source_matches = True
                    wanted_source_but_not_found = False

                    if "source" in subtitle.matches:
                        source_matches = False
                        if isinstance(subtitle.releases, list):
                            releases = ",".join(subtitle.releases).lower()
                        else:
                            releases = subtitle.releases.lower()

                        if "source" not in guess:
                            wanted_source_but_not_found = True

                        else:
                            formats = guess["source"]
                            if not isinstance(formats, list):
                                formats = [formats]

                            for f in formats:
                                source_matches = f.lower() in releases
                                if source_matches:
                                    break

                    release_group_matches = True
                    if subtitle.is_pack or (subtitle.asked_for_release_group and
                                            ("release_group" in subtitle.matches or
                                             "hash" in subtitle.matches)):

                        if subtitle.asked_for_release_group:
                            asked_for_rlsgrp = subtitle.asked_for_release_group.lower()

                            if asked_for_rlsgrp:
                                release_group_matches = False
                                if asked_for_rlsgrp in sub_name_lower:
                                    release_group_matches = True

                    if not is_episode and release_group_matches and source_matches:
                        matching_sub = sub_name
                        break

                    if is_episode and episode_matches:
                        matching_sub = sub_name
                        break

                    elif release_group_matches and wanted_source_but_not_found:
                        subs_unsure.append(sub_name)
                    else:
                        subs_fallback.append(sub_name)


        if not matching_sub and not subs_unsure and not subs_fallback:
            logger.error("None of expected subtitle found in archive")
            return

        elif matching_sub:
            logger.debug("Matched subtitle found: %s", matching_sub)

        elif subs_unsure:
            matching_sub = subs_unsure[0]

        elif subs_fallback:
            matching_sub = subs_fallback[0]

        logger.info(u"Using %s from the archive", matching_sub)
        return fix_line_ending(archive.read(matching_sub))
