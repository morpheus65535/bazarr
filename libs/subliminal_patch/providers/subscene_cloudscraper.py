# -*- coding: utf-8 -*-

from difflib import SequenceMatcher
import functools
import logging
import re
import time
import urllib.parse

from bs4 import BeautifulSoup as bso
import cloudscraper
from guessit import guessit
from requests import Session
from requests.exceptions import HTTPError
from subliminal.exceptions import ProviderError
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)


class SubsceneSubtitle(Subtitle):
    provider_name = "subscene_cloudscraper"
    hash_verifiable = False

    def __init__(self, language, page_link, release_info, episode_number=None):
        super().__init__(language, page_link=page_link)

        self.release_info = release_info
        self.episode_number = episode_number
        self.episode_title = None

        self._matches = set(
            ("title", "year")
            if episode_number is None
            else ("title", "series", "year", "season", "episode")
        )

    def get_matches(self, video):
        update_matches(self._matches, video, self.release_info)

        return self._matches

    @property
    def id(self):
        return self.page_link


_BASE_URL = "https://subscene.com"

# TODO: add more seasons and languages

_SEASONS = (
    "First",
    "Second",
    "Third",
    "Fourth",
    "Fifth",
    "Sixth",
    "Seventh",
    "Eighth",
    "Ninth",
    "Tenth",
    "Eleventh",
    "Twelfth",
    "Thirdteenth",
    "Fourthteenth",
    "Fifteenth",
    "Sixteenth",
    "Seventeenth",
    "Eightheenth",
    "Nineteenth",
    "Tweentieth",
)

_LANGUAGE_MAP = {
    "english": "eng",
    "farsi_persian": "per",
    "arabic": "ara",
    "spanish": "spa",
    "portuguese": "por",
    "italian": "ita",
    "dutch": "dut",
    "hebrew": "heb",
    "indonesian": "ind",
    "danish": "dan",
    "norwegian": "nor",
    "bengali": "ben",
    "bulgarian": "bul",
    "croatian": "hrv",
    "swedish": "swe",
    "vietnamese": "vie",
    "czech": "cze",
    "finnish": "fin",
    "french": "fre",
    "german": "ger",
    "greek": "gre",
    "hungarian": "hun",
    "icelandic": "ice",
    "japanese": "jpn",
    "macedonian": "mac",
    "malay": "may",
    "polish": "pol",
    "romanian": "rum",
    "russian": "rus",
    "serbian": "srp",
    "thai": "tha",
    "turkish": "tur",
}


