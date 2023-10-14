# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import re
import time

from requests import Session
from six.moves import range
from subliminal import __short_version__
from subliminal.providers import ParserBeautifulSoup
from subliminal.video import Episode
from subliminal.video import Movie
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

_SERVER_URL = "https://www.subdivx.com"

_CLEAN_TITLE_RES = [
    (r"subt[ií]tulos de", ""),
    (r"´|`", "'"),
    (r" {2,}", " "),
]

_SPANISH_RE = re.compile(r"españa|ib[eé]rico|castellano|gallego|castilla")
_YEAR_RE = re.compile(r"(\(\d{4}\))")
_YEAR_RE_INT = re.compile(r"\((\d{4})\)")


_SERIES_RE = re.compile(
    r"\(?\d{4}\)?|(s\d{1,2}(e\d{1,2})?|(season|temporada)\s\d{1,2}).*?$",
    flags=re.IGNORECASE,
)
_EPISODE_NUM_RE = re.compile(r"[eE](?P<x>\d{1,2})")
_SEASON_NUM_RE = re.compile(
    r"(s|(season|temporada)\s)(?P<x>\d{1,2})", flags=re.IGNORECASE
)
_EPISODE_YEAR_RE = re.compile(r"\((?P<x>(19\d{2}|20[0-2]\d))\)")
_UNSUPPORTED_RE = re.compile(
    r"(\)?\d{4}\)?|[sS]\d{1,2})\s.{,3}(extras|forzado(s)?|forced)", flags=re.IGNORECASE
)

logger = logging.getLogger(__name__)


class SubdivxSubtitle(Subtitle):
    provider_name = "subdivx"
    hash_verifiable = False

    def __init__(
        self, language, video, page_link, title, description, uploader, download_url
    ):
        super(SubdivxSubtitle, self).__init__(
            language, hearing_impaired=False, page_link=page_link
        )
        self.video = video

        self.download_url = download_url
        self.uploader = uploader

        self._title = str(title).strip()
        self._description = str(description).strip()

        self.release_info = self._title

        if self._description:
            self.release_info += " | " + self._description

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # already matched within provider
            matches.update(["title", "series", "season", "episode", "year"])

        # movie
        elif isinstance(video, Movie):
            # already matched within provider
            matches.update(["title", "year"])

        update_matches(matches, video, self._description)

        # Don't lowercase; otherwise it will match a lot of false positives
        if video.release_group and video.release_group in self._description:
            matches.add("release_group")

        return matches


_IDUSER_COOKIE = "VkZaRk9WQlJQVDA12809"


class SubdivxSubtitlesProvider(Provider):
    provider_name = "subdivx"
    hash_verifiable = False
    languages = {Language("spa", "MX")} | {Language.fromalpha2("es")}
    video_types = (Episode, Movie)
    subtitle_class = SubdivxSubtitle

    multi_result_throttle = 2

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = f"Subliminal/{__short_version__}"
        self.session.cookies.update({"iduser_cookie": _IDUSER_COOKIE})

    def terminate(self):
        self.session.close()

    def query(self, video, languages):
        subtitles = []

        if isinstance(video, Episode):
            # TODO: cache pack queries (TV SHOW S01).
            # Too many redundant server calls.

            for query in (
                f"{video.series} S{video.season:02}E{video.episode:02}",
                f"{video.series} S{video.season:02}",
            ):
                subtitles += self._handle_multi_page_search(query, video)

            # Try only with series title
            if len(subtitles) <= 5:
                subtitles += self._handle_multi_page_search(video.series, video, 1)

            # Try with episode title as last resort
            if not subtitles and video.title != video.series:
                subtitles += self._handle_multi_page_search(video.title, video, 1)
        else:
            for query in (video.title, f"{video.title} ({video.year})"):
                subtitles += self._handle_multi_page_search(query, video)
                # Second query is a fallback
                if subtitles:
                    break

        return subtitles

    def _handle_multi_page_search(self, query, video, max_loops=2):
        params = {
            "buscar2": query,
            "accion": "5",
            "masdesc": "",
            "subtitulos": "1",
            "realiza_b": "1",
            "pg": 1,
        }
        logger.debug("Query: %s", query)

        loops = 1
        max_loops_not_met = True

        while max_loops_not_met:
            max_loops_not_met = loops < max_loops

            page_subtitles, last_page = self._get_page_subtitles(params, video)

            logger.debug("Yielding %d subtitles [loop #%d]", len(page_subtitles), loops)
            yield from page_subtitles

            if last_page:
                logger.debug("Last page for '%s' query. Breaking loop", query)
                break

            loops += 1

            params["pg"] += 1  # search next page
            time.sleep(self.multi_result_throttle)

        if not max_loops_not_met:
            logger.debug("Max loops limit exceeded (%d)", max_loops)

    def _get_page_subtitles(self, params, video):
        search_link = f"{_SERVER_URL}/index.php"
        response = self.session.get(
            search_link, params=params, allow_redirects=True, timeout=20
        )

        try:
            page_subtitles, last_page = self._parse_subtitles_page(video, response)
        except Exception as error:
            logger.error(f"Error parsing subtitles list: {error}")
            return []

        return page_subtitles, last_page

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def download_subtitle(self, subtitle):
        # download the subtitle
        logger.debug("Downloading subtitle %r", subtitle)

        response = self.session.get(
            subtitle.download_url,
            headers={"Referer": _SERVER_URL},
            timeout=30,
        )
        response.raise_for_status()

        # TODO: add MustGetBlacklisted support

        archive = get_archive_from_bytes(response.content)
        if archive is None:
            raise APIThrottled("Unknwon compressed format")

        episode = None
        if isinstance(subtitle.video, Episode):
            episode = subtitle.video.episode

        subtitle.content = get_subtitle_from_archive(archive, episode=episode)

    def _parse_subtitles_page(self, video, response):
        subtitles = []

        page_soup = ParserBeautifulSoup(
            response.content.decode("utf-8", "ignore"), ["lxml", "html.parser"]
        )
        title_soups = page_soup.find_all("div", {"id": "menu_detalle_buscador"})
        body_soups = page_soup.find_all("div", {"id": "buscador_detalle"})

        title_checker = _check_episode if isinstance(video, Episode) else _check_movie

        for subtitle in range(0, len(title_soups)):
            title_soup, body_soup = title_soups[subtitle], body_soups[subtitle]
            # title
            title = _clean_title(title_soup.find("a").text)

            if _UNSUPPORTED_RE.search(title):
                logger.debug("Skipping unsupported subtitles: %s", title)
                continue

            if not title_checker(video, title):
                continue

            # Data
            datos = body_soup.find("div", {"id": "buscador_detalle_sub_datos"}).text
            # Ignore multi-disc and non-srt subtitles
            if not any(item in datos for item in ("Cds:</b> 1", "SubRip")):
                continue

            # description
            sub_details = body_soup.find("div", {"id": "buscador_detalle_sub"}).text
            description = sub_details.replace(",", " ")

            # language
            spain = (
                "/pais/7.gif" in datos
                or _SPANISH_RE.search(description.lower()) is not None
            )
            language = Language.fromalpha2("es") if spain else Language("spa", "MX")

            # uploader
            uploader = body_soup.find("a", {"class": "link1"}).text
            download_url = _get_download_url(body_soup)
            page_link = title_soup.find("a")["href"]

            subtitle = self.subtitle_class(
                language, video, page_link, title, description, uploader, download_url
            )

            logger.debug("Found subtitle %r", subtitle)
            subtitles.append(subtitle)

        return subtitles, len(title_soups) < 100


