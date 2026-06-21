# -*- coding: utf-8 -*-
import io
import logging
import re

from guessit import guessit
from subzero.language import Language
from rarfile import RarFile, is_rarfile
from zipfile import ZipFile, is_zipfile

from subliminal.exceptions import ProviderError
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal_patch.subtitle import guess_matches
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending
from subliminal.utils import sanitize
from subliminal.video import Episode

try:
    from subliminal_patch.http import RetryingCFSession
except ImportError:
    from requests import Session as RetryingCFSession

# The page initialises `epizode.key = ""` in the object literal and then
# overrides it in a separate script block: `epizode.key = '<32-char hex>';`
# We match only the dot-notation assignment so we don't accidentally match
# the empty-string initialiser in the object literal.
_KEY_RE = re.compile(r"epizode\.key\s*=\s*['\"]([0-9a-f]{32})['\"]")

logger = logging.getLogger(__name__)


class PrijevodiOnlineSubtitle(Subtitle):
    """Prijevodi-Online Subtitle."""
    provider_name = 'prijevodionline'
    hash_verifiable = False
    hearing_impaired_verifiable = False

    def __init__(self, language, page_link, subtitle_id, series, season, episode, releases, verified):
        super(PrijevodiOnlineSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.series = series
        self.season = season
        self.episode = episode
        self.releases = releases
        self.release_info = u", ".join(releases)
        self.verified = verified

    @property
    def id(self):
        return str(self.subtitle_id)

    @property
    def info(self):
        return self.release_info or ''

    def get_matches(self, video):
        matches = set()
        if isinstance(video, Episode):
            if video.series and sanitize(self.series) in (
                    sanitize(name) for name in [video.series] + video.alternative_series):
                matches.add('series')
            if video.season and self.season == video.season:
                matches.add('season')
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'episode'}))
        return matches


