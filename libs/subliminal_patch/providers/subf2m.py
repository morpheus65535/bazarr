# -*- coding: utf-8 -*-

from difflib import SequenceMatcher
import functools
import logging
import re
import time
import urllib.parse

from bs4 import BeautifulSoup as bso
from guessit import guessit
from requests import Session
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


class Subf2mSubtitle(Subtitle):
    provider_name = "subf2m"
    hash_verifiable = False

    def __init__(self, language, page_link, release_info, episode_number=None):
        super().__init__(language, page_link=page_link)

        self.release_info = release_info
        self.episode_number = episode_number
        self.episode_title = None

        self._matches = set(
            ("title", "year")
            if episode_number is None
            else ("title", "series", "season", "episode")
        )

    def get_matches(self, video):
        update_matches(self._matches, video, self.release_info)

        return self._matches

    @property
    def id(self):
        return self.page_link


_BASE_URL = "https://subf2m.co"

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


class Subf2mProvider(Provider):
    provider_name = "subf2m"

    _movie_title_regex = re.compile(r"^(.+?)( \((\d{4})\))?$")
    _tv_show_title_regex = re.compile(r"^(.+?) - (.*?) (season|series)( \((\d{4})\))?$")
    _supported_languages = {}
    _supported_languages["brazillian-portuguese"] = Language("por", "BR")

    for key, val in _LANGUAGE_MAP.items():
        _supported_languages[key] = Language.fromalpha3b(val)

    _supported_languages_reversed = {
        val: key for key, val in _supported_languages.items()
    }

    languages = set(_supported_languages.values())

    video_types = (Episode, Movie)
    subtitle_class = Subf2mSubtitle

    def initialize(self):
        self._session = Session()
        self._session.headers.update({"user-agent": "Bazarr"})

    def terminate(self):
        self._session.close()

    def _safe_get_text(self, url, retry=3, default_return=""):
        req = None

        for n in range(retry):
            req = self._session.get(url, stream=True)
            # Sometimes subf2m will return a 503 code. This error usually disappears
            # retrying the query
            if req.status_code == 503:
                logger.debug("503 returned. Trying again [%d] in 3 seconds", n + 1)
                time.sleep(3)
                continue
            else:
                req.raise_for_status()
                break

        if req is not None:
            return "\n".join(
                line for line in req.iter_lines(decode_unicode=True) if line
            )

        return default_return

    def _gen_results(self, query):
        query = urllib.parse.quote(query)

        url = f"{_BASE_URL}/subtitles/searchbytitle?query={query}&l="

        text = self._safe_get_text(url)
        soup = bso(text, "html.parser")

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

    def _search_tv_show_season(self, title, season):
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
            if season_str == match_season or match_season == "complete":
                results.append(
                    {
                        "href": result.get("href"),
                        "similarity": SequenceMatcher(None, title, match_title).ratio(),
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

        for item in soup.select("li.item"):
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

        for item in soup.select("li.item"):
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

        text = self._safe_get_text(f"{_BASE_URL}{path}/{language_path}")

        return bso(text, "html.parser")

    def list_subtitles(self, video, languages):
        is_episode = isinstance(video, Episode)

        if is_episode:
            result = self._search_tv_show_season(video.series, video.season)
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

        text = self._safe_get_text(subtitle.page_link)
        soup = bso(text, "html.parser")
        try:
            download_url = _BASE_URL + str(
                soup.select_one("a[id='downloadButton']")["href"]  # type: ignore
            )
        except (AttributeError, KeyError, TypeError):
            raise APIThrottled(f"Couldn't get download url from {subtitle.page_link}")

        downloaded = self._session.get(download_url, allow_redirects=True)

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
    release_info = [
        rel.text.strip() for rel in item.find("ul", {"class": "scrolllist"})
    ]

    try:
        text = item.find("div", {"class": "comment-col"}).find("p").text
        release_info.append(text.replace("\n", " ").strip())
    except AttributeError:
        pass

    release_info = "\n".join([item for item in release_info if item])

    try:
        path = item.find("a", {"class": "download icon-download"})["href"]  # type: ignore
    except (AttributeError, KeyError):
        logger.debug("Couldn't get path: %s", item)
        return None

    return Subf2mSubtitle(language, _BASE_URL + path, release_info, episode_number)