def _clean_title(title):
    """
    Normalize apostrophes and spaces to avoid matching problems
    (e.g. Subtitulos de  Carlito´s  Way -> Carlito's Way)
    """
    for og, new in _CLEAN_TITLE_RES:
        title = re.sub(og, new, title, flags=re.IGNORECASE)

    return title


def _get_download_url(data):
    try:
        return [
            a_.get("href")
            for a_ in data.find_all("a")
            if "bajar.php" in a_.get("href", "n/a")
        ][0]
    except IndexError:
        return None


def _check_episode(video, title):
    ep_num = _EPISODE_NUM_RE.search(title)
    season_num = _SEASON_NUM_RE.search(title)
    year = _EPISODE_YEAR_RE.search(title)

    # Only check if both video and Subdivx's title have year metadata
    if year is not None and video.year:
        year = int(year.group("x"))
        # Tolerancy of 1 year difference
        if abs(year - (video.year or 0)) > 1:
            logger.debug("Series year doesn't match: %s", title)
            return False

    # Include matches where the episode title is present
    if (
        video.series.lower() in title.lower()
        and (video.title or "").lower() in title.lower()
    ):
        logger.debug("Episode title found in title: %s ~ %s", video.title, title)
        return True

    if season_num is None:
        logger.debug("Not a season/episode: %s", title)
        return False

    season_num = int(season_num.group("x"))

    if ep_num is not None:
        ep_num = int(ep_num.group("x"))

    ep_matches = (
        (video.episode == ep_num) or (ep_num is None)
    ) and season_num == video.season

    series_title = _SERIES_RE.sub("", title).strip()

    distance = abs(len(series_title) - len(video.series))

    series_matched = distance < 4 and ep_matches

    logger.debug(
        "Series matched? %s [%s -> %s] [title distance: %d]",
        series_matched,
        video,
        title,
        distance,
    )

    return series_matched


def _check_movie(video, title):
    try:
        year = int(_YEAR_RE_INT.search(title).group(1))  # type: ignore
    except (AttributeError, ValueError):
        logger.debug("Year not found in title (%s). Discarding movie", title)
        return False

    if video.year and abs(year - video.year) > 1:
        logger.debug("Year not matching: %s -> %s", year, video.year)
        return False

    aka_split = re.split("aka", title, flags=re.IGNORECASE)

    alt_title = None
    if len(aka_split) == 2:
        alt_title = aka_split[-1].strip()

    try:
        actual_movie_title = _YEAR_RE.split(title)[0].strip()
    except IndexError:
        return False

    all_titles = [
        v_title.lower() for v_title in [video.title, *video.alternative_titles]
    ]

    return (
        actual_movie_title.lower() in all_titles
        or (alt_title or "").lower() in all_titles
    )
