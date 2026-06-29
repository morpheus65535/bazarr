# -*- coding: utf-8 -*-
from __future__ import absolute_import

import codecs
import logging
import re
from hashlib import sha1
from random import randint

from dogpile.cache.api import NO_VALUE
from dogpile.cache.exception import RegionNotConfigured
from requests import Session
from subliminal.cache import region
from subliminal.video import Episode
from subliminal.video import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.subtitle import guess_matches
from guessit import guessit
from subzero.language import Language

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST


logger = logging.getLogger(__name__)

_BASE_URL = "https://vladoon.mooo.com/subs"
_SEARCH_URL = _BASE_URL + "/search-subtitles"
_DOWNLOAD_URL = _BASE_URL + "/download/{id}"


def _episode_token(video):
    if not isinstance(video, Episode):
        return None

    return "S%02dE%02d" % (video.season, video.episode)


def _episode_tuple(text):
    if not text:
        return None

    match = re.search(r"\b[Ss](\d{1,2})[Ee](\d{1,2})\b", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r"\b(\d{1,2})x(\d{1,2})\b", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    return None


def _search_query(video):
    if isinstance(video, Episode):
        return "%s %s" % (video.series.strip(), _episode_token(video))

    return video.title.strip()


def _cache_get(cache_key):
    try:
        return region.get(cache_key)
    except RegionNotConfigured:
        return NO_VALUE


def _cache_set(cache_key, response):
    try:
        region.set(cache_key, response)
    except RegionNotConfigured:
        pass


def _cache_delete(cache_key):
    try:
        region.delete(cache_key)
    except RegionNotConfigured:
        pass


def _release_names(item):
    releases = item.get("release_names") or []
    if isinstance(releases, str):
        return [releases]
    return releases


def _matches_movie(item, video):
    if not isinstance(video, Movie):
        return True

    if item.get("type") and item.get("type") != "movie":
        return False

    if video.imdb_id and item.get("imdb_id"):
        return video.imdb_id == item.get("imdb_id")

    return True


def _matches_episode(item, video):
    if not isinstance(video, Episode):
        return True

    if item.get("type") and item.get("type") != "tv":
        return False

    if video.series_imdb_id and item.get("imdb_id") and video.series_imdb_id != item.get("imdb_id"):
        return False

    season = item.get("season")
    episode = item.get("episode")
    if season == video.season and episode == video.episode:
        return True

    wanted = (video.season, video.episode)
    for release in _release_names(item):
        if _episode_tuple(release) == wanted:
            return True

    if item.get("episode_type") == "season" and season == video.season:
        return True

    return False


class VladoonMoooSubtitle(Subtitle):
    provider_name = "vladoonmooo"

    def __init__(
        self,
        language,
        page_link,
        file_id,
        title,
        release_names,
        imdb_id=None,
        media_type=None,
        video=None,
        uploader=None,
    ):
        super(VladoonMoooSubtitle, self).__init__(language)
        self.page_link = page_link
        self.file_id = str(file_id)
        self.title = title or ""
        self.release_names = release_names or []
        self.release_info = "\n".join(self.release_names) or self.title
        self.imdb_id = imdb_id
        self.media_type = media_type
        self.video = video
        self.uploader = uploader
        self.matches = set()

    @property
    def id(self):
        return self.file_id

    def make_picklable(self):
        self.content = None
        self._is_valid = False
        return self

    def get_matches(self, video):
        self.matches = set()
        guess_type = "episode" if isinstance(video, Episode) else "movie"

        self.matches |= guess_matches(video, guessit(self.title, {"type": guess_type}))
        update_matches(self.matches, video, self.release_info, split="\n")

        if isinstance(video, Movie) and video.imdb_id and self.imdb_id == video.imdb_id:
            self.matches.add("imdb_id")
        if isinstance(video, Episode) and video.series_imdb_id and self.imdb_id == video.series_imdb_id:
            self.matches.add("imdb_id")

        return self.matches


class VladoonMoooProvider(Provider):
    languages = {Language("bul")}
    video_types = (Episode, Movie)

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers["Accept"] = "application/json"
        self.session.headers["Referer"] = _BASE_URL + "/"

    def terminate(self):
        self.session.close()

    def query(self, language, video):
        subtitles = []
        params = {"q": _search_query(video)}

        logger.debug("Searching Vladoon Mooo subtitles: %r", params)
        response = self.session.get(_SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()

        for item in (response.json() or {}).get("results") or []:
            if not _matches_movie(item, video):
                continue
            if not _matches_episode(item, video):
                continue

            file_id = item.get("id")
            if file_id is None:
                continue

            subtitle = VladoonMoooSubtitle(
                language=language,
                page_link=_DOWNLOAD_URL.format(id=file_id),
                file_id=file_id,
                title=item.get("original_title") or item.get("title"),
                release_names=_release_names(item),
                imdb_id=item.get("imdb_id"),
                media_type="episode" if isinstance(video, Episode) else "movie",
                video=video,
                uploader=item.get("uploaded_by"),
            )
            logger.debug("Found Vladoon Mooo subtitle: %s", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return [subtitle for language in languages for subtitle in self.query(language, video)]

    def download_subtitle(self, subtitle):
        logger.debug("Downloading Vladoon Mooo subtitle %r", subtitle.page_link)
        cache_key = sha1(subtitle.page_link.encode("utf-8")).digest()
        response = _cache_get(cache_key)

        if response is NO_VALUE:
            response = self.session.get(subtitle.page_link, timeout=30)
            response.raise_for_status()
            _cache_set(cache_key, response)
        else:
            logger.debug(
                "Using cache file %s",
                codecs.encode(cache_key, "hex_codec").decode("utf-8"),
            )

        archive = get_archive_from_bytes(response.content)
        if archive is None:
            logger.error("Ignore unsupported Vladoon Mooo archive %r", response.headers)
            _cache_delete(cache_key)
            return

        subtitle.content = get_subtitle_from_archive(
            archive,
            episode=subtitle.video.episode if isinstance(subtitle.video, Episode) else None,
            get_first_subtitle=not isinstance(subtitle.video, Episode),
        )
        if not subtitle.content:
            logger.error("No subtitle found in Vladoon Mooo archive %r", response.headers)
            _cache_delete(cache_key)
