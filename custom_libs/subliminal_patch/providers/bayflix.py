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

_BASE_URL = "https://bayflix.sb"
_SEARCH_URL = _BASE_URL + "/api/subtitles/search"
_DOWNLOAD_URL = _BASE_URL + "/api/subtitles/download/{id}"


def _extract_fps(description):
    match = re.search(r"FPS:\s*([\d.]+)", description or "", re.I)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def _extract_cds(description):
    match = re.search(r"CDs?:\s*(\d+)", description or "", re.I)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


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


def _wanted_episode(video):
    if not isinstance(video, Episode):
        return None

    return video.season, video.episode


def _matches_episode(item, video):
    wanted = _wanted_episode(video)
    if wanted is None:
        return True

    for release in item.get("release_name") or []:
        if _episode_tuple(release) == wanted:
            return True

    for line in (item.get("description") or "").splitlines():
        if _episode_tuple(line) == wanted:
            return True

    return False


def _matches_movie_year(item, video):
    if not isinstance(video, Movie) or not video.year:
        return True

    release_year = (item.get("release_date") or "")[:4]
    if not release_year:
        return True

    try:
        return abs(int(release_year) - int(video.year)) <= 1
    except ValueError:
        return True


def _search_title(video):
    if isinstance(video, Episode):
        return video.series.strip()

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


class BayflixSubtitle(Subtitle):
    provider_name = "bayflix"

    def __init__(
        self,
        language,
        page_link,
        file_id,
        title,
        release_names,
        year=None,
        media_type=None,
        video=None,
        fps=None,
        num_cds=None,
    ):
        super(BayflixSubtitle, self).__init__(language)
        self.page_link = page_link
        self.file_id = str(file_id)
        self.title = title or ""
        self.release_names = release_names or []
        self.release_info = "\n".join(self.release_names) or self.title
        self.year = year
        self.media_type = media_type
        self.video = video
        self.fps = fps
        self.num_cds = num_cds
        self.matches = set()

    @property
    def id(self):
        return self.file_id

    def get_fps(self):
        return self.fps

    def make_picklable(self):
        self.content = None
        self._is_valid = False
        return self

    def get_matches(self, video):
        self.matches = set()
        guess_type = "episode" if isinstance(video, Episode) else "movie"

        self.matches |= guess_matches(video, guessit(self.title, {"type": guess_type}))
        update_matches(self.matches, video, self.release_info, split="\n")

        if isinstance(video, Movie) and video.year and self.year == video.year:
            self.matches.add("year")

        return self.matches


class BayflixProvider(Provider):
    languages = {Language("bul")}
    video_types = (Episode, Movie)

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers["Accept"] = "application/json, text/plain, */*"
        self.session.headers["Accept-Language"] = "en-US,en;q=0.9"
        self.session.headers["Referer"] = _BASE_URL + "/"

    def terminate(self):
        self.session.close()

    def query(self, language, video):
        subtitles = []
        params = {"title": _search_title(video)}

        logger.debug("Searching Bayflix subtitles: %r", params)
        response = self.session.get(_SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()

        for item in response.json() or []:
            if not _matches_movie_year(item, video):
                continue
            if not _matches_episode(item, video):
                continue

            file_id = item.get("_id")
            if not file_id:
                continue

            page_link = item.get("subtitle_link") or _DOWNLOAD_URL.format(id=file_id)
            release_names = item.get("release_name") or []
            if isinstance(release_names, str):
                release_names = [release_names]

            release_year = (item.get("release_date") or "")[:4]
            try:
                release_year = int(release_year) if release_year else None
            except ValueError:
                release_year = None

            subtitle = BayflixSubtitle(
                language=language,
                page_link=page_link,
                file_id=file_id,
                title=item.get("title"),
                release_names=release_names,
                year=release_year,
                media_type=item.get("media_type"),
                video=video,
                fps=_extract_fps(item.get("description")),
                num_cds=_extract_cds(item.get("description")),
            )
            logger.debug("Found Bayflix subtitle: %s", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return [subtitle for language in languages for subtitle in self.query(language, video)]

    def download_subtitle(self, subtitle):
        logger.debug("Downloading Bayflix subtitle %r", subtitle.page_link)
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
            logger.error("Ignore unsupported Bayflix archive %r", response.headers)
            _cache_delete(cache_key)
            return

        subtitle.content = get_subtitle_from_archive(
            archive,
            episode=subtitle.video.episode if isinstance(subtitle.video, Episode) else None,
            get_first_subtitle=not isinstance(subtitle.video, Episode),
        )
        if not subtitle.content:
            logger.error("No subtitle found in Bayflix archive %r", response.headers)
            _cache_delete(cache_key)
