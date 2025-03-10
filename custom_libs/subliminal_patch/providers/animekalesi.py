# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import re
import io
import os
import zipfile
from random import randint
from typing import Optional, Dict, List, Set
from datetime import datetime, timedelta

from babelfish import Language
from guessit import guessit
from bs4 import BeautifulSoup
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.http import RetryingCFSession
from subliminal.subtitle import fix_line_ending
from subliminal.video import Episode
from subliminal_patch.utils import sanitize, fix_inconsistent_naming
from subzero.language import Language
from subliminal.cache import region

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)

# Cache expiration times
SEARCH_EXPIRATION_TIME = timedelta(hours=1).total_seconds()

def fix_turkish_chars(text: str) -> str:
    """Fix Turkish characters for proper matching."""
    if not text:
        return ""
    tr_chars = {
        'İ': 'i', 'I': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c',
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'
    }
    for tr_char, eng_char in tr_chars.items():
        text = text.replace(tr_char, eng_char)
    return text

def normalize_series_name(series: str) -> str:
    """Normalize series name for consistent matching."""
    if not series:
        return ""
    # Remove special characters
    series = re.sub(r'[^\w\s-]', '', series)
    # Replace multiple spaces with single space
    series = re.sub(r'\s+', ' ', series)
    # Fix Turkish characters
    series = fix_turkish_chars(series)
    return series.lower().strip()

class AnimeKalesiSubtitle(Subtitle):
    """AnimeKalesi Subtitle."""
    provider_name = 'animekalesi'
    hearing_impaired_verifiable = False

    def __init__(self, language: Language, page_link: str, series: str, season: int, episode: int, 
                 version: str, download_link: str, uploader: str = None, release_group: str = None):
        super().__init__(language)
        self.page_link = page_link
        self.series = series
        self.season = season
        self.episode = episode
        self.version = version
        self.download_link = download_link
        self.release_info = version
        self.matches = set()
        self.uploader = uploader
        self.release_group = release_group
        self.hearing_impaired = False

    @property
    def id(self) -> str:
        return self.download_link

    def get_matches(self, video: Episode) -> Set[str]:
        matches = set()

        # Series name match
        if video.series and self.series:
            # Direct comparison
            if video.series.lower() == self.series.lower():
                matches.add('series')
            # Normalized comparison
            elif normalize_series_name(video.series) == normalize_series_name(self.series):
                matches.add('series')
            # Alternative series comparison
            elif getattr(video, 'alternative_series', None):
                for alt_name in video.alternative_series:
                    if normalize_series_name(alt_name) == normalize_series_name(self.series):
                        matches.add('series')
                        break

        # Season match
        if video.season and self.season == video.season:
            matches.add('season')

        # Episode match
        if video.episode and self.episode == video.episode:
            matches.add('episode')

        # Release group match
        if getattr(video, 'release_group', None) and self.release_group:
            if video.release_group.lower() in self.release_group.lower():
                matches.add('release_group')

        matches |= guess_matches(video, guessit(self.version))

        self.matches = matches
        return matches

