# -*- coding: utf-8 -*-
from __future__ import absolute_import

import io
import logging
import os
import re
from random import randint
from urllib.parse import quote, urljoin

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subzero.language import Language

from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal.exceptions import DownloadLimitExceeded, ProviderError
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import TooManyRequests
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST, get_archive_from_bytes

logger = logging.getLogger(__name__)

language_converters.register('subhd = subliminal_patch.converters.subhd:SubhdConverter')

supported_languages = list(language_converters['subhd'].to_subhd.keys())


class SubhdSubtitle(Subtitle):
    """SubHD Subtitle."""

    provider_name = 'subhd'

    def __init__(self, language, page_link, sid, version, session=None, year=None, sub_format=None, uploader=None):
        super(SubhdSubtitle, self).__init__(language, page_link=page_link)
        self.sid = sid
        self.version = version
        self.release_info = version
        self.hearing_impaired = False
        self.encoding = 'utf-8'
        self.session = session
        self.year = year
        self.sub_format = sub_format
        self.uploader = uploader
        self.matches = set()
        self.video = None

    @property
    def id(self):
        return self.sid or self.page_link

    def get_matches(self, video):
        self.video = video
        if self.year and video.year and self.year == video.year:
            self.matches.add('year')

        if isinstance(video, Episode):
            info = guessit(self.version, {'type': 'episode'})
            self.matches |= guess_matches(video, info)
            if not video.year and all(item in self.matches for item in ['series', 'season', 'episode']):
                self.matches |= {'year'}
        elif isinstance(video, Movie):
            self.matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}))

        return self.matches


def _has_keyword(name: str, keywords: list[str]) -> bool:
    """Return True if any keyword occurs in a file name.

    Purely alphanumeric ASCII keywords must not be adjacent to another ASCII letter or digit, so
    ``sc`` matches ``show.sc.srt`` but not ``scrubs``. Keywords with punctuation or non-ASCII
    characters are matched as plain substrings.

    :param str name: Lower-cased file name to search.
    :param list[str] keywords: Keywords to look for.
    :return: True if at least one keyword matches.
    :rtype: bool
    """
    for kw in keywords:
        if kw.isascii() and kw.isalnum():
            if re.search(r'(?<![a-z0-9])%s(?![a-z0-9])' % re.escape(kw), name):
                return True
        elif kw in name:
            return True
    return False


def _raise_if_rate_limited(response, exc_cls: type[ProviderError], message: str) -> None:
    """Raise ``exc_cls`` if the HTTP response is a 429 Too Many Requests.

    :param response: HTTP response object exposing ``status_code``.
    :param type[ProviderError] exc_cls: Exception class to raise on a rate-limited response.
    :param str message: Message attached to the raised exception.
    :raises ProviderError: ``exc_cls`` when the status code is 429.
    :return: None
    :rtype: None
    """
    if response.status_code == 429:
        raise exc_cls(message)


