# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import logging
import os
import re
import time
import zipfile

import rarfile
from subzero.language import Language
from requests import Session

from subliminal import __short_version__
from subliminal.exceptions import ServiceUnavailable
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending, guess_matches
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import APIThrottled
from six.moves import range
from subliminal_patch.score import get_scores
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from guessit import guessit

_SERVER_URL = "https://www.subdivx.com"

_CLEAN_TITLE_RES = [
    (r"subt[ií]tulos de", ""),
    (r"´|`", "'"),
    (r" {2,}", " "),
]

_YEAR_RE = re.compile(r"(\(\d{4}\))")
_AKA_RE = re.compile("aka")

logger = logging.getLogger(__name__)


class SubdivxSubtitle(Subtitle):
    provider_name = "subdivx"
    hash_verifiable = False

    def __init__(self, language, video, page_link, title, description, uploader):
        super(SubdivxSubtitle, self).__init__(
            language, hearing_impaired=False, page_link=page_link
        )
        self.video = video
        self.title = title
        self.description = description
        self.uploader = uploader
        self.release_info = self.title
        if self.description and self.description.strip():
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

        # Special string comparisons are unnecessary. Guessit can match keys
        # from any string and find even more keywords.
        matches |= guess_matches(
            video,
            guessit(
                self.description,
                {"type": "episode" if isinstance(video, Episode) else "movie"},
            ),
        )

        return matches


class SubdivxSubtitlesProvider(Provider):
    provider_name = "subdivx"
    hash_verifiable = False
    languages = {Language("spa", "MX")} | {Language.fromalpha2("es")}
    video_types = (Episode, Movie)
    subtitle_class = SubdivxSubtitle

    multi_result_throttle = 2
    language_list = list(languages)

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = f"Subliminal/{__short_version__}"

    def terminate(self):
        self.session.close()

    def query(self, video, languages):
        if isinstance(video, Episode):
            query = f"{video.series} S{video.season:02}E{video.episode:02}"
        else:
            # Subdvix has problems searching foreign movies if the year is
            # appended. A proper solution would be filtering results with the
            # year in self._parse_subtitles_page.
            query = video.title

        params = {
            "buscar2": query,
            "accion": "5",
            "masdesc": "",
            "subtitulos": "1",
            "realiza_b": "1",
            "pg": "1",
        }

        logger.debug(f"Searching subtitles: {query}")
        subtitles = []
        language = self.language_list[0]
        search_link = f"{_SERVER_URL}/index.php"
        while True:
            response = self.session.get(
                search_link, params=params, allow_redirects=True, timeout=20
            )

            try:
                page_subtitles = self._parse_subtitles_page(video, response, language)
            except Exception as e:
                logger.error(f"Error parsing subtitles list: {e}")
                break

            subtitles += page_subtitles

            if len(page_subtitles) < 100:
                break  # this is the last page

            params["pg"] += 1  # search next page
            time.sleep(self.multi_result_throttle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def download_subtitle(self, subtitle):
        # download the subtitle
        logger.info("Downloading subtitle %r", subtitle)

        # get download link
        download_link = self._get_download_link(subtitle)

        # download zip / rar file with the subtitle
        response = self.session.get(
            f"{_SERVER_URL}/{download_link}",
            headers={"Referer": subtitle.page_link},
            timeout=30,
        )
        response.raise_for_status()

        # open the compressed archive
        archive = _get_archive(response.content)

        # extract the subtitle
        subtitle_content = _get_subtitle_from_archive(archive, subtitle)
        subtitle.content = fix_line_ending(subtitle_content)

    def _parse_subtitles_page(self, video, response, language):
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

            spain = "/pais/7.gif" in datos
            language = Language.fromalpha2("es") if spain else Language("spa", "MX")

            # description
            sub_details = body_soup.find("div", {"id": "buscador_detalle_sub"}).text
            description = sub_details.replace(",", " ").lower()

            # uploader
            uploader = body_soup.find("a", {"class": "link1"}).text
            page_link = title_soup.find("a")["href"]

            subtitle = self.subtitle_class(
                language, video, page_link, title, description, uploader
            )

            logger.debug("Found subtitle %r", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def _get_download_link(self, subtitle):
        response = self.session.get(subtitle.page_link, timeout=20)
        response.raise_for_status()

        try:
            page_soup = ParserBeautifulSoup(
                response.content.decode("utf-8", "ignore"), ["lxml", "html.parser"]
            )
            links_soup = page_soup.find_all("a", {"class": "detalle_link"})
            for link_soup in links_soup:
                if link_soup["href"].startswith("bajar"):
                    return f"{_SERVER_URL}/{link_soup['href']}"

            links_soup = page_soup.find_all("a", {"class": "link1"})
            for link_soup in links_soup:
                if "bajar.php" in link_soup["href"]:
                    return link_soup["href"]
        except Exception as e:
            raise APIThrottled(f"Error parsing download link: {e}")

        raise APIThrottled("Download link not found")


def _clean_title(title):
    """
    Normalize apostrophes and spaces to avoid matching problems
    (e.g. Subtitulos de  Carlito´s  Way -> Carlito's Way)
    """
    for og, new in _CLEAN_TITLE_RES:
        title = re.sub(og, new, title, flags=re.IGNORECASE)

    return title


def _get_archive(content):
    # open the archive
    archive_stream = io.BytesIO(content)
    if rarfile.is_rarfile(archive_stream):
        logger.debug("Identified rar archive")
        archive = rarfile.RarFile(archive_stream)
    elif zipfile.is_zipfile(archive_stream):
        logger.debug("Identified zip archive")
        archive = zipfile.ZipFile(archive_stream)
    else:
        raise APIThrottled("Unsupported compressed format")

    return archive


def _get_subtitle_from_archive(archive, subtitle):
    _valid_names = []
    for name in archive.namelist():
        # discard hidden files
        # discard non-subtitle files
        if not os.path.split(name)[-1].startswith(".") and name.lower().endswith(
            SUBTITLE_EXTENSIONS
        ):
            _valid_names.append(name)

    # archive with only 1 subtitle
    if len(_valid_names) == 1:
        logger.debug(
            f"returning from archive: {_valid_names[0]} (single subtitle file)"
        )
        return archive.read(_valid_names[0])

    # in archives with more than 1 subtitle (season pack) we try to guess the best subtitle file
    _scores = get_scores(subtitle.video)
    _max_score = 0
    _max_name = ""
    for name in _valid_names:
        _guess = guessit(name)
        if "season" not in _guess:
            _guess["season"] = -1
        if "episode" not in _guess:
            _guess["episode"] = -1

        if isinstance(subtitle.video, Episode):
            logger.debug("guessing %s" % name)
            logger.debug(
                f"subtitle S{_guess['season']}E{_guess['episode']} video "
                f"S{subtitle.video.season}E{subtitle.video.episode}"
            )

            if (
                subtitle.video.episode != _guess["episode"]
                or subtitle.video.season != _guess["season"]
            ):
                logger.debug("subtitle does not match video, skipping")
                continue

        matches = set()
        matches |= guess_matches(subtitle.video, _guess)
        _score = sum((_scores.get(match, 0) for match in matches))
        logger.debug("srt matches: %s, score %d" % (matches, _score))
        if _score > _max_score:
            _max_score = _score
            _max_name = name
            logger.debug(f"new max: {name} {_score}")

    if _max_score > 0:
        logger.debug(f"returning from archive: {_max_name} scored {_max_score}")
        return archive.read(_max_name)

    raise APIThrottled("Can not find the subtitle in the compressed file")


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
