# -*- coding: utf-8 -*-
"""Legendei.net subtitle provider (Brazilian Portuguese).

Site mechanics:
    * Search:   GET https://legendei.net/?s=<query>  (WordPress search)
    * Detail:   each result links to https://legendei.net/<slug>/, which holds the release
                name in its <h1> and a download anchor ending in ``?download=<id>``.
    * Download: GET <detail_url>?download=<id> 302-redirects to a ``.zip`` under
                ``wp-content/uploads/`` that contains a single ``.srt``.
    * Inline JS rewrites the download anchor through ``btoa()`` into an ad-gate; since we read
                the raw href without running JS, we always get the direct link.
"""
import io
import logging
import os
import re
import zipfile
from time import sleep
from urllib.parse import quote

from guessit import guessit
from requests.exceptions import RequestException

from subliminal.subtitle import fix_line_ending
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Episode, Movie
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils
from subliminal_patch.score import get_scores
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language

logger = logging.getLogger(__name__)

# Cap on detail-page fetches per search; each is an extra request to the site.
MAX_DETAIL_FETCHES = 5
# Seconds between requests.
REQUEST_DELAY = 1
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}

# href markers for the real download link (before JS rewrites it into an ad-gate).
DOWNLOAD_HREF_MARKERS = ('?download=', '?dl_', '/zip-attachments.php')

# Flag and pictograph emojis that decorate titles.
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"  # regional indicator symbols (flags)
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000027BF"
    "]+",
    flags=re.UNICODE,
)

# Matches a result anchor pointing to a detail page.
# e.g. <a href="https://legendei.net/oppenheimer-2023-1080p-bluray/" title="Oppenheimer 2023 1080p Bluray">
RESULT_RE = re.compile(
    r'<a[^>]+href="(https?://(?:www\.)?legendei\.net/(?!category/|tag/|page/|author/|feed/)'
    r'[^"?#]+/)"[^>]*?title="([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)
DOWNLOAD_ID_RE = re.compile(r'\?download=(\d+)', re.IGNORECASE)
H1_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)


class LegendeiSubtitle(Subtitle):
    """Legendei.net Subtitle."""
    provider_name = 'legendei'

    def __init__(self, language, release_name, page_link, download_link, file_id,
                 video=None, uploader=None):
        super(LegendeiSubtitle, self).__init__(language, page_link=page_link)
        self.release_name = release_name
        self.release_info = release_name
        self.page_link = page_link
        self.download_link = download_link
        self.file_id = file_id
        self.video = video
        self.uploader = uploader
        self.matches = set()
        # season packs ("Temporada Completa") bundle several episodes in one archive
        self.is_pack = isinstance(video, Episode) and bool(
            re.search(r'temporada\s+completa|complete\s+season|season\s+pack', release_name or '',
                      re.IGNORECASE))

    @property
    def id(self):
        # attachment id when available, otherwise the (unique) download link
        return self.file_id or self.download_link

    def get_matches(self, video):
        matches = set()

        release = sanitize(self.release_name)
        type_ = 'episode' if isinstance(video, Episode) else 'movie'

        if isinstance(video, Episode):
            for series_name in [video.series] + video.alternative_series:
                if sanitize(series_name) in release:
                    matches.update(['series'])
                    break
            if video.season and 's{:02d}'.format(video.season) in release:
                matches.update(['season'])
            if video.episode and 'e{:02d}'.format(video.episode) in release:
                matches.update(['episode'])
            if video.title and sanitize(video.title) in release:
                matches.update(['title'])
        else:
            for movie_name in [video.title] + video.alternative_titles:
                if sanitize(movie_name) in release:
                    matches.update(['title'])
                    break
            if video.year and '{:04d}'.format(video.year) in release:
                matches.update(['year'])

        if video.release_group and \
                sanitize_release_group(video.release_group) in sanitize_release_group(release):
            matches.update(['release_group'])

        utils.update_matches(matches, video, self.release_name, split="\n")

        self.matches = matches
        return matches


