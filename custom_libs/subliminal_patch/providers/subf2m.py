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
from subliminal.exceptions import ConfigurationError
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
            ("title", "year", "imdb_id")
            if episode_number is None
            else ("title", "series", "year", "season", "episode", "imdb_id")
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

_DEFAULT_HEADERS = {
    "authority": "subf2m.co",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "referer": "https://subf2m.co",
    "sec-ch-ua": '"Chromium";v="111", "Not(A:Brand";v="8"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Unknown"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}


class Subf2mProvider(Provider):
    provider_name = "subf2m"

    _movie_title_regex = re.compile(r"^(.+?)(\s+\((\d{4})\))?$")
    _tv_show_title_regex = re.compile(
        r"^(.+?)\s+[-\(]\s?(.*?)\s+(season|series)\)?(\s+\((\d{4})\))?$"
    )
    _tv_show_title_alt_regex = re.compile(r"(.+)\s(\d{1,2})(?:\s|$)")
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

    def __init__(self, user_agent, verify_ssl=True, session_factory=None):
        super().__init__()

        if not (user_agent or "").strip():
            raise ConfigurationError("User-agent config missing")

        self._user_agent = user_agent
        self._verify_ssl = verify_ssl
        self._session_factory = session_factory

    def initialize(self):
        if self._session_factory is not None:
            self._session = self._session_factory()
        else:
            logger.debug("No session factory set. Using default requests.Session.")
            self._session = Session()

        self._session.verify = self._verify_ssl
        self._session.headers.update(_DEFAULT_HEADERS)
        self._session.headers.update({"user-agent": self._user_agent})

    def terminate(self):
        self._session.close()

    def _safe_get_text(self, url, retry=3, default_return=""):
        req = None

        for n in range(retry):
            req = self._session.get(url, stream=True)

            if req.status_code == 403:
                logger.debug("Access to this resource is forbidden: %s", url)
                break

            # Sometimes subf2m will return 404 or 503. This error usually disappears
            # retrying the query
            if req.status_code in (404, 503):
                logger.debug("503/404 returned. Trying again [%d] in 3 seconds", n + 1)
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

    def _search_movie(self, title, year, return_len=3):
        title = title.lower()
        year = str(year)

        results = []
        for result in self._gen_results(title):
            text = result.text.strip().lower()
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
            results = [result["href"] for result in results]
            if results:
                results = set(results[:return_len])
                logger.debug("Results: %s", results)
                return results

        return []

    def _search_tv_show_season(self, title, season, year=None, return_len=3):
        try:
            season_strs = (_SEASONS[season - 1].lower(), str(season))
        except IndexError:
            logger.debug("Season number not supported: %s", season)
            return None

        results = []
        for result in self._gen_results(title):
            text = result.text.strip().lower()

            match = self._tv_show_title_regex.match(text)
            if not match:
                match = self._tv_show_title_alt_regex.match(text)

            if not match:
                logger.debug("Series title not matched: %s", text)
                continue

            match_title = match.group(1).strip()
            match_season = match.group(2).strip().lower()

            if match_season in season_strs or "complete" in match_season:
                logger.debug("OK: '%s' IN %s|complete", match_season, season_strs)
                plus = 0.1 if year and str(year) in text else 0
                results.append(
                    {
                        "href": result.get("href"),
                        "similarity": SequenceMatcher(None, title, match_title).ratio()
                        + plus,
                    }
                )
            else:
                logger.debug("Invalid: '%s' IN %s|complete", match_season, season_strs)

        if results:
            results.sort(key=lambda x: x["similarity"], reverse=True)
            results = [result["href"] for result in results]
            if results:
                results = set(results[:return_len])
                logger.debug("Results: %s", results)
                return results

        return []

    def _find_movie_subtitles(self, path, language, imdb_id):
        soup = self._get_subtitle_page_soup(path, language)
        imdb_matched = _match_imdb(soup, imdb_id)
        if not imdb_matched:
            return []

        subtitles = []

        for item in soup.select("li.item"):
            subtitle = _get_subtitle_from_item(item, language)
            if subtitle is None:
                continue

            logger.debug("Found subtitle: %s", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def _find_episode_subtitles(
        self, path, season, episode, language, episode_title=None, imdb_id=None
    ):
        soup = self._get_subtitle_page_soup(path, language)
        imdb_matched = _match_imdb(soup, imdb_id)
        if not imdb_matched:
            return []

        subtitles = []

        for item in soup.select("li.item"):
            valid_item = None
            clean_text = " ".join(item.text.split())

            if not clean_text:
                continue

            # First try with the special episode matches for subf2m
            guess = _get_episode_from_release(clean_text)

            if guess is None:
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
            paths = self._search_tv_show_season(video.series, video.season, video.year)
        else:
            paths = self._search_movie(video.title, video.year)

        if not paths:
            logger.debug("No results")
            return []

        languages = set([lang for lang in languages if lang in self.languages])

        subs = []
        for path in paths:
            must_break = False

            logger.debug("Looking for subs from %s", path)

            for language in languages:
                if is_episode:
                    subs.extend(
                        self._find_episode_subtitles(
                            path,
                            video.season,
                            video.episode,
                            language,
                            video.title,
                            video.series_imdb_id,
                        )
                    )

                else:
                    subs.extend(
                        self._find_movie_subtitles(path, language, video.imdb_id)
                    )

                must_break = subs != []

            if must_break:
                logger.debug("Good path found: %s. Not running over others.", path)
                break

        return subs

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


_EPISODE_SPECIAL_RE = re.compile(
    r"(season|s)\s*?(?P<x>\d{,2})\s?[-−]\s?(?P<y>\d{,2})", flags=re.IGNORECASE
)


def _match_imdb(soup, imdb_id):
    try:
        parsed_imdb_id = (
            soup.select_one(
                "#content > div.subtitles.byFilm > div.box.clearfix > div.top.left > div.header > h2 > a"
            )
            .get("href")  # type: ignore
            .split("/")[-1]  # type: ignore
            .strip()
        )
    except AttributeError:
        logger.debug("Couldn't get IMDB ID")
        parsed_imdb_id = None

    if parsed_imdb_id is not None and parsed_imdb_id != imdb_id:
        logger.debug("Wrong IMDB ID: '%s' != '%s'", parsed_imdb_id, imdb_id)
        return False

    if parsed_imdb_id is None:
        logger.debug("Matching subtitles as IMDB ID was not parsed.")
    else:
        logger.debug("Good IMDB ID: '%s' == '%s'", parsed_imdb_id, imdb_id)

    return True


def _get_episode_from_release(release: str):
    match = _EPISODE_SPECIAL_RE.search(release)
    if match is None:
        return None

    try:
        season, episode = [int(item) for item in match.group("x", "y")]
    except (IndexError, ValueError):
        return None

    return {"season": [season], "episode": [episode]}


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
