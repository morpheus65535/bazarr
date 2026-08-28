# -*- coding: utf-8 -*-
"""Provider for the public, unauthenticated search/download flow of
opensubtitles.org.

This is intentionally independent from ``opensubtitlescom.py`` (the
provider for the modern api.opensubtitles.com REST API, which requires a
username/password). It does not use the legacy OpenSubtitles XML-RPC API
either, since unauthenticated ``SearchSubtitles`` calls against that API
return ``401 Unauthorized``.

Instead, this provider scrapes the classic HTML search results and
subtitle download pages through the ``api.opensubtitles.org`` mirror.
Manual testing showed that:

* ``www.opensubtitles.org`` is protected by an "Anubis" proof-of-work
  anti-bot challenge and returns HTTP 401 with a challenge page for
  plain HTTP clients.
* ``api.opensubtitles.org`` serves the exact same HTML (search results,
  subtitle listings, subtitle downloads) without that challenge.

No username or password is required or supported by this provider.
"""
from __future__ import absolute_import

import gzip
import io
import logging
import re
import urllib.parse
import zipfile

import pysubs2
import rarfile
from babelfish.exceptions import LanguageReverseError
from babelfish import language_converters
from bs4 import BeautifulSoup as bso
from guessit import guessit
from requests import Session

from subliminal.subtitle import fix_line_ending
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.utils import sanitize
from subzero.language import Language

logger = logging.getLogger(__name__)

# api.opensubtitles.org mirrors www.opensubtitles.org's HTML pages without
# the Anubis anti-bot challenge that blocks plain HTTP clients on the www
# subdomain (confirmed by manual testing).
_SERVER_URL = "https://api.opensubtitles.org"

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Reuse Bazarr's own OpenSubtitles language converter (adds pt-BR, sr script
# variants, zh-Hant, es-MX on top of babelfish's stock alpha3b/opensubtitles
# mapping) so that language codes match exactly what the rest of the
# codebase (e.g. opensubtitlescom) considers valid OpenSubtitles codes.
_LANGUAGE_CONVERTER = language_converters["szopensubtitles"]

_ROW_ID_RE = re.compile(r"^name(\d+)$")
_LANG_CODE_RE = re.compile(r"sublanguageid-([a-zA-Z]+)")
_IMDB_ID_RE = re.compile(r"imdb\.com/title/tt(\d+)")
_YEAR_RE = re.compile(r"\((\d{4})\)\s*$")
_TITLE_PREFIX_RE = re.compile(r"^subtitles\s*-\s*", re.I)
_DOWNLOAD_COUNT_RE = re.compile(r"^\d+x$")

# On a subtitle *detail* page (e.g. /en/subtitles/{id}/{slug}), the actual
# direct, unauthenticated download link is an absolute
# https://dl.opensubtitles.org/en/download/file/{token} URL. This token is
# unrelated to the subtitle id used on search result pages/subtitleserve
# links, is only exposed on the detail page, and must be extracted fresh
# for every subtitle (confirmed by live testing: see PR description).
_DOWNLOAD_TOKEN_RE = re.compile(
    r'href="(https://dl\.opensubtitles\.org/en/download/file/\d+)"'
)


def _to_site_code(language):
    """Convert a subzero/babelfish Language into an OpenSubtitles.org
    SubLanguageID (e.g. 'eng', 'pob', 'scc')."""
    return _LANGUAGE_CONVERTER.convert(language.alpha3, language.country, language.script)


def _from_site_code(code):
    """Convert an OpenSubtitles.org SubLanguageID into a Language, or None
    if it isn't a recognized code."""
    try:
        return Language.fromcode(code, "szopensubtitles")
    except (LanguageReverseError, ValueError):
        return None


def _build_supported_languages():
    languages = set()
    for code in _LANGUAGE_CONVERTER.codes:
        language = _from_site_code(code)
        if language is not None:
            languages.add(language)
    return languages


_SUPPORTED_LANGUAGES = _build_supported_languages()

_TEXT_ENCODINGS = ("utf-8", "utf-8-sig", "cp1252", "iso-8859-1", "iso-8859-2")


def _extract_raw_subtitle(content):
    """Validate and return `content` as-is if it looks like a plain
    (uncompressed, non-archived) subtitle file, trying a few common
    encodings. Returns None if it doesn't look like a subtitle.

    This purposely parses in-memory (via ``pysubs2.SSAFile.from_string``)
    instead of round-tripping through a temporary file, since ``content``
    is only used to *validate* the format here.
    """
    for encoding in _TEXT_ENCODINGS:
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            continue

        try:
            pysubs2.SSAFile.from_string(text)
        except Exception:
            continue

        return fix_line_ending(content)

    return None


