# coding=utf-8

from __future__ import absolute_import, unicode_literals

import io
import logging
import os
import re
from time import sleep
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from bs4 import BeautifulSoup
from guessit import guessit
from requests.exceptions import HTTPError, RequestException

from subzero.language import Language
from subliminal.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ProviderError,
    ServiceUnavailable,
)
from subliminal.subtitle import fix_line_ending
from subliminal.video import Episode, Movie

from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches

from . import Provider, reinitialize_on_error

logger = logging.getLogger(__name__)

SITE = "https://pipocas.tv"
LOGIN_URL = SITE + "/login"
SEARCH_URL = SITE + "/legendas"
DOWNLOAD_URL = SITE + "/legendas/download/{id}"

TOKEN_RE = re.compile(r'<meta name="csrf-token" content="(.+?)">', re.IGNORECASE)


# Mapping between Language objects and pipocas.tv language names
PIPOCAS_LANGUAGE_MAP = {
    # Portuguese (Portugal)
    ("por", None): "portugues",
    ("por", "PT"): "portugues",
    # Portuguese (Brazil)
    ("por", "BR"): "brasileiro",
    # English
    ("eng", None): "ingles",
    ("eng", "US"): "ingles",
    ("eng", "GB"): "ingles",
    # Spanish
    ("spa", None): "espanhol",
    ("spa", "ES"): "espanhol",
    ("spa", "MX"): "espanhol",
}


def get_pipocas_language(language):
    """Map a Language to pipocas.tv internal language string."""
    key = (language.alpha3, language.country)
    if key in PIPOCAS_LANGUAGE_MAP:
        return PIPOCAS_LANGUAGE_MAP[key]

    key = (language.alpha3, None)
    return PIPOCAS_LANGUAGE_MAP.get(key)


class PipocasSubtitle(Subtitle):
    """Single subtitle entry from pipocas.tv."""

    provider_name = "pipocas"
    hash_verifiable = False

    def __init__(self, language, video, sub_id, release, hits, uploader, score_stars):
        super(PipocasSubtitle, self).__init__(language)
        self.video = video
        self.sub_id = sub_id
        self.release = release or ""
        self.releases = self.release_info = self.release
        self.matches = set()

        if isinstance(video, Episode):
            self.season = video.season
            self.episode = video.episode
            self.asked_for_episode = video.episode
        else:
            self.season = None
            self.episode = None
            self.asked_for_episode = None

        self.asked_for_release_group = getattr(video, "release_group", None)
        self.is_pack = False
        self.hits = hits or 0
        self.uploader = uploader or "pipocas-bot"
        self.user_score = score_stars or 0
        self.page_link = DOWNLOAD_URL.format(id=sub_id)

    @property
    def id(self):
        # Stable internal ID for caching/history
        return f"{self.provider_name}_{self.sub_id}"

    def get_matches(self, video):
        """Compute match set for scoring."""
        matches = set()

        # Basic movie/episode matching on name/year
        if isinstance(video, Episode):
            if video.series and video.series.lower() in self.release.lower():
                matches.add("series")
            if video.season and f"s{video.season:02d}".lower() in self.release.lower():
                matches.add("season")
            if video.episode and f"e{video.episode:02d}".lower() in self.release.lower():
                matches.add("episode")
        else:
            if video.title and video.title.lower() in self.release.lower():
                matches.add("title")

        if video.year and str(video.year) in self.release:
            matches.add("year")

        # Let guessit refine matches
        try:
            guessed = guessit(self.release, {"type": "episode" if isinstance(video, Episode) else "movie"})
            matches |= guess_matches(video, guessed)
        except Exception:
            pass

        self.matches = matches
        return matches


