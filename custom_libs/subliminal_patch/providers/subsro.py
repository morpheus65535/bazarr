# coding=utf-8

import io
import re
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from requests import Session
from bs4 import BeautifulSoup
import logging
from guessit import guessit
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.video import Episode, Movie
from subzero.language import Language
from subliminal_patch.exceptions import APIThrottled, TooManyRequests

logger = logging.getLogger(__name__)


class SubsRoSubtitle(Subtitle):
    """SubsRo Subtitle."""

    provider_name = "subsro"
    hash_verifiable = False

    def __init__(
        self,
        language,
        title,
        download_link,
        imdb_id,
        is_episode=False,
        episode_number=None,
        year=None,
        release_info=None,
        season=None,
    ):
        super().__init__(language)
        self.title = title
        self.page_link = download_link
        self.imdb_id = imdb_id
        self.matches = None
        self.asked_for_episode = is_episode
        self.episode = episode_number
        self.year = year
        self.release_info = self.releases = release_info
        self.season = season

    @property
    def id(self):
        logger.info("Getting ID for SubsRo subtitle: %s. ID: %s", self, self.page_link)
        return self.page_link

    def get_matches(self, video):
        matches = set()

        if video.year and self.year == video.year:
            matches.add("year")

        if isinstance(video, Movie):
            # title
            if video.title:
                matches.add("title")

            # imdb
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add("imdb_id")

            # guess match others
            matches |= guess_matches(
                video,
                guessit(
                    f"{self.title} {self.season} {self.year} {self.release_info}",
                    {"type": "movie"},
                ),
            )

        else:
            # title
            if video.series:
                matches.add("series")

            # imdb
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add("imdb_id")

            # season
            if video.season == self.season:
                matches.add("season")

            # episode
            if {"imdb_id", "season"}.issubset(matches):
                matches.add("episode")

            # guess match others
            matches |= guess_matches(
                video,
                guessit(
                    f"{self.title} {self.year} {self.release_info}", {"type": "episode"}
                ),
            )

        self.matches = matches
        return matches


class SubsRoProvider(Provider, ProviderSubtitleArchiveMixin):
    """SubsRo Provider."""

    languages = {Language(lang) for lang in ["ron", "eng"]}
    video_types = (Episode, Movie)
    hash_verifiable = False

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        # Placeholder, update with real API if available
        self.url = "https://subs.ro/api/search"

    def terminate(self):
        self.session.close()

    @classmethod
    def check(cls, video):
        return isinstance(video, (Episode, Movie))

    def query(self, language, imdb_id, video):
        logger.info("Querying SubsRo for %s subtitles of %s", language, imdb_id)
        if not imdb_id:
            return []

        url = f"https://subs.ro/subtitrari/imdbid/{imdb_id}"
        response = self._request("get", url)

        results = []
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all("div", class_="md:col-span-6"):
            if (
                "flag-rom" in item.find("img")["src"] and language != Language("ron")
            ) or (
                "flag-eng" in item.find("img")["src"] and language != Language("eng")
            ):
                continue  # Skip if English flag and language is not English or Romanian flag and language is not Romanian

            episode_number = video.episode if isinstance(video, Episode) else None

            div_tag = item.find("div", class_="col-span-2 lg:col-span-1")
            download_link = None
            if div_tag:
                a_tag = div_tag.find("a")
                if a_tag and a_tag.has_attr("href"):
                    download_link = a_tag["href"]

            h1_tag = item.find(
                "h1",
                class_="leading-tight text-base font-semibold mb-1 border-b border-dashed border-gray-300 text-[#7f431e] hover:text-red-800",
            )
            title = None
            year = None
            if h1_tag:
                a_tag = h1_tag.find("a")
                if a_tag and a_tag.text:
                    title_raw = a_tag.text.strip()
                    title = re.sub(
                        r"\s*(-\s*Sezonul\s*\d+)?\s*\(\d{4}\).*$", "", title_raw
                    ).strip()
                    year = re.search(r"\((\d{4})\)", title_raw).group(1)
                    season = re.search(r"\s*Sezonul\s *\d?", title_raw)
                    if season:
                        season = int(season.group(0).replace("Sezonul", "").strip())

            release_info = None
            p_tag = item.find(
                "p", class_="text-sm font-base overflow-auto h-auto lg:h-16"
            )
            if p_tag:
                span_blue = p_tag.find("span", style=lambda s: s and "color: blue" in s)
                if span_blue:
                    release_info = span_blue.get_text(strip=True)
                else:
                    release_info = p_tag.get_text(separator="\n", strip=True)

            if download_link and title and year:
                results.append(
                    SubsRoSubtitle(
                        language,
                        title,
                        download_link,
                        f"tt{imdb_id}",
                        isinstance(video, Episode),
                        episode_number,
                        year,
                        release_info,
                        season,
                    )
                )
        return results

    def list_subtitles(self, video, languages):
        imdb_id = None
        try:
            if isinstance(video, Episode):
                imdb_id = video.series_imdb_id[2:]
            else:
                imdb_id = video.imdb_id[2:]
        except:
            logger.error(
                "Error parsing imdb_id from video object {}".format(str(video))
            )

        subtitles = [s for lang in languages for s in self.query(lang, imdb_id, video)]
        return subtitles

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle from SubsRo: %s", subtitle.page_link)
        response = self._request("get", subtitle.page_link)

        archive_stream = io.BytesIO(response.content)
        if is_rarfile(archive_stream):
            logger.debug("Archive identified as RAR")
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug("Archive identified as ZIP")
            archive = ZipFile(archive_stream)
        else:
            if subtitle.is_valid():
                subtitle.content = response.content
                return True
            else:
                subtitle.content = None
                return False

        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
        return True

    def _request(self, method, url, **kwargs):
        try:
            response = self.session.request(method, url, **kwargs)
        except Exception as e:
            logger.error("SubsRo request error: %s", e)
            raise APIThrottled(f"SubsRo request failed: {e}")

        if response.status_code == 429:
            logger.warning("SubsRo: Too many requests (HTTP 429) for %s", url)
            raise TooManyRequests("SubsRo: Too many requests (HTTP 429)")
        if response.status_code >= 500:
            logger.warning("SubsRo: Server error %s for %s", response.status_code, url)
            raise APIThrottled(f"SubsRo: Server error {response.status_code}")
        if response.status_code != 200:
            logger.warning(
                "SubsRo: Unexpected status %s for %s", response.status_code, url
            )
            raise APIThrottled(f"SubsRo: Unexpected status {response.status_code}")

        return response
