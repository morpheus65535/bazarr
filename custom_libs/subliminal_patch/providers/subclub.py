# -*- coding: utf-8 -*-
import io
import logging
import re
from random import randint
from zipfile import ZipFile, is_zipfile

from rarfile import RarFile, is_rarfile

from guessit import guessit
from requests import Session
from subliminal.exceptions import ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending, sanitize
from subliminal.video import Episode, Movie
from subzero.language import Language

from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)

# Anchor text shapes: "Inception (2010)" or "Game of Thrones (2011) [01x01]".
TITLE_RE = re.compile(
    r'^(?P<title>.+?)\s*\((?P<year>\d{4})\)'
    r'(?:\s*\[(?P<season>\d+)x(?P<episode>\d+)\])?\s*$'
)
IMDB_ID_RE = re.compile(r'(tt\d+)')
DOWN_ID_RE = re.compile(r'down\.php\?id=(\d+)')


class SubclubSubtitle(Subtitle):
    provider_name = 'subclub'

    def __init__(self, language, page_link, download_link, archive_id, filename,
                 title, year, season, episode, imdb_id, fps, rating, uploader):
        super().__init__(language, page_link=page_link)
        self.download_link = download_link
        self.archive_id = archive_id
        self.filename = filename
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.imdb_id = imdb_id
        self.fps = fps
        self.rating = rating
        self.uploader = uploader
        self.release_info = filename
        self.matches = set()

    @property
    def id(self):
        return '{}/{}'.format(self.archive_id, self.filename)

    def get_fps(self):
        return self.fps

    def get_matches(self, video):
        matches = set()
        type_ = 'episode' if isinstance(video, Episode) else 'movie'

        if isinstance(video, Movie):
            if video.title and sanitize(self.title) == sanitize(video.title):
                matches.add('title')
        else:
            if video.series and sanitize(self.title) == sanitize(video.series):
                matches.add('series')
            if video.season is not None and self.season == video.season:
                matches.add('season')
            if video.episode is not None and self.episode == video.episode:
                matches.add('episode')

        if video.year and self.year == video.year:
            matches.add('year')

        if self.imdb_id:
            if isinstance(video, Movie) and video.imdb_id == self.imdb_id:
                matches.add('imdb_id')
            elif isinstance(video, Episode) and video.series_imdb_id == self.imdb_id:
                matches.add('series_imdb_id')

        matches |= guess_matches(video, guessit(self.filename, {'type': type_}))

        self.matches = matches
        return matches


