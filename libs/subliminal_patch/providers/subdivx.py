# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import re
import time

from requests import Session
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

        # Determine if the video is a movie or a TV episode and set the search accordingly
        
        if isinstance(video, Episode):
            # For TV episodes, use alternative_series if available ; only include titles that pass the is_latin_extended test (reject non latin alphabets)
            titles_to_search = [title for title in [video.title] + getattr(video, 'alternative_series', []) if is_latin_extended(title)]

            # TODO: cache pack queries (TV SHOW S01).
            # Too many redundant server calls.

            # For TV episodes, construct queries with each main and alternative series title
            for title in titles_to_search:
                # Perform the existing search logic for each title
                subtitles += self._handle_search(f"{title} S{video.season:02}E{video.episode:02}", video)

            # If nothing found under SxxExx, try with only season number
            if not subtitles:
                for title in titles_to_search:
                    # Perform the existing search logic for each title
                    subtitles += self._handle_search(f"{title} S{video.season:02}", video)

            # If still nothing found, try with only series title (each main and alternative series title)
            if not subtitles:
                for title in titles_to_search:
                    subtitles += self._handle_search(title, video, 1)

            # Try with episode title as last resort
            if not subtitles and video.title != video.series:
                subtitles += self._handle_search(video.title, video, 1)

            # Additional logic for handling insufficient subtitle results can go here

        else:
            # For movies, use alternative_titles if available ; only include titles that pass the is_latin_extended test (reject non latin alphabets)
            titles_to_search = [title for title in [video.title] + getattr(video, 'alternative_titles', []) if is_latin_extended(title)]

            # For movies, first search with the title and year (if available) (each main and alternative movie title)
            if video.year:
                for title in titles_to_search:
                    subtitles += self._handle_search(f"{title} ({video.year})", video)

            # Then add a search with only the title (each main and alternative movie title)
            for title in titles_to_search:
                subtitles += self._handle_search(title, video)


            # Additional logic for handling insufficient subtitle results can go here

        return subtitles

    def _handle_search(self, query, video):
        # URL for the POST request
        search_link = f"{_SERVER_URL}/inc/ajax.php"

        # Payload for POST
        payload = {
            'tabla': 'resultados',
            'filtros': '',  # Not used now
            'buscar': query
        }
    
        logger.debug("Query: %s", query)
    
        # Make the POST request
        response = self.session.post(search_link, data=payload)
        
        if response.status_code == 500:
            logger.debug("Error 500 (probably bad encoding of query causing issue on provider side): %s", query)
            return []
    
        # Ensure it was successful
        response.raise_for_status()

        # Processing the JSON result
        subtitles = []
        data = response.json()

        # Iterate over each subtitle in the response
        for item in data['aaData']:
            # Extract the relevant information
            id_subtitulo = item['id']
            page_link = f"{_SERVER_URL}/descargar.php?id={id_subtitulo}"  # There is no direct link to view sub details, this is just the download link
            title = item['titulo']
            description = item['descripcion']
            uploader = item['nick']

            download_url = f"{_SERVER_URL}/descargar.php?id={id_subtitulo}"  # Build the download URL - assuming RAR for now

            language = Language('spa', 'MX')  # Subdivx is always latin spanish

            # Create the SubdivxSubtitle instance
            subtitle = self.subtitle_class(language, video, page_link, title, description, uploader, download_url)

            subtitles.append(subtitle)

        return subtitles  # The JSON contains all subs, not paged

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

    # Prepare a list of all series names to check against (include alternative series names)
    series_names = [video.series] + getattr(video, 'alternative_series', [])
    
    # Normalize the title for comparison
    normalized_title = _clean_title(title).lower()

    # Check if the normalized title contains any of the series names (main or alternative)
    series_clean_match = any(series_name.lower() in normalized_title for series_name in series_names)

    # Include matches where the episode title is present
    if (
        series_clean_match
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

    series_matched = (distance < 4 and ep_matches) or series_clean_match

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

def is_latin_extended(s):
    """
    Checks if the string contains only latin or latin extended or european
    language characters, excluding non-latin alphabets.
    """
    # Regex with only valid characters.
    patron = re.compile(r'^[a-zA-Z0-9 \.\,\-\(\)\!\?áéíóúüñÁÉÍÓÚÜÑäöüßÄÖÜàèìòùÀÈÌÒÙãõÃÕåÅęłńśźżĄĘŁŃŚŹŻçÇğĞşŞıİøØđĐžŽčšŠ]+$')
    return bool(patron.match(s))
