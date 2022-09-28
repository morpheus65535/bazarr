# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re
import time

from subzero.language import Language
from requests import Session

from subliminal import __short_version__
from subliminal.providers import ParserBeautifulSoup
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import APIThrottled
from six.moves import range
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches

_SERVER_URL = "https://www.subdivx.com"

_CLEAN_TITLE_RES = [
    (r"subt[ií]tulos de", ""),
    (r"´|`", "'"),
    (r" {2,}", " "),
]
_SPANISH_RE = re.compile(r"españa|ib[eé]rico|castellano|gallego|castilla")

_YEAR_RE = re.compile(r"(\(\d{4}\))")

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

        self.release_info = str(title)
        self.description = str(description).strip()

        if self.description:
            self.release_info += " | " + self.description

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # already matched in search query
            matches.update(["title", "series", "season", "episode", "year"])

        # movie
        elif isinstance(video, Movie):
            # already matched in search query
            matches.update(["title", "year"])

        update_matches(matches, video, self.description)

        # Don't lowercase; otherwise it will match a lot of false positives
        if video.release_group and video.release_group in self.description:
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
            for query in (
                f"{video.series} S{video.season:02}E{video.episode:02}",
                f"{video.series} S{video.season:02}",
            ):
                subtitles += self._handle_multi_page_search(query, video)
        else:
            for query in (video.title, f"{video.title} ({video.year})"):
                subtitles += self._handle_multi_page_search(query, video)
                # Second query is a fallback
                if subtitles:
                    break

        return subtitles

    def _handle_multi_page_search(self, query, video, max_loops=3):
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
            loops += 1
            max_loops_not_met = loops < max_loops

            page_subtitles = self._get_page_subtitles(params, video)

            logger.debug("Yielding %d subtitles", len(page_subtitles))
            yield from page_subtitles

            if len(page_subtitles) < 100:
                break  # this is the last page

            params["pg"] += 1  # search next page
            time.sleep(self.multi_result_throttle)

    def _get_page_subtitles(self, params, video):
        search_link = f"{_SERVER_URL}/index.php"
        response = self.session.get(
            search_link, params=params, allow_redirects=True, timeout=20
        )

        try:
            page_subtitles = self._parse_subtitles_page(video, response)
        except Exception as error:
            logger.error(f"Error parsing subtitles list: {error}")
            return []

        return page_subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def download_subtitle(self, subtitle):
        # download the subtitle
        logger.info("Downloading subtitle %r", subtitle)

        # download zip / rar file with the subtitle
        response = self.session.get(
            subtitle.download_url,
            headers={"Referer": subtitle.page_link},
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
        episode = isinstance(video, Episode)

        for subtitle in range(0, len(title_soups)):
            title_soup, body_soup = title_soups[subtitle], body_soups[subtitle]
            # title
            title = _clean_title(title_soup.find("a").text)

            # Forced subtitles are not supported
            if title.lower().rstrip().endswith(("forzado", "forzados")):
                logger.debug("Skipping forced subtitles: %s", title)
                continue

            # Check movie title (if the video is a movie)
            if not episode and not _check_movie(video, title):
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

        return subtitles


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


def _check_movie(video, title):
    if str(video.year) not in title:
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
