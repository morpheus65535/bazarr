# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re

from bs4 import BeautifulSoup
from guessit import guessit
from requests import Session

from subliminal import Episode, Movie
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language

logger = logging.getLogger(__name__)

server_url = 'https://www.subtitlecat.com/'


def _language_from_code(code):
    code = code.strip().lower()
    if '-' in code:
        code = code.split('-', 1)[0]
    try:
        return Language.fromalpha2(code)
    except Exception:
        logger.debug('Could not parse language code: %s', code)
        return None


def _build_languages():
    codes = [
        'af', 'ak', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs',
        'bg', 'ca', 'ny', 'zh', 'hr', 'cs', 'da', 'nl', 'en', 'et', 'fi',
        'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu', 'ht', 'ha', 'he', 'hi',
        'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jv', 'kn', 'kk', 'km',
        'rw', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'ln', 'lt', 'lg', 'lb',
        'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no',
        'or', 'om', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sr', 'si',
        'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'te', 'th',
        'tr', 'uk', 'ur', 'uz', 'vi', 'cy', 'xh', 'yo', 'zu',
    ]
    result = set()
    for code in codes:
        try:
            result.add(Language.fromalpha2(code))
        except Exception:
            pass
    return result


class SubtitleCatSubtitle(Subtitle):
    provider_name = 'subtitlecat'

    def __init__(self, language, subtitle_id, page_link, download_link, release_name, matches):
        super(SubtitleCatSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.download_link = download_link
        self.release_info = release_name
        self.release_name = release_name
        self.matches = matches or set()

    @property
    def id(self):
        return self.subtitle_id

    def get_matches(self, video):
        video_type = 'episode' if isinstance(video, Episode) else 'movie'
        self.matches |= guess_matches(video, guessit(self.release_name, {'type': video_type}), partial=True)
        return self.matches


class SubtitleCatProvider(Provider):
    """Subtitle Cat Provider"""
    languages = _build_languages()
    video_types = (Episode, Movie)

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        if isinstance(video, Episode):
            query = video.series
            if video.season and video.episode:
                query += f' S{video.season:02d}E{video.episode:02d}'
        else:
            query = video.title
            if video.year:
                query += f' {video.year}'

        logger.info('Searching subtitles for %r', query)

        params = {'search': query}
        res = self.session.get(server_url + 'index.php', params=params, timeout=15)
        res.raise_for_status()

        soup = BeautifulSoup(res.content, 'html.parser')
        results = []
        for row in soup.select('table.sub-table tbody tr'):
            link = row.find('a', href=True)
            if not link:
                continue
            release_name = link.get_text(strip=True)
            href = link['href']
            if not href.startswith('subs/'):
                continue
            results.append((release_name, href))

        subtitles = []
        for release_name, href in results[:20]:
            detail_url = server_url + href
            try:
                detail_res = self.session.get(detail_url, timeout=15)
                detail_res.raise_for_status()
            except Exception as e:
                logger.debug('Error fetching detail page %r: %s', detail_url, e)
                continue

            detail_soup = BeautifulSoup(detail_res.content, 'html.parser')
            for sub_div in detail_soup.select('div.sub-single'):
                download_a = sub_div.find('a', id=re.compile(r'^download_'))
                if not download_a:
                    continue

                lang_code = download_a.get('id', '').replace('download_', '')
                language = _language_from_code(lang_code)
                if language is None or language not in languages:
                    continue

                download_link = download_a.get('href')
                if not download_link:
                    continue

                if not download_link.startswith('http'):
                    download_link = server_url + download_link.lstrip('/')

                subtitle_id = f'{href}-{lang_code}'
                subtitles.append(SubtitleCatSubtitle(
                    language=language,
                    subtitle_id=subtitle_id,
                    page_link=detail_url,
                    download_link=download_link,
                    release_name=release_name,
                    matches=set(),
                ))

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle.download_link)
        r = self.session.get(subtitle.download_link, timeout=15)
        if r.status_code == 404:
            logger.error('Error 404 downloading %r', subtitle)
            return
        r.raise_for_status()

        if r.content:
            subtitle.content = fix_line_ending(r.content)
        else:
            logger.error('Empty content from %r', subtitle.download_link)
