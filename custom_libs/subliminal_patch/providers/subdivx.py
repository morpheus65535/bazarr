# -*- coding: utf-8 -*-
from __future__ import absolute_import

from requests.exceptions import JSONDecodeError
import logging
import random
import re

from requests import Session
from subliminal import ProviderError
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import (get_archive_from_bytes, get_subtitle_from_archive, update_matches,
                                              USER_AGENTS)
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

_SERVER_URL = "https://www.subdivx.com"

_CLEAN_TITLE_RES = [
    (r"subt[ií]tulos de", ""),
    (r"´|`", "'"),
    (r" {2,}", " "),
]

_SPANISH_RE = re.compile(r"españa|ib[eé]rico|castellano|gallego|castilla|europ[ae]")
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
_UNSUPPORTED_RE = re.compile(r"(extras|forzado(s)?|forced)\s?$", flags=re.IGNORECASE)
_VERSION_RESOLUTION = re.compile(r'id="vs">([^<]+)<\/div>')

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
        self.session = Session()

    def initialize(self):
        self.session.headers["User-Agent"] = random.choice(USER_AGENTS)
        self.session.cookies.update({"iduser_cookie": _IDUSER_COOKIE})

    def terminate(self):
        self.session.close()

    def _query(self, video, languages):
        subtitles = []

        episode = isinstance(video, Episode)

        titles = [video.series if episode else video.title]

        try:
            titles.extend(video.alternative_series if episode else video.alternative_titles)
        except:
            pass
        else:
            titles = titles[:5]  # limit alt titles

        logger.debug("Titles to look at: %s", titles)

        if episode:
            # TODO: cache pack queries (TV SHOW S01).
            # Too many redundant server calls.
            for title in titles:
                title = _series_sanitizer(title)
                for query in (
                    f"{title} S{video.season:02}E{video.episode:02}",
                    f"{title} S{video.season:02}",
                ):
                    subtitles += self._query_results(query, video)

                # Try only with series title
                if len(subtitles) <= 5:
                    subtitles += self._query_results(title, video)
                else:
                    break

                # Try with episode title as last resort
                if not subtitles and video.title and video.title != title:
                    subtitles += self._query_results(video.title, video)

        else:
            for title in titles:
                for query in (title, f"{title} ({video.year})"):
                    subtitles += self._query_results(query, video)
                    # Second query is a fallback
                    if subtitles:
                        break

        return subtitles

    def _get_vs(self):
        #    t["buscar" + $("#vs").html().replace(".", "").replace("v", "")] = $("#buscar").val(),
        res = self.session.get('https://subdivx.com/')
        results = _VERSION_RESOLUTION.findall(res.text)
        if results is not None and len(results) == 0:
            return -1
        version = results[0]
        version = version.replace('.','').replace('v','')
        return version

    def _query_results(self, query, video):
        token_link = f"{_SERVER_URL}/inc/gt.php?gt=1"

        token_response = self.session.get(token_link, timeout=30)

        if token_response.status_code != 200:
            raise ProviderError("Unable to obtain a token")

        try:
            token_response_json = token_response.json()
        except JSONDecodeError:
            raise ProviderError("Unable to parse JSON response")
        else:
            if 'token' in token_response_json and token_response_json['token']:
                token = token_response_json['token']
            else:
                raise ProviderError("Response doesn't include a token")

        search_link = f"{_SERVER_URL}/inc/ajax.php"
        version = self._get_vs()
        payload = {"tabla": "resultados", "filtros": "", f"buscar{version}": query, "token": token}

        logger.debug("Query: %s", query)

        response = self.session.post(search_link, data=payload, timeout=30)

        if response.status_code == 500:
            logger.debug(
                "Error 500 (probably bad encoding of query causing issue on provider side): %s",
                query,
            )
            return []

        # Ensure it was successful
        response.raise_for_status()

        # Processing the JSON result
        subtitles = []
        try:
            data = response.json()
        except JSONDecodeError:
            logger.debug("JSONDecodeError: %s", response.content)
            return []

        title_checker = _check_episode if isinstance(video, Episode) else _check_movie

        # Iterate over each subtitle in the response
        for item in data["aaData"]:
            id = item["id"]
            page_link = f"{_SERVER_URL}/{id}"
            title = _clean_title(item["titulo"])
            description = item["descripcion"]
            uploader = item["nick"]

            download_url = f"{_SERVER_URL}/descargar.php?id={id}"

            if _UNSUPPORTED_RE.search(title) is not None:
                logger.debug("Skipping unsupported subtitles: %s", title)
                continue

            if not title_checker(video, title):
                continue

            spain = _SPANISH_RE.search(description.lower()) is not None
            language = Language.fromalpha2("es") if spain else Language("spa", "MX")

            subtitle = self.subtitle_class(
                language, video, page_link, title, description, uploader, download_url
            )

            logger.debug("Found subtitle %r", subtitle)
            subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self._query(video, languages)

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

        logger.debug("Episode number: %s", episode)

        subtitle.content = get_subtitle_from_archive(archive, episode=episode)


def _clean_title(title):
    """
    Normalize apostrophes and spaces to avoid matching problems
    (e.g. Subtitulos de  Carlito´s  Way -> Carlito's Way)
    """
    for og, new in _CLEAN_TITLE_RES:
        title = re.sub(og, new, title, flags=re.IGNORECASE)

    return title


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
    series_title = _series_sanitizer(series_title)

    for video_series_title in [video.series] + video.alternative_series:
        video_series_title = _series_sanitizer(video_series_title)
        distance = abs(len(series_title) - len(video_series_title))

        series_matched = (distance < 4 or video_series_title in series_title) and ep_matches

        logger.debug(
            "Series matched? %s [%s -> %s] [title distance: %d]",
            series_matched,
            video_series_title,
            series_title,
            distance,
        )

        if series_matched:
            return True
    return False


def _series_sanitizer(title):
    title = re.sub(r"\'|\.+", '', title)  # remove single quote and dot
    title = re.sub(r"\W+", ' ', title)  # replace by a space anything other than a letter, digit or underscore
    return re.sub(r"([A-Z])\s(?=[A-Z]\b)", '', title).strip()  # Marvels Agent of S.H.I.E.L.D


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