class PipocasProvider(Provider, ProviderSubtitleArchiveMixin):
    """pipocas.tv provider for subliminal_patch."""

    languages = {
        Language("por"),          # Portuguese (Portugal)
        Language("por", "BR"),    # Portuguese (Brazil)
        Language("eng"),          # English
        Language("spa"),          # Spanish
    }

    video_types = (Episode, Movie)
    subtitle_class = PipocasSubtitle
    SEARCH_DELAY = 5

    headers = {
        "User-Agent": os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Origin": SITE,
        "Referer": SITE,
        "Connection": "keep-alive",
    }

    def __init__(self, username=None, password=None):
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError("Pipocas.tv :: username and password must both be set")

        self.username = username
        self.password = password
        self.session = None

    def initialize(self):
        """Create HTTP session and log in."""
        if not self.username or not self.password:
            raise ConfigurationError("Pipocas.tv :: username/password not configured")

        # Session is injected to this module as Session by providers/__init__.py
        self.session = Session()
        self.session.headers.update(self.headers)

        self._login()

    def terminate(self):
        if self.session:
            self.session.close()

    def _login(self):
        """Perform CSRF-based login."""
        logger.debug("Pipocas.tv :: requesting login page")
        res = self.session.get(LOGIN_URL)
        res.raise_for_status()

        token_match = TOKEN_RE.search(res.text)
        if not token_match:
            raise ServiceUnavailable("Pipocas.tv :: unable to find CSRF token on login page")

        token = token_match.group(1)
        payload = {
            "username": self.username,
            "password": self.password,
            "_token": token,
        }

        logger.debug("Pipocas.tv :: posting login form")
        res = self.session.post(LOGIN_URL, data=payload)
        res.raise_for_status()

        if "Cria uma conta" in res.text:
            raise AuthenticationError("Pipocas.tv :: login failed, check credentials")

        logger.info("Pipocas.tv :: login successful")

    # ------------------------------------------------------------------ search

    def _build_search_query(self, video):
        """Build search string from video metadata."""
        if isinstance(video, Episode):
            if video.series and video.season and video.episode:
                return f"{video.series} S{video.season:02d}E{video.episode:02d}"
            if video.series:
                return video.series
        else:
            if video.title:
                return video.title

        if video.name:
            return os.path.splitext(os.path.basename(video.name))[0]

        return ""

    def _parse_details_page(self, video, url, language):
        """Parse /legendas/info/<id> page into a PipocasSubtitle."""
        res = self.session.get(url)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Release name
        release = ""
        title_h3 = soup.find("h3", class_="title")
        if title_h3:
            span = title_h3.find("span", class_="font-normal")
            if span and span.text:
                release = span.text.strip()

        # Subtitle ID
        sub_id = None
        for a in soup.find_all("a", href=True):
            m = re.search(r"/legendas/download/([^\"']+)", a["href"])
            if m:
                sub_id = m.group(1)
                break

        if not sub_id:
            return None

        # Hits
        hits = 0
        hits_span = soup.find("span", class_="hits hits-pd")
        if hits_span:
            div = hits_span.find("div")
            if div and div.text:
                try:
                    hits = int(div.text.strip())
                except ValueError:
                    hits = 0

        # Uploader
        uploader = None
        span_color = soup.find("span", style=re.compile(r"color:\s*#[0-9A-Fa-f]{3,6}"))
        if span_color and span_color.text:
            uploader = span_color.text.strip()

        # Rating X/Y
        rating_val = 0
        rating_h2 = soup.find("h2", class_="mt-3 text-center")
        if rating_h2 and rating_h2.text:
            m = re.search(r"(\d+)\s*/\s*\d+", rating_h2.text)
            if m:
                try:
                    rating_val = int(m.group(1))
                except ValueError:
                    rating_val = 0

        # Convert rating + hits to 0–5 stars (similar to Kodi addon)
        if rating_val == 0:
            hit_factor = 0
        else:
            hit_factor = min(hits / 100.0, 5.0)
        score_stars = round((rating_val + hit_factor) / 2.0)

        return PipocasSubtitle(
            language=language,
            video=video,
            sub_id=sub_id,
            release=release,
            hits=hits,
            uploader=uploader,
            score_stars=score_stars,
        )

    def _search_language(self, video, language):
        """Search for one language and return a list of PipocasSubtitle."""
        site_lang = get_pipocas_language(language)
        if not site_lang:
            logger.debug("Pipocas.tv :: language %s not supported by site", language)
            return []

        query = self._build_search_query(video)
        if not query:
            return []

        params = {
            "t": "rel",
            "l": site_lang,
            "page": 1,
            "s": query,
        }

        logger.debug("Pipocas.tv :: searching '%s' [%s]", query, site_lang)
        sleep(self.SEARCH_DELAY)

        res = self.session.get(SEARCH_URL, params=params)
        res.raise_for_status()

        if "Cria uma conta" in res.text:
            raise AuthenticationError("Pipocas.tv :: not authenticated during search")

        soup = BeautifulSoup(res.text, "html.parser")
        results = []

        for a in soup.find_all("a", href=True, class_="text-dark no-decoration"):
            if "/legendas/info/" not in a["href"]:
                continue

            details_href = a["href"]
            if not details_href.startswith("http"):
                details_href = SITE.rstrip("/") + details_href

            sub = self._parse_details_page(video, details_href, language)
            if sub:
                results.append(sub)

        return results

    def list_subtitles(self, video, languages):
        """Main entry point used by subliminal."""
        all_subs = []
        for lang in languages:
            try:
                subs = self._search_language(video, lang)
                all_subs.extend(subs)
            except (HTTPError, RequestException, AuthenticationError, ServiceUnavailable):
                raise
            except Exception as e:
                logger.error("Pipocas.tv :: error searching %s: %r", lang, e)

        all_subs.sort(key=lambda s: (s.user_score, s.hits), reverse=True)
        return all_subs

    # ---------------------------------------------------------------- download

    @reinitialize_on_error((RequestException,), attempts=1)
    def download_subtitle(self, subtitle):
        """Download subtitle and fill subtitle.content."""
        logger.info("Pipocas.tv :: downloading %s", subtitle.page_link)

        res = self.session.get(subtitle.page_link, timeout=10)
        res.raise_for_status()

        if "Cria uma conta" in res.text:
            raise AuthenticationError("Pipocas.tv :: not authenticated during download")

        data = res.content
        if not data:
            raise ServiceUnavailable("Pipocas.tv :: empty download response")

        archive_stream = io.BytesIO(data)

        if is_rarfile(archive_stream):
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            archive = ZipFile(archive_stream)
        else:
            subtitle.content = fix_line_ending(data)

            if subtitle.is_valid():
                return subtitle

            subtitle.content = None
            raise ProviderError("Pipocas.tv :: unidentified archive type")

        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

        if not subtitle.content:
            raise ServiceUnavailable("Pipocas.tv :: no suitable subtitle file in archive")

        return subtitle