class SubsceneProvider(Provider):
    provider_name = "subscene_cloudscraper"

    _movie_title_regex = re.compile(r"^(.+?)( \((\d{4})\))?$")
    _tv_show_title_regex = re.compile(
        r"^(.+?) [-\(]\s?(.*?) (season|series)\)?( \((\d{4})\))?$"
    )
    _supported_languages = {}
    _supported_languages["brazillian-portuguese"] = Language("por", "BR")

    for key, val in _LANGUAGE_MAP.items():
        _supported_languages[key] = Language.fromalpha3b(val)

    _supported_languages_reversed = {
        val: key for key, val in _supported_languages.items()
    }

    languages = set(_supported_languages.values())

    video_types = (Episode, Movie)
    subtitle_class = SubsceneSubtitle

    def initialize(self):
        pass

    def terminate(self):
        pass

    def _scraper_call(self, url, retry=7, method="GET", sleep=5, **kwargs):
        last_exc = None

        for n in range(retry):
            # Creating an instance for every try in order to avoid dropped connections.

            # This could probably be improved!
            scraper = cloudscraper.create_scraper()
            if method == "GET":
                req = scraper.get(url, **kwargs)
            elif method == "POST":
                req = scraper.post(url, **kwargs)
            else:
                raise NotImplementedError(f"{method} not allowed")

            try:
                req.raise_for_status()
            except HTTPError as error:
                logger.debug(
                    "'%s' returned. Trying again [%d] in %s", error, n + 1, sleep
                )
                last_exc = error
                time.sleep(sleep)
            else:
                return req

        raise ProviderError("403 Retry count exceeded") from last_exc

    def _gen_results(self, query):
        url = (
            f"{_BASE_URL}/subtitles/searchbytitle?query={urllib.parse.quote(query)}&l="
        )

        result = self._scraper_call(url, method="POST")
        soup = bso(result.content, "html.parser")

        for title in soup.select("li div[class='title'] a"):
            yield title

    def _search_movie(self, title, year):
        title = title.lower()
        year = str(year)

        found_movie = None

        results = []
        for result in self._gen_results(title):
            text = result.text.lower()
            match = self._movie_title_regex.match(text)
            if not match:
                continue
            match_title = match.group(1)
            match_year = match.group(3)
            if year == match_year:
                results.append(
                    {
                        "href": result.get("href"),
                        "similarity": SequenceMatcher(None, title, match_title).ratio(),
                    }
                )

        if results:
            results.sort(key=lambda x: x["similarity"], reverse=True)
            found_movie = results[0]["href"]
            logger.debug("Movie found: %s", results[0])
        return found_movie

    def _search_tv_show_season(self, title, season, year=None):
        try:
            season_str = _SEASONS[season - 1].lower()
        except IndexError:
            logger.debug("Season number not supported: %s", season)
            return None

        found_tv_show_season = None

        results = []
        for result in self._gen_results(title):
            text = result.text.lower()

            match = self._tv_show_title_regex.match(text)
            if not match:
                logger.debug("Series title not matched: %s", text)
                continue
            else:
                logger.debug("Series title matched: %s", text)

            match_title = match.group(1)
            match_season = match.group(2)

            # Match "complete series" titles as they usually contain season packs
            if season_str == match_season or "complete" in match_season:
                plus = 0.1 if year and str(year) in text else 0
                results.append(
                    {
                        "href": result.get("href"),
                        "similarity": SequenceMatcher(None, title, match_title).ratio()
                        + plus,
                    }
                )

        if results:
            results.sort(key=lambda x: x["similarity"], reverse=True)
            found_tv_show_season = results[0]["href"]
            logger.debug("TV Show season found: %s", results[0])

        return found_tv_show_season

    def _find_movie_subtitles(self, path, language):
        soup = self._get_subtitle_page_soup(path, language)

        subtitles = []
        for item in soup.select("tr"):
            subtitle = _get_subtitle_from_item(item, language)
            if subtitle is None:
                continue

            logger.debug("Found subtitle: %s", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def _find_episode_subtitles(
        self, path, season, episode, language, episode_title=None
    ):
        soup = self._get_subtitle_page_soup(path, language)

        subtitles = []

        for item in soup.select("tr"):
            valid_item = None
            clean_text = " ".join(item.text.split())

            if not clean_text:
                continue

            # It will return list values
            guess = _memoized_episode_guess(clean_text)

            if "season" not in guess:
                if "complete series" in clean_text.lower():
                    logger.debug("Complete series pack found: %s", clean_text)
                    guess["season"] = [season]
                else:
                    logger.debug("Nothing guessed from release: %s", clean_text)
                    continue

            if season in guess["season"] and episode in guess.get("episode", []):
                logger.debug("Episode match found: %s - %s", guess, clean_text)
                valid_item = item

            elif season in guess["season"] and not "episode" in guess:
                logger.debug("Season pack found: %s", clean_text)
                valid_item = item

            if valid_item is None:
                continue

            subtitle = _get_subtitle_from_item(item, language, episode)

            if subtitle is None:
                continue

            subtitle.episode_title = episode_title

            logger.debug("Found subtitle: %s", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def _get_subtitle_page_soup(self, path, language):
        language_path = self._supported_languages_reversed[language]
        result = self._scraper_call(f"{_BASE_URL}{path}/{language_path}")
        return bso(result.content, "html.parser")

    def list_subtitles(self, video, languages):
        is_episode = isinstance(video, Episode)

        if is_episode:
            result = self._search_tv_show_season(video.series, video.season, video.year)
        else:
            result = self._search_movie(video.title, video.year)

        if result is None:
            logger.debug("No results")
            return []

        subtitles = []

        for language in languages:
            if is_episode:
                subtitles.extend(
                    self._find_episode_subtitles(
                        result, video.season, video.episode, language, video.title
                    )
                )
            else:
                subtitles.extend(self._find_movie_subtitles(result, language))

        return subtitles

    def download_subtitle(self, subtitle):
        # TODO: add MustGetBlacklisted support

        result = self._scraper_call(subtitle.page_link)
        soup = bso(result.content, "html.parser")
        try:
            download_url = _BASE_URL + str(
                soup.select_one("a[id='downloadButton']")["href"]  # type: ignore
            )
        except (AttributeError, KeyError, TypeError):
            raise APIThrottled(f"Couldn't get download url from {subtitle.page_link}")

        downloaded = self._scraper_call(download_url)
        archive = get_archive_from_bytes(downloaded.content)

        if archive is None:
            raise APIThrottled(f"Invalid archive: {subtitle.page_link}")

        subtitle.content = get_subtitle_from_archive(
            archive,
            episode=subtitle.episode_number,
            episode_title=subtitle.episode_title,
        )


@functools.lru_cache(2048)
def _memoized_episode_guess(content):
    # Use include to save time from unnecessary checks
    return guessit(
        content,
        {
            "type": "episode",
            # Add codec keys to avoid matching x264, 5.1, etc as episode info
            "includes": ["season", "episode", "video_codec", "audio_codec"],
            "enforce_list": True,
        },
    )


def _get_subtitle_from_item(item, language, episode_number=None):
    release_infos = []

    try:
        release_infos.append(item.find("td", {"class": "a6"}).text.strip())
    except (AttributeError, KeyError):
        pass

    try:
        release_infos.append(
            item.find("td", {"class": "a1"}).find_all("span")[-1].text.strip()
        )
    except (AttributeError, KeyError):
        pass

    release_info = "".join(r_info for r_info in release_infos if r_info)

    try:
        path = item.find("td", {"class": "a1"}).find("a")["href"]
    except (AttributeError, KeyError):
        logger.debug("Couldn't get path: %s", item)
        return None

    return SubsceneSubtitle(language, _BASE_URL + path, release_info, episode_number)