def _extract_subtitle_from_archive(archive, language, video=None):
    """Extract best matching subtitle file from zip/rar archive according to language and episode."""
    extract_subname = None
    max_score = -1

    target_episode = getattr(video, 'episode', None) if isinstance(video, Episode) else None

    for subname in archive.namelist():
        basename = os.path.basename(subname)
        if basename.startswith('.') or basename.startswith('__MACOSX'):
            continue

        if not subname.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        score = 0

        # Episode number matching for TV episodes
        if target_episode is not None:
            ep_patterns = [
                r'[Ss]\d+[Ee]%02d\b' % target_episode,
                r'[Ee][Pp]?%02d\b' % target_episode,
                r'[Ee][Pp]?%d\b' % target_episode,
                r'第%d[集话話期]' % target_episode,
                r'第%02d[集话話期]' % target_episode,
                r'\[%02d\]' % target_episode,
                r'\[%d\]' % target_episode,
            ]
            if any(re.search(pat, basename, re.IGNORECASE) for pat in ep_patterns):
                score += 50
            else:
                other_ep = re.search(r'[Ee][Pp]?(\d{1,3})\b', basename, re.IGNORECASE)
                if other_ep and int(other_ep.group(1)) != target_episode:
                    score -= 100

        # Language scoring
        lower_name = basename.lower()
        lang_alpha3 = getattr(language, 'alpha3', None)
        lang_country = getattr(language, 'country', None)

        if lang_alpha3 == 'zho' and (lang_country == 'CN' or not lang_country):
            if _has_keyword(lower_name, ['简', 'chs', 'gb', 'gbk', 'gb2312', 'sc', 'zh-cn', 'zh-hans']):
                score += 15
            if _has_keyword(lower_name, ['中英', '简英', '双语']):
                score += 10
            if _has_keyword(lower_name, ['繁体', 'cht', 'big5', 'tc', 'zh-tw', 'zh-hant']) and not _has_keyword(lower_name, ['简', 'chs']):
                score -= 10
        elif lang_alpha3 == 'zho' and lang_country in ('TW', 'HK'):
            if _has_keyword(lower_name, ['繁', 'cht', 'big5', 'tc', 'zh-tw', 'zh-hant']):
                score += 15
            if _has_keyword(lower_name, ['繁英', '双语']):
                score += 10
            if _has_keyword(lower_name, ['简体', 'chs', 'gb', 'gbk', 'gb2312', 'sc', 'zh-cn', 'zh-hans']) and not _has_keyword(lower_name, ['繁', 'cht']):
                score -= 10
        elif lang_alpha3 == 'eng':
            if _has_keyword(lower_name, ['eng', 'en.', '.en', 'english']):
                score += 15
            if _has_keyword(lower_name, ['双语', '中英', '简英', '繁英']):
                score += 10

        # Format scoring
        if lower_name.endswith(('.ass', '.ssa')):
            score += 3
        elif lower_name.endswith('.srt'):
            score += 2

        if score > max_score:
            max_score = score
            extract_subname = subname

    if extract_subname is not None and max_score > -50:
        logger.debug("Selected %r from archive with score %d", extract_subname, max_score)
        return archive.read(extract_subname)

    sup_files = [s for s in archive.namelist() if s.lower().endswith('.sup')]
    if sup_files:
        logger.debug("SubHD archive only contains unsupported SUP/PGS files: %r", sup_files)
    return None