class OpenSubtitlesOrgSubtitle(Subtitle):
    provider_name = "opensubtitlesorg"
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(
        self,
        language,
        page_link,
        download_id,
        release_info,
        hearing_impaired=False,
        uploader=None,
        trusted=False,
        download_count=0,
        imdb_match=False,
        episode_number=None,
    ):
        super().__init__(language, hearing_impaired=hearing_impaired, page_link=page_link)

        self.download_id = download_id
        self.release_info = release_info
        self.uploader = uploader
        self.trusted = trusted
        self.download_count = download_count
        self.episode_number = episode_number
        self.episode_title = None

        self.matches = set(
            ("title", "year")
            if episode_number is None
            else ("title", "series", "season", "episode")
        )
        if imdb_match:
            self.matches.add("imdb_id")

    def get_matches(self, video):
        update_matches(self.matches, video, self.release_info)
        return self.matches

    @property
    def id(self):
        return str(self.download_id)


class OpenSubtitlesOrgProvider(Provider):
    """Provider for opensubtitles.org's public search/download flow.

    Does not require, and does not support, a username or password.
    """

    provider_name = "opensubtitlesorg"

    languages = _SUPPORTED_LANGUAGES
    video_types = (Episode, Movie)
    subtitle_class = OpenSubtitlesOrgSubtitle

    def __init__(self, user_agent=None, verify_ssl=True):
        self._user_agent = (user_agent or "").strip() or _DEFAULT_USER_AGENT
        self._verify_ssl = verify_ssl
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.verify = self._verify_ssl
        self.session.headers["User-Agent"] = self._user_agent
        self.session.headers["Accept-Language"] = "en-US,en;q=0.9"

    def terminate(self):
        if self.session is not None:
            self.session.close()

    def _get_soup(self, url):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except Exception as error:
            logger.debug("Request to %s failed: %s", url, error)
            return None

        return bso(response.content, "html.parser")

    def _search(self, query, language_code):
        quoted = urllib.parse.quote(query.strip())
        url = f"{_SERVER_URL}/en/search/moviename-{quoted}/sublanguageid-{language_code}"
        return self._get_soup(url)

    @staticmethod
    def _parse_rows(soup):
        """Parse every subtitle row of a search results page.

        opensubtitles.org lists each subtitle as a ``<tr id="name{id}">``
        row inside (possibly several, one per matched title) results
        tables. Each row independently carries the movie/episode title,
        year, IMDB link, language, release name and download link, so
        rows can be parsed and filtered without needing to track which
        results table/movie group they came from.
        """
        if soup is None:
            return

        for row in soup.select('tr[id^="name"]'):
            row_id_match = _ROW_ID_RE.match(row.get("id", ""))
            if not row_id_match:
                continue
            subtitle_id = row_id_match.group(1)

            title_link = row.select_one('a[href*="/en/subtitles/"]')
            if title_link is None:
                continue

            href = title_link.get("href", "")
            raw_title = title_link.get_text(" ", strip=True)
            title_attr = (title_link.get("title") or "").strip()
            clean_title = _TITLE_PREFIX_RE.sub("", title_attr).strip()
            if not clean_title:
                clean_title = _YEAR_RE.sub("", raw_title).strip()

            year_match = _YEAR_RE.search(raw_title)
            year = int(year_match.group(1)) if year_match else None

            title_cell = title_link.find_parent("td")
            release_span = title_cell.find("span") if title_cell is not None else None
            if release_span is not None:
                release_info = (release_span.get("title") or release_span.get_text(strip=True)).strip()
            else:
                release_info = raw_title

            lang_link = row.select_one('a[href*="sublanguageid-"]')
            lang_code_match = _LANG_CODE_RE.search(lang_link.get("href", "")) if lang_link else None
            language = _from_site_code(lang_code_match.group(1)) if lang_code_match else None
            if language is None:
                logger.debug("Could not determine language for row: %s", href)
                continue

            # The download count is shown as a plain "{n}x" link elsewhere in
            # the row (its target is a dead-end landing page and is
            # intentionally not used here -- see download_subtitle()/
            # _get_download_url() for the real download mechanism).
            download_count = 0
            for anchor in row.find_all("a"):
                if _DOWNLOAD_COUNT_RE.match(anchor.get_text(strip=True)):
                    download_count = int(anchor.get_text(strip=True)[:-1])
                    break

            imdb_link = row.select_one('a[href*="imdb.com/title/tt"]')
            imdb_id_match = _IMDB_ID_RE.search(imdb_link.get("href", "")) if imdb_link else None
            imdb_id = f"tt{imdb_id_match.group(1)}" if imdb_id_match else None

            hearing_impaired = row.find("img", attrs={"src": re.compile("hearing_impaired")}) is not None
            trusted = row.find("img", attrs={"src": re.compile("from_trusted")}) is not None

            uploader_link = row.select_one('a[href*="/en/profile/"]')
            uploader = uploader_link.get_text(strip=True) if uploader_link else None

            yield {
                "title": clean_title,
                "year": year,
                "release_info": release_info,
                "language": language,
                "download_id": subtitle_id,
                "download_count": download_count,
                "imdb_id": imdb_id,
                "hearing_impaired": hearing_impaired,
                "trusted": trusted,
                "uploader": uploader,
                "page_link": _SERVER_URL + href,
            }

    @staticmethod
    def _titles_match(candidate, titles):
        candidate = sanitize(candidate)
        return any(candidate == sanitize(title) for title in titles if title)

    def _find_movie_subtitles(self, video, languages):
        subtitles = []
        titles = [video.title] + list(getattr(video, "alternative_titles", None) or [])

        for language in languages:
            try:
                code = _to_site_code(language)
            except Exception as error:
                logger.debug("Could not convert language %s to a site code: %s", language, error)
                continue

            for row in self._parse_rows(self._search(video.title, code)):
                if row["language"] != language:
                    continue

                imdb_matched = bool(video.imdb_id) and row["imdb_id"] == video.imdb_id
                if video.imdb_id and row["imdb_id"] and not imdb_matched:
                    # Confirmed IMDB id mismatch: definitely a different movie.
                    continue

                if not imdb_matched:
                    if row["year"] and video.year and row["year"] != video.year:
                        continue
                    if not self._titles_match(row["title"], titles):
                        continue

                subtitles.append(
                    self.subtitle_class(
                        language,
                        row["page_link"],
                        row["download_id"],
                        row["release_info"],
                        hearing_impaired=row["hearing_impaired"],
                        uploader=row["uploader"],
                        trusted=row["trusted"],
                        download_count=row["download_count"],
                        imdb_match=imdb_matched,
                    )
                )

        return subtitles

    def _find_episode_subtitles(self, video, languages):
        subtitles = []
        titles = [video.series] + list(getattr(video, "alternative_series", None) or [])
        queries = [
            f"{video.series} S{video.season:02d}E{video.episode:02d}",
            video.series,
        ]

        for language in languages:
            try:
                code = _to_site_code(language)
            except Exception as error:
                logger.debug("Could not convert language %s to a site code: %s", language, error)
                continue

            rows = []
            for query in queries:
                rows = list(self._parse_rows(self._search(query, code)))
                if rows:
                    break

            for row in rows:
                if row["language"] != language:
                    continue

                if not self._titles_match(row["title"], titles):
                    # The row's "title" for an episode result is normally the
                    # series (or series + episode) name.
                    guess = guessit(row["title"], {"type": "episode"})
                    if not self._titles_match(guess.get("title") or "", titles):
                        continue

                guess = guessit(row["release_info"], {"type": "episode"})
                if guess.get("season") != video.season or guess.get("episode") != video.episode:
                    continue

                imdb_matched = bool(video.series_imdb_id) and row["imdb_id"] == video.series_imdb_id

                subtitle = self.subtitle_class(
                    language,
                    row["page_link"],
                    row["download_id"],
                    row["release_info"],
                    hearing_impaired=row["hearing_impaired"],
                    uploader=row["uploader"],
                    trusted=row["trusted"],
                    download_count=row["download_count"],
                    imdb_match=imdb_matched,
                    episode_number=video.episode,
                )
                subtitle.episode_title = video.title
                subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        languages = {language for language in languages if language in self.languages}
        if not languages:
            return []

        if isinstance(video, Episode):
            return self._find_episode_subtitles(video, languages)

        return self._find_movie_subtitles(video, languages)

    def _get_download_url(self, subtitle):
        """Fetch the subtitle's detail page and extract the real,
        per-subtitle download URL (dl.opensubtitles.org/en/download/file/
        {token}). This token is dynamic and only exposed on the detail
        page -- it cannot be derived from the search-results subtitle id.
        """
        if not subtitle.page_link:
            raise APIThrottled(
                f"Cannot download subtitle {subtitle.id}: no detail page link available"
            )

        response = self.session.get(subtitle.page_link, timeout=30)
        response.raise_for_status()

        html = response.content.decode("utf-8", errors="replace")
        match = _DOWNLOAD_TOKEN_RE.search(html)
        if not match:
            raise APIThrottled(
                f"Could not find a download link on the detail page for subtitle {subtitle.id}"
            )

        return match.group(1)

    def download_subtitle(self, subtitle):
        download_url = self._get_download_url(subtitle)

        response = self.session.get(download_url, timeout=30, allow_redirects=True)
        response.raise_for_status()

        # `requests` already transparently decodes a standard HTTP
        # Content-Encoding: gzip response; `content` below is only for the
        # (less common) case of a raw gzip-compressed *file* being served
        # as the payload itself, with no Content-Encoding header set.
        content = response.content

        if content[:2] == b"\x1f\x8b":
            try:
                content = gzip.decompress(content)
            except OSError as error:
                raise APIThrottled(
                    f"Invalid gzip response for subtitle {subtitle.id}: {error}"
                )

        archive_stream = io.BytesIO(content)

        if rarfile.is_rarfile(archive_stream):
            archive = rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            archive = zipfile.ZipFile(archive_stream)
        else:
            archive = None

        if archive is not None:
            subtitle_content = get_subtitle_from_archive(
                archive,
                episode=subtitle.episode_number,
                episode_title=subtitle.episode_title,
            )
        else:
            # Not an archive: a single, uncompressed subtitle file served
            # directly (the common case for this endpoint).
            subtitle_content = _extract_raw_subtitle(content)

        if subtitle_content is None:
            raise APIThrottled(
                f"Could not extract subtitle {subtitle.id}: unrecognized response format"
            )

        subtitle.content = subtitle_content