class SubclubProvider(Provider):
    subtitle_class = SubclubSubtitle
    languages = {Language('est')}
    video_types = (Episode, Movie)
    server_url = 'https://www.subclub.eu'
    search_url = server_url + '/jutud.php'
    archive_content_url = server_url + '/subtitles_archivecontent.php'
    download_url = server_url + '/down.php'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers['Referer'] = self.server_url + '/'

    def terminate(self):
        self.session.close()

    @staticmethod
    def _parse_float(text):
        if not text:
            return None
        try:
            return float(text.strip().replace(',', '.').split()[0])
        except (ValueError, IndexError):
            return None

    def _search(self, title):
        r = self.session.get(self.search_url, params={'otsing': title}, timeout=30)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'),
                                   ['lxml', 'html.parser'])
        table = soup.find('table', id='tale_list')
        if table is None:
            return []

        results = []
        for row in table.select('tbody > tr'):
            tds = row.find_all('td', recursive=False)
            if len(tds) < 9:
                continue

            link_el = tds[1].find('a', class_='sc_link', href=DOWN_ID_RE)
            if link_el is None:
                continue

            archive_id = DOWN_ID_RE.search(link_el['href']).group(1)
            anchor_text = ' '.join(link_el.get_text(' ', strip=True).split())
            m = TITLE_RE.match(anchor_text)
            if not m:
                logger.debug('subclub: skipping unparsable title %r', anchor_text)
                continue

            imdb_id = None
            imdb_a = tds[3].find('a', href=True)
            if imdb_a:
                im = IMDB_ID_RE.search(imdb_a['href'])
                if im:
                    imdb_id = im.group(1)

            rating_span = tds[7].find('span')
            rating_text = rating_span.get_text() if rating_span else tds[7].get_text()

            results.append({
                'archive_id': archive_id,
                'page_link': '{}?id={}'.format(self.download_url, archive_id),
                'title': m.group('title').strip(),
                'year': int(m.group('year')),
                'season': int(m.group('season')) if m.group('season') else None,
                'episode': int(m.group('episode')) if m.group('episode') else None,
                'imdb_id': imdb_id,
                'fps': self._parse_float(tds[6].get_text()),
                'rating': self._parse_float(rating_text),
                'uploader': tds[8].get_text(strip=True) or None,
            })

        results.sort(key=lambda h: -(h['rating'] or 0.0))
        return results

    def _archive_files(self, archive_id):
        """Return [(filename, direct download url)] from the site's listing,
        or [] when the listing is empty (caller falls back to extraction)."""
        r = self.session.get(self.archive_content_url,
                             params={'id': archive_id}, timeout=30)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'),
                                   ['lxml', 'html.parser'])
        files = []
        for a in soup.select('a[href*="down.php"]'):
            href = a.get('href') or ''
            if 'filename=' not in href:
                continue
            filename = a.get_text(strip=True)
            if not filename.lower().endswith(tuple(SUBTITLE_EXTENSIONS)):
                continue
            # Site emits "../down.php?id=N&filename=B64".
            files.append((filename, self.server_url + '/' + href.lstrip('./')))
        return files

    def _extract_archive(self, archive_id):
        """Download and unpack the whole archive; return [(filename, bytes)]
        for each subtitle member. Used when the listing endpoint is empty."""
        r = self.session.get(self.download_url,
                             params={'id': archive_id}, timeout=60)
        r.raise_for_status()

        stream = io.BytesIO(r.content)
        if is_zipfile(stream):
            archive = ZipFile(stream)
        elif is_rarfile(stream):
            archive = RarFile(stream)
        else:
            raise ProviderError(
                'subclub: unsupported archive format for id=%s' % archive_id
            )

        out = []
        for name in archive.namelist():
            base = name.rsplit('/', 1)[-1]
            if not base or base.startswith('.'):
                continue
            if not base.lower().endswith(tuple(SUBTITLE_EXTENSIONS)):
                continue
            try:
                data = archive.read(name)
            except Exception as e:
                logger.warning('subclub: failed to read %r from archive %s: %s',
                               name, archive_id, e)
                continue
            out.append((base, data))
        return out

    def _hit_matches_video(self, hit, video):
        if isinstance(video, Episode):
            if hit['season'] is None or hit['episode'] is None:
                return False
            if video.season is not None and hit['season'] != video.season:
                return False
            if video.episode is not None and hit['episode'] != video.episode:
                return False
            if video.series and sanitize(hit['title']) != sanitize(video.series):
                return False
        else:
            if hit['season'] is not None or hit['episode'] is not None:
                return False
            if video.title and sanitize(hit['title']) != sanitize(video.title):
                return False
            if video.year and hit['year'] != video.year:
                return False
        return True

    def query(self, video):
        if isinstance(video, Episode):
            search_titles = [video.series] + list(getattr(video, 'alternative_series', []) or [])
        else:
            search_titles = [video.title] + list(getattr(video, 'alternative_titles', []) or [])

        seen_archive_ids = set()
        subtitles = []

        for search_title in search_titles:
            if not search_title:
                continue
            try:
                hits = self._search(search_title)
            except Exception as e:
                logger.warning('subclub: search for %r failed: %s', search_title, e)
                continue

            for hit in hits:
                if hit['archive_id'] in seen_archive_ids:
                    continue
                if not self._hit_matches_video(hit, video):
                    continue
                seen_archive_ids.add(hit['archive_id'])

                try:
                    files = self._archive_files(hit['archive_id'])
                except Exception as e:
                    logger.warning('subclub: archive list for id=%s failed: %s',
                                   hit['archive_id'], e)
                    continue

                extracted = []
                if not files:
                    try:
                        extracted = self._extract_archive(hit['archive_id'])
                    except Exception as e:
                        logger.warning('subclub: archive unpack for id=%s failed: %s',
                                       hit['archive_id'], e)
                        continue
                    if not extracted:
                        continue

                pairs = files or [(name, None) for name, _ in extracted]
                contents = dict(extracted)

                for filename, download_link in pairs:
                    subtitle = self.subtitle_class(
                        language=Language('est'),
                        page_link=hit['page_link'],
                        download_link=download_link,
                        archive_id=hit['archive_id'],
                        filename=filename,
                        title=hit['title'],
                        year=hit['year'],
                        season=hit['season'],
                        episode=hit['episode'],
                        imdb_id=hit['imdb_id'],
                        fps=hit['fps'],
                        rating=hit['rating'],
                        uploader=hit['uploader'],
                    )
                    if filename in contents:
                        subtitle.content = fix_line_ending(contents[filename])
                    subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        if not any(lang.alpha3 == 'est' for lang in languages):
            return []
        return self.query(video)

    def download_subtitle(self, subtitle):
        # Fallback path pre-populates content during query().
        if subtitle.content:
            return

        r = self.session.get(subtitle.download_link, timeout=30)
        r.raise_for_status()
        if not r.content:
            raise ProviderError('subclub: empty response for id=%s file=%s' % (
                subtitle.archive_id, subtitle.filename))
        subtitle.content = fix_line_ending(r.content)