class SubhdProvider(Provider):
    """SubHD Provider."""

    languages = {Language(*l) for l in supported_languages}
    languages.update({Language.rebuild(l, hi=True) for l in languages})
    video_types = (Episode, Movie)

    subtitle_class = SubhdSubtitle

    def __init__(self, base_url=None):
        self.server_url = (base_url.rstrip('/') if base_url else 'https://subhd.tv')
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        self.session.headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'

    def terminate(self):
        if self.session:
            self.session.close()

    def _parse_search_page(self, html, languages, default_year=None):
        subtitles = []
        soup = ParserBeautifulSoup(html, ['lxml', 'html.parser'])

        # Search result cards
        cards = soup.find_all('div', class_=re.compile(r'\bshadow-sm\b.*\brounded-3\b'))
        if not cards:
            logger.debug('SubHD search page contained no result cards; no results or markup changed')
        for card in cards:
            # Find subtitle title & link
            view_text = card.find('div', class_='view-text')
            link_a = view_text.find('a') if view_text else None
            if not link_a:
                link_a = card.find('a', href=re.compile(r'^/a/([a-zA-Z0-9]+)$'))
            if not link_a:
                continue

            href = link_a.get('href', '')
            match = re.search(r'/a/([a-zA-Z0-9]+)', href)
            if not match:
                continue
            sid = match.group(1)
            page_link = urljoin(self.server_url, f'/a/{sid}')
            release_name = link_a.text.strip()

            # Year extraction
            year = default_year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', release_name)
            if year_match:
                year = int(year_match.group(1))
            else:
                title_div = card.find('div', class_=re.compile(r'\bfloat-start\b'))
                if title_div:
                    title_year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title_div.text)
                    if title_year_match:
                        year = int(title_year_match.group(1))

            # Language tags & format tags
            tag_texts = []
            tag_container = card.find('div', class_=re.compile(r'\btext-truncate\b'))
            if tag_container:
                tag_texts = [s.text.strip() for s in tag_container.find_all('span')]

            # Format check: ignore SUP-only subtitles (Bazarr only supports text subtitles)
            format_tags = {t.upper() for t in tag_texts if t.upper() in {'SUP', 'SRT', 'ASS', 'SSA', 'VTT', 'SUB'}}
            if 'SUP' in format_tags and not (format_tags - {'SUP'}):
                logger.debug("SubHD skipping SUP-only subtitle %r (sid %s)", release_name, sid)
                continue
            if re.search(r'\.sup(?:\.|$|\s)', release_name, re.IGNORECASE) and not any(ext in release_name.lower() for ext in ['.srt', '.ass', '.ssa']):
                logger.debug("SubHD skipping .sup in title %r (sid %s)", release_name, sid)
                continue

            is_bilingual = any('双语' in t for t in tag_texts)
            has_chs = any('简体' in t for t in tag_texts)
            has_cht = any('繁体' in t for t in tag_texts)
            has_eng = any(('英语' in t or '英文' in t) for t in tag_texts)

            detected_langs = []
            if has_chs or (is_bilingual and not has_cht):
                detected_langs.append(Language('zho', 'CN'))
                detected_langs.append(Language('zho'))
            if has_cht:
                detected_langs.append(Language('zho', 'TW'))
            if is_bilingual or has_eng:
                detected_langs.append(Language('eng'))
            if not detected_langs:
                detected_langs.append(Language('zho', 'CN'))
                detected_langs.append(Language('zho'))

            # Deduplicate detected languages while preserving order
            seen_langs = set()
            unique_detected = []
            for dl in detected_langs:
                lang_key = (dl.alpha3, dl.country, dl.script)
                if lang_key not in seen_langs:
                    seen_langs.add(lang_key)
                    unique_detected.append(dl)

            # Match with requested languages
            for dl in unique_detected:
                matched_req_lang = None
                for rl in languages:
                    if rl == dl:
                        matched_req_lang = rl
                        break
                    if rl.alpha3 == dl.alpha3:
                        if not rl.country or rl.country == dl.country:
                            matched_req_lang = rl
                            break
                if matched_req_lang:
                    sub = self.subtitle_class(
                        language=matched_req_lang,
                        page_link=page_link,
                        sid=sid,
                        version=release_name,
                        session=self.session,
                        year=year,
                    )
                    subtitles.append(sub)

        return subtitles

    def query(self, search_term, languages, year=None):
        search_link = urljoin(self.server_url, f'/search/{quote(search_term)}')
        logger.debug('SubHD searching URL: %s', search_link)
        try:
            r = self.session.get(search_link, timeout=15)
            _raise_if_rate_limited(r, TooManyRequests, 'SubHD search rate limited (HTTP 429)')
            r.raise_for_status()
        except TooManyRequests:
            raise
        except Exception as err:
            logger.warning('SubHD search request failed for %r: %s', search_term, err)
            return []

        if not r.content:
            return []

        html = r.content.decode('utf-8', 'ignore')
        return self._parse_search_page(html, languages, default_year=year)

    def list_subtitles(self, video, languages):
        candidates = []
        seen_keys = set()

        titles = []
        if isinstance(video, Episode):
            if video.series:
                titles.append(video.series)
            if getattr(video, 'alternative_series', None):
                for alt in video.alternative_series:
                    if alt and alt not in titles:
                        titles.append(alt)
        elif isinstance(video, Movie):
            if video.title:
                titles.append(video.title)
            if getattr(video, 'alternative_titles', None):
                for alt in video.alternative_titles:
                    if alt and alt not in titles:
                        titles.append(alt)

        for title in titles:
            # Each entry is (query term, episode_specific)
            search_queries = []
            if isinstance(video, Episode):
                if video.season is not None and video.episode is not None:
                    search_queries.append((f"{title} S{video.season:02d}E{video.episode:02d}", True))
                    search_queries.append((f"{title} S{video.season:02d}", False))
                elif video.season is not None:
                    search_queries.append((f"{title} S{video.season:02d}", False))
                else:
                    search_queries.append((title, False))
            elif isinstance(video, Movie):
                if video.year:
                    search_queries.append((f"{title} {video.year}", False))
                search_queries.append((title, False))

            for query_term, episode_specific in search_queries:
                subs = self.query(query_term, languages, year=video.year)
                for sub in subs:
                    key = (sub.sid, sub.language.alpha3, sub.language.country)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        sub.video = video
                        candidates.append(sub)

                # If specific episode query returned results, no need to fallback to broader season search
                if episode_specific and subs:
                    break

        return candidates

    def download_subtitle(self, subtitle: SubhdSubtitle):
        sid = subtitle.sid
        if not sid and subtitle.page_link:
            match = re.search(r'/a/([a-zA-Z0-9]+)', subtitle.page_link)
            if match:
                sid = match.group(1)

        if not sid:
            logger.error("SubHD subtitle has no valid ID: %r", subtitle.page_link)
            return

        detail_url = urljoin(self.server_url, f"/a/{sid}")
        try:
            # Step 1: visit detail page to initialize session / referer
            logger.debug("SubHD step 1: fetching detail page %s", detail_url)
            detail_res = self.session.get(detail_url, headers={'Referer': self.server_url}, timeout=15)
            _raise_if_rate_limited(detail_res, DownloadLimitExceeded, 'SubHD rate limited (detail page)')

            # Step 2: request prepare-download
            prep_url = urljoin(self.server_url, "/api/sub/prepare-download")
            logger.debug("SubHD step 2: requesting prepare-download for sid %s", sid)
            prep_res = self.session.post(
                prep_url,
                json={'sid': sid},
                headers={
                    'Referer': detail_url,
                    'Origin': self.server_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/json; charset=utf-8',
                },
                timeout=15,
            )
            _raise_if_rate_limited(prep_res, DownloadLimitExceeded, 'SubHD rate limited (prepare-download)')
            prep_res.raise_for_status()
            prep_data = prep_res.json()
            if not prep_data.get('success') or not prep_data.get('url'):
                logger.error("SubHD prepare-download failed for sid %s: %s", sid, prep_data)
                return

            down_path = prep_data.get('url')

            # Step 3: GET the down page to acquire the down authorization cookie
            down_page_url = urljoin(self.server_url, down_path)
            logger.debug("SubHD step 3: fetching down page %s", down_page_url)
            down_page_res = self.session.get(down_page_url, headers={'Referer': detail_url}, timeout=15)
            _raise_if_rate_limited(down_page_res, DownloadLimitExceeded, 'SubHD rate limited (down page)')

            # Step 4: POST /api/sub/down to acquire direct download URL
            api_down_url = urljoin(self.server_url, "/api/sub/down")
            logger.debug("SubHD step 4: requesting /api/sub/down for sid %s", sid)
            down_api_res = self.session.post(
                api_down_url,
                json={'sid': sid},
                headers={
                    'Referer': down_page_url,
                    'Origin': self.server_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/json',
                },
                timeout=15,
            )
            _raise_if_rate_limited(down_api_res, DownloadLimitExceeded, 'SubHD rate limited (/api/sub/down)')
            down_api_res.raise_for_status()
            down_data = down_api_res.json()
            if not down_data.get('success') or not down_data.get('url'):
                logger.error("SubHD /api/sub/down failed for sid %s: %s", sid, down_data)
                return

            file_url = down_data.get('url')

            # Step 5: GET direct file download
            logger.debug("SubHD step 5: downloading file from %s", file_url)
            file_res = self.session.get(
                file_url,
                headers={
                    'Referer': self.server_url,
                    'Origin': self.server_url,
                },
                timeout=30,
            )
            _raise_if_rate_limited(file_res, DownloadLimitExceeded, 'SubHD rate limited (file download)')
            file_res.raise_for_status()
            raw_content = file_res.content

            archive = get_archive_from_bytes(raw_content)
            if archive:
                logger.debug("SubHD downloaded content is an archive; extracting best match")
                extracted = _extract_subtitle_from_archive(archive, subtitle.language, subtitle.video)
                if extracted:
                    subtitle.content = fix_line_ending(extracted)
                else:
                    logger.warning("Could not extract suitable subtitle for %s from archive", subtitle.language)
            else:
                if raw_content.startswith(b'PG') or (file_url and file_url.lower().endswith('.sup')):
                    logger.debug("SubHD downloaded file is unsupported .sup format")
                    return
                subtitle.content = fix_line_ending(raw_content)

        except ProviderError:
            raise
        except Exception as e:
            logger.exception("Failed to download subtitle from SubHD for sid %s: %s", sid, e)
