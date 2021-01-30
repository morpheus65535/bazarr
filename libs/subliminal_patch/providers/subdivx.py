# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import logging
import os
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
    languages = {Language.fromalpha2(lang) for lang in ["es"]}
    subtitle_class = SubdivxSubtitle

    server_url = "https://www.subdivx.com/"
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
            "q": query,  # search string
            "accion": 5,  # action search
            "oxdown": 1,  # order by downloads descending
            "pg": 1,  # page 1
        }

        logger.debug(f"Searching subtitles: {query}")
        subtitles = []
        language = self.language_list[0]
        search_link = self.server_url + "index.php"
        while True:
            response = self.session.get(search_link, params=params, timeout=20)
            self._check_response(response)

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
        if isinstance(subtitle, SubdivxSubtitle):
            # download the subtitle
            logger.info("Downloading subtitle %r", subtitle)

            # get download link
            download_link = self._get_download_link(subtitle)

            # download zip / rar file with the subtitle
            response = self.session.get(
                self.server_url + download_link,
                headers={"Referer": subtitle.page_link},
                timeout=30,
            )
            self._check_response(response)

            # open the compressed archive
            archive = self._get_archive(response.content)

            # extract the subtitle
            subtitle_content = self._get_subtitle_from_archive(archive, subtitle)
            subtitle.content = fix_line_ending(subtitle_content)

    def _parse_subtitles_page(self, video, response, language):
        subtitles = []

        page_soup = ParserBeautifulSoup(
            response.content.decode("utf-8", "ignore"), ["lxml", "html.parser"]
        )
        title_soups = page_soup.find_all("div", {"id": "menu_detalle_buscador"})
        body_soups = page_soup.find_all("div", {"id": "buscador_detalle"})

        for subtitle in range(0, len(title_soups)):
            title_soup, body_soup = title_soups[subtitle], body_soups[subtitle]

            # title
            title = title_soup.find("a").text.replace("Subtitulos de ", "")

            # filter by year
            if video.year and str(video.year) not in title:
                continue

            page_link = title_soup.find("a")["href"]

            # description
            description = body_soup.find("div", {"id": "buscador_detalle_sub"}).text
            description = description.replace(",", " ").lower()

            # uploader
            uploader = body_soup.find("a", {"class": "link1"}).text

            subtitle = self.subtitle_class(
                language, video, page_link, title, description, uploader
            )

            logger.debug("Found subtitle %r", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def _get_download_link(self, subtitle):
        response = self.session.get(subtitle.page_link, timeout=20)
        self._check_response(response)
        try:
            page_soup = ParserBeautifulSoup(
                response.content.decode("utf-8", "ignore"), ["lxml", "html.parser"]
            )
            links_soup = page_soup.find_all("a", {"class": "detalle_link"})
            for link_soup in links_soup:
                if link_soup["href"].startswith("bajar"):
                    return self.server_url + link_soup["href"]
            links_soup = page_soup.find_all("a", {"class": "link1"})
            for link_soup in links_soup:
                if "bajar.php" in link_soup["href"]:
                    return link_soup["href"]
        except Exception as e:
            raise APIThrottled(f"Error parsing download link: {e}")

        raise APIThrottled("Download link not found")

    @staticmethod
    def _check_response(response):
        if response.status_code != 200:
            raise ServiceUnavailable(f"Bad status code: {response.status_code}")

    @staticmethod
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

    @staticmethod
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