class LegendeiProvider(Provider):
    """Legendei.net Provider."""
    languages = {Language('por', 'BR')}
    video_types = (Episode, Movie)

    site = 'https://legendei.net'
    search_url = site + '/?s={query}'

    def __init__(self):
        self.session = None

    def initialize(self):
        logger.debug("Legendei :: Creating session for requests")
        self.session = RetryingCFSession()
        self.session.headers.update(BROWSER_HEADERS)

    def terminate(self):
        if self.session:
            self.session.close()

    # ------------------------------------------------------------------ helpers

    def _fetch_html(self, url):
        """GET *url* and return its HTML body, or None on failure."""
        try:
            resp = self.session.get(url, timeout=30)
        except RequestException as e:
            logger.warning("Legendei :: Request to %s failed: %r", url, e)
            return None
        if resp.status_code != 200:
            logger.warning("Legendei :: Unexpected status %s for %s", resp.status_code, url)
            return None
        return resp.text

    @staticmethod
    def _clean_release_name(raw):
        """Normalise an <h1>/title string into a clean release name."""
        if not raw:
            return ''
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^legenda\s+', '', text, flags=re.IGNORECASE)
        text = EMOJI_RE.sub('', text).strip()
        return text

    @staticmethod
    def _parse_search_results(html):
        """Yield (detail_url, title) tuples from a search results page."""
        seen = set()
        for match in RESULT_RE.finditer(html or ''):
            detail_url = match.group(1).strip()
            title = match.group(2).strip()
            if detail_url in seen:
                continue
            seen.add(detail_url)
            yield detail_url, title

    @staticmethod
    def _parse_detail_page(html, fallback_title):
        """Extract (release_name, download_link, file_id) from a detail page, or None."""
        if not html:
            return None

        release_name = ''
        h1 = H1_RE.search(html)
        if h1:
            release_name = LegendeiProvider._clean_release_name(h1.group(1))
        if not release_name:
            release_name = LegendeiProvider._clean_release_name(fallback_title or '')

        # the WordPress attachment anchor with ?download=<id>
        dl_match = re.search(r'href="([^"]*\?download=\d+)"', html, re.IGNORECASE)
        if not dl_match:
            for marker in DOWNLOAD_HREF_MARKERS:
                m = re.search(r'href="([^"]*%s[^"]*)"' % re.escape(marker), html, re.IGNORECASE)
                if m:
                    dl_match = m
                    break
        if not dl_match:
            return None

        download_link = dl_match.group(1).strip()
        file_id_match = DOWNLOAD_ID_RE.search(download_link)
        file_id = file_id_match.group(1) if file_id_match else None

        return release_name, download_link, file_id

    # ------------------------------------------------------------------ provider API

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def _search_queries(self, video):
        """Yield search queries to try for *video*, in priority order.

        For episodes, search the exact episode first; if only a season pack is available, the
        caller falls back to the broader ``series + season`` query.
        """
        if isinstance(video, Episode):
            yield quote('{series} S{season:02d}E{episode:02d}'.format(
                series=video.series, season=video.season, episode=video.episode))
            yield quote('{series} S{season:02d}'.format(series=video.series, season=video.season))
            return
        query = video.title
        if video.year:
            query = '{} {:04d}'.format(query, video.year)
        yield quote(query)

    def query(self, video, languages):
        # legendei only serves pt-BR; nothing to do unless it was requested
        wanted = self.languages & set(languages)
        if not wanted:
            return []
        language = next(iter(wanted))

        subtitles = []
        seen_detail_urls = set()
        fetched = 0

        for query_text in self._search_queries(video):
            if fetched >= MAX_DETAIL_FETCHES:
                break

            search_url = self.search_url.format(query=query_text)
            logger.debug("Legendei :: Searching %s", search_url)
            sleep(REQUEST_DELAY)
            html = self._fetch_html(search_url)
            if not html:
                logger.warning("Legendei :: Could not retrieve search results for %r",
                               getattr(video, 'name', video))
                continue

            results = list(self._parse_search_results(html))
            logger.debug("Legendei :: Found %d result(s) for %r", len(results), query_text)
            if not results:
                continue

            for detail_url, title in results:
                if fetched >= MAX_DETAIL_FETCHES:
                    break
                if detail_url in seen_detail_urls:
                    continue
                seen_detail_urls.add(detail_url)
                sleep(REQUEST_DELAY)
                detail_html = self._fetch_html(detail_url)
                # count every fetch attempt so a run of unparseable pages cannot exceed the cap
                fetched += 1
                parsed = self._parse_detail_page(detail_html, title)
                if not parsed:
                    continue
                release_name, download_link, file_id = parsed

                subtitle = LegendeiSubtitle(
                    language=language,
                    release_name=release_name,
                    page_link=detail_url,
                    download_link=download_link,
                    file_id=file_id,
                    video=video,
                )
                subtitle.get_matches(video)
                subtitles.append(subtitle)

            # stop as soon as one query produced results
            if subtitles:
                break

        return subtitles

    def download_subtitle(self, subtitle):
        logger.debug("Legendei :: Downloading subtitle %r", subtitle)
        try:
            sleep(REQUEST_DELAY)
            # follow the redirect to the actual archive
            res = self.session.get(subtitle.download_link, timeout=30)
            res.raise_for_status()
        except RequestException as e:
            logger.error("Legendei :: Download request failed: %r", e)
            return

        content = res.content
        archive_stream = io.BytesIO(content)
        if zipfile.is_zipfile(archive_stream):
            logger.debug("Legendei :: Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = self._pick_from_archive(archive, subtitle)
            if subtitle_content is None:
                logger.error("Legendei :: No subtitle file inside archive for %r", subtitle)
                return
            subtitle.content = fix_line_ending(subtitle_content)
            subtitle.normalize()
            return subtitle

        # not a zip: maybe a raw .srt (rare) or an error page
        head = content.lstrip(b'\xef\xbb\xbf')[:6].lower()
        if head[:1] == b'1' or content[:6].lower() == b'webvtt':
            logger.debug("Legendei :: Treating response as a raw subtitle file")
            subtitle.content = fix_line_ending(content)
            subtitle.normalize()
            return subtitle

        logger.error("Legendei :: Unexpected download payload (%d bytes) from %s",
                     len(content), subtitle.download_link)

    @staticmethod
    def _pick_from_archive(archive, subtitle):
        """Return the best subtitle bytes from *archive* (single-file fast path + scoring)."""
        names = [n for n in archive.namelist()
                 if not os.path.split(n)[-1].startswith('.') and
                 n.lower().endswith(('.srt', '.sub', '.ssa', '.ass'))]
        if not names:
            return None
        if len(names) == 1:
            return archive.read(names[0])

        # several candidates: score each with guessit against the video
        video = getattr(subtitle, 'video', None)
        best_name, best_score = names[0], -1
        for name in names:
            try:
                score = 0
                if video is not None:
                    scores = get_scores(video)
                    matches = guess_matches(video, guessit(name))
                    score = sum(scores.get(m, 0) for m in matches)
                if subtitle.release_name and \
                        sanitize_release_group(subtitle.release_name).lower() in \
                        sanitize_release_group(name).lower():
                    score += 1
            except Exception:
                score = 0
            if score > best_score:
                best_name, best_score = name, score
        return archive.read(best_name)