class PrijevodiOnlineProvider(Provider):
    """Prijevodi-Online Provider."""
    languages = {Language('hrv'), Language('mne'), Language('srp'), Language('hbs')}
    video_types = (Episode,)
    server_url = 'https://www.prijevodi-online.org'
    subtitle_class = PrijevodiOnlineSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = RetryingCFSession()

    def terminate(self):
        self.session.close()

    def _find_series(self, title):
        """Search the alphabetical index page for a series. Returns (series_id, slug) or (None, None)."""
        letter = title[0].lower()
        if not letter.isalpha():
            letter = '0'

        url = '{}/serije/index/{}'.format(self.server_url, letter)
        r = self.session.get(url, timeout=10)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        sanitized_title = sanitize(title)

        for row in soup.select('tr[id^="serija-"]'):
            link = row.select_one('td.naziv > a')
            if link and sanitize(link.get_text()) == sanitized_title:
                # href format: /serije/view/{id}/{slug}
                parts = link['href'].split('/')
                if len(parts) >= 5:
                    return int(parts[3]), parts[4]

        return None, None

    def _find_episode_id(self, series_id, slug, season, episode):
        """Find the episode ID for the given season/episode on the series page.

        Returns (episode_id, key, series_url) or (None, None, None).
        The key is the 32-char hex token the site requires for the subtitle POST request.
        """
        series_url = '{}/serije/view/{}/{}'.format(self.server_url, series_id, slug)
        r = self.session.get(series_url, timeout=10)
        r.raise_for_status()

        # Extract the AJAX key. The JS object initialises it as "" and the server
        # may inject a non-empty value elsewhere on the page; fall back to "" if absent.
        m = _KEY_RE.search(r.text)
        key = m.group(1) if m else ''

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        episodes_div = soup.find('div', id='epizode')
        if not episodes_div:
            return None, None, None

        season_h3 = episodes_div.find('h3', id='sezona-{}'.format(season))
        if not season_h3:
            return None, None, None

        for sibling in season_h3.next_siblings:
            if not hasattr(sibling, 'name'):
                continue
            if sibling.name == 'h3':
                break
            if sibling.name == 'div' and sibling.get('id', '').startswith('epizoda-'):
                broj = sibling.select_one('li.broj')
                if not broj:
                    continue
                try:
                    ep_num = int(broj.get_text().strip().rstrip('.'))
                except ValueError:
                    continue
                if ep_num == episode:
                    return int(sibling['id'].split('-')[1]), key, series_url

        return None, None, None

    def _fetch_subtitles(self, episode_id, series, season, episode, languages, key, series_url):
        """POST to the episode subtitle list once and return subtitles for all requested languages."""
        url = '{}/prijevod/get/{}'.format(self.server_url, episode_id)
        r = self.session.post(
            url,
            data={'key': key or ''},
            timeout=10,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': series_url,
                'Origin': self.server_url,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
        )
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        subtitles = []

        for row in soup.select('tr[id^="prijevod-"]'):
            row_id = row.get('id', '')
            if 'opis' in row_id:
                continue

            try:
                sub_id = int(row_id.split('-')[1])
            except (IndexError, ValueError):
                continue

            link = row.select_one('td.naziv a[href]')
            if not link:
                continue
            href = link['href']

            # Detect language from URL suffix (-hr = Croatian, -sr = Serbian, -cg = Montenegrin)
            href_lower = href.lower()
            if href_lower.endswith('-hr'):
                sub_lang = Language('hrv')
            elif href_lower.endswith('-sr'):
                sub_lang = Language('srp')
            elif href_lower.endswith('-cg'):
                sub_lang = Language('mne')
            else:
                continue

            if sub_lang not in languages and Language('hbs') not in languages:
                continue

            if Language('hbs') in languages:
                sub_lang = Language('hbs')

            status_td = row.select_one('td.status')
            verified = bool(status_td and 'provjereno' in status_td.get_text())

            releases = []
            opis_row = soup.find('tr', id='prijevod-opis-{}'.format(sub_id))
            if opis_row:
                opis_td = opis_row.select_one('td.opis') or opis_row.find('td')
                if opis_td:
                    release_info = opis_td.get_text(strip=True)
                    releases = [r.strip() for r in release_info.split("/")] if release_info else []

            subtitle = self.subtitle_class(
                sub_lang, self.server_url + href,
                sub_id, series, season, episode,
                releases, verified,
            )
            subtitles.append(subtitle)

        # Verified subtitles first
        subtitles.sort(key=lambda s: s.verified, reverse=True)
        return subtitles

    def query(self, languages, series, season, episode):
        series_id, slug = self._find_series(series)
        if not series_id:
            logger.debug('Series %r not found on prijevodi-online', series)
            return []

        episode_id, key, series_url = self._find_episode_id(series_id, slug, season, episode)
        if not episode_id:
            logger.debug('S%02dE%02d not found for series %r', season, episode, series)
            return []

        subtitles = self._fetch_subtitles(episode_id, series, season, episode, languages, key, series_url)
        logger.debug('Found %d subtitle(s) for %r S%02dE%02d', len(subtitles), series, season, episode)
        return subtitles

    def list_subtitles(self, video, languages):
        if not isinstance(video, Episode):
            return []

        for title in [video.series] + video.alternative_series:
            subtitles = self.query(languages, title, video.season, video.episode)
            if subtitles:
                return subtitles

        return []

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.page_link, timeout=30)
        r.raise_for_status()

        archive_stream = io.BytesIO(r.content)
        if is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive_stream.seek(0)
            with RarFile(archive_stream) as rf:
                names = [n for n in rf.namelist() if n.lower().endswith(SUBTITLE_EXTENSIONS)]
                if not names:
                    raise ProviderError('No subtitle file found in rar archive')
                subtitle.content = fix_line_ending(rf.read(names[0]))
        elif is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive_stream.seek(0)
            with ZipFile(archive_stream) as zf:
                names = [n for n in zf.namelist() if n.lower().endswith(SUBTITLE_EXTENSIONS)]
                if not names:
                    raise ProviderError('No subtitle file found in zip archive')
                subtitle.content = fix_line_ending(zf.read(names[0]))
        else:
            raise ProviderError('Unrecognized archive format for subtitle {}'.format(subtitle.id))