class AnimeKalesiProvider(Provider, ProviderSubtitleArchiveMixin):
    """AnimeKalesi Provider."""
    languages = {Language('tur')}
    video_types = (Episode,)
    server_url = 'https://www.animekalesi.com'
    subtitle_class = AnimeKalesiSubtitle
    hearing_impaired_verifiable = False

    def __init__(self):
        self.session = None
        super().__init__()

    def initialize(self):
        self.session = RetryingCFSession()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        self.session.headers['Accept-Language'] = 'tr,en-US;q=0.7,en;q=0.3'
        self.session.headers['Connection'] = 'keep-alive'
        self.session.headers['Referer'] = self.server_url
        logger.info('AnimeKalesi provider initialized')

    def terminate(self):
        self.session.close()

    @region.cache_on_arguments(expiration_time=SEARCH_EXPIRATION_TIME)
    def _search_anime_list(self, series: str) -> Optional[Dict[str, str]]:
        """Search for series in anime list."""
        if not series:
            return None

        try:
            response = self.session.get(f'{self.server_url}/tum-anime-serileri.html', timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            normalized_search = normalize_series_name(series)
            possible_matches = []

            for td in soup.select('td#bolumler'):
                link = td.find('a')
                if not link:
                    continue

                title = link.text.strip()
                href = link.get('href', '')

                if not href or 'bolumler-' not in href:
                    continue

                normalized_title = normalize_series_name(title)

                # Exact match
                if normalized_title == normalized_search:
                    return {'title': title, 'url': href}

                # Partial match
                if normalized_search in normalized_title or normalized_title in normalized_search:
                    possible_matches.append({'title': title, 'url': href})

            # Return best partial match if no exact match found
            if possible_matches:
                return possible_matches[0]

        except Exception as e:
            logger.error('Error searching anime list: %s', e)

        return None

    def _parse_season_episode(self, title: str) -> tuple:
        """Extract season and episode numbers from title."""
        if not title:
            return None, None

        try:
            ep_match = re.search(r'(\d+)\.\s*Bölüm', title)
            episode = int(ep_match.group(1)) if ep_match else None

            season_match = re.search(r'(\d+)\.\s*Sezon', title)
            season = int(season_match.group(1)) if season_match else 1

            return season, episode
        except (AttributeError, ValueError) as e:
            logger.error('Error parsing season/episode from title "%s": %s', title, e)
            return None, None

    @region.cache_on_arguments(expiration_time=SEARCH_EXPIRATION_TIME)
    def _get_episode_list(self, series_url: str) -> Optional[List[Dict[str, str]]]:
        """Get episode list for a series."""
        if not series_url:
            return None

        try:
            subtitle_page_url = f'{self.server_url}/{series_url.replace("bolumler-", "altyazib-")}'
            response = self.session.get(subtitle_page_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            episodes = []
            for td in soup.select('td#ayazi_indir'):
                link = td.find('a', href=True)
                if not link:
                    continue

                if 'indir_bolum-' in link['href'] and 'Bölüm Türkçe Altyazısı' in link.get('title', ''):
                    episodes.append({
                        'title': link['title'],
                        'url': f"{self.server_url}/{link['href']}"
                    })

            return episodes

        except Exception as e:
            logger.error('Error getting episode list: %s', e)
            return None

    def query(self, series: str, season: int, episode: int) -> List[AnimeKalesiSubtitle]:
        """Search subtitles from AnimeKalesi."""
        if not series or not season or not episode:
            return []

        subtitles = []

        # Find series information
        series_data = self._search_anime_list(series)
        if not series_data:
            logger.debug('Series not found: %s', series)
            return subtitles

        # Get episode list
        episodes = self._get_episode_list(series_data['url'])
        if not episodes:
            return subtitles

        try:
            for episode_data in episodes:
                title = episode_data['title']
                link_url = episode_data['url']

                # Extract season and episode numbers
                current_season, current_episode = self._parse_season_episode(title)
                if current_season is None or current_episode is None:
                    continue

                if current_season == season and current_episode == episode:
                    try:
                        # Navigate to subtitle download page
                        response = self.session.get(link_url, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Find download link
                        subtitle_div = soup.find('div', id='altyazi_indir')
                        if subtitle_div and subtitle_div.find('a', href=True):
                            download_link = f"{self.server_url}/{subtitle_div.find('a')['href']}"

                            # Find uploader information
                            uploader = None
                            translator_info = soup.find('strong', text='Altyazı/Çeviri:')
                            if translator_info and translator_info.parent:
                                strong_tags = translator_info.parent.find_all('strong')
                                for i, tag in enumerate(strong_tags):
                                    if tag.text == 'Altyazı/Çeviri:':
                                        if i + 1 < len(strong_tags):
                                            uploader = tag.next_sibling
                                            if uploader:
                                                uploader = uploader.strip()
                                        else:
                                            uploader = tag.next_sibling
                                            if uploader:
                                                uploader = uploader.strip()
                                        break

                            version = f"{series_data['title']} - S{current_season:02d}E{current_episode:02d}"
                            if uploader:
                                version += f" by {uploader}"

                            try:
                                subtitle = self.subtitle_class(
                                    Language('tur'),
                                    link_url,
                                    series_data['title'],
                                    current_season,
                                    current_episode,
                                    version,
                                    download_link,
                                    uploader=uploader,
                                    release_group=None
                                )
                                subtitles.append(subtitle)
                            except Exception as e:
                                logger.error('Error creating subtitle object: %s', e)
                                continue

                    except Exception as e:
                        logger.error('Error processing subtitle page %s: %s', link_url, e)
                        continue

        except Exception as e:
            logger.error('Error querying subtitles: %s', e)

        return subtitles

    def list_subtitles(self, video: Episode, languages: Set[Language]) -> List[AnimeKalesiSubtitle]:
        if not video.series or not video.episode:
            return []

        return self.query(video.series, video.season, video.episode)

    def download_subtitle(self, subtitle: AnimeKalesiSubtitle) -> None:
        try:
            response = self.session.get(subtitle.download_link, timeout=10)
            response.raise_for_status()

            # Check for ZIP file
            if response.content.startswith(b'PK\x03\x04'):
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    subtitle_files = [f for f in zf.namelist() if f.lower().endswith(('.srt', '.ass'))]

                    if not subtitle_files:
                        logger.error('No subtitle file found in ZIP archive')
                        return

                    # Select best matching subtitle file
                    subtitle_file = subtitle_files[0]
                    if len(subtitle_files) > 1:
                        for f in subtitle_files:
                            if subtitle.version.lower() in f.lower():
                                subtitle_file = f
                                break

                    subtitle.content = fix_line_ending(zf.read(subtitle_file))
            else:
                # Regular subtitle file
                subtitle.content = fix_line_ending(response.content)

        except Exception as e:
            logger.error('Error downloading subtitle: %s', e)

