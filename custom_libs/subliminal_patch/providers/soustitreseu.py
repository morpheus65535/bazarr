# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import os
import logging
from urllib.parse import unquote

from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile

from guessit import guessit
from subliminal_patch.http import RetryingCFSession
import chardet
from bs4 import NavigableString, UnicodeDammit
from subzero.language import Language

from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.score import get_scores, framerate_equal
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import sanitize, SUBTITLE_EXTENSIONS
from subliminal.video import Episode, Movie
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


class SoustitreseuSubtitle(Subtitle):
    """Sous-Titres.eu Subtitle."""
    provider_name = 'soustitreseu'

    def __init__(self, language, video, name, data, content, is_perfect_match):
        super().__init__(language)
        self.srt_filename = name
        self.release_info = name
        self.page_link = None
        self.download_link = None
        self.data = data
        self.video = video
        self.matches = set()
        self.content = content
        self.hearing_impaired = None
        self.is_perfect_match = is_perfect_match
        self._guessed_encoding = None

    @property
    def id(self):
        return self.srt_filename

    def get_matches(self, video):
        matches = set()

        if self.is_perfect_match:
            if isinstance(video, Episode):
                matches.add('series')
            else:
                matches.add('title')

        # guess additional info from data
        matches |= guess_matches(video, self.data)

        self.matches = matches
        self.data = None  # removing this make the subtitles object unpickable
        return matches

    def guess_encoding(self):
        # override default subtitle guess_encoding method to not include language-specific encodings guessing
        # chardet encoding detection seem to yield better results
        """Guess encoding using chardet.

        :return: the guessed encoding.
        :rtype: str

        """
        if self._guessed_encoding:
            return self._guessed_encoding

        logger.info('Guessing encoding for language %s', self.language)

        # guess/detect encoding using chardet
        encoding = chardet.detect(self.content)['encoding']
        logger.info('Chardet found encoding %s', encoding)

        if not encoding:
            # fallback on bs4
            logger.info('Falling back to bs4 detection')
            a = UnicodeDammit(self.content)

            logger.info("bs4 detected encoding: %s", a.original_encoding)

            if a.original_encoding:
                self._guessed_encoding = a.original_encoding
                return a.original_encoding
            raise ValueError(u"Couldn't guess the proper encoding for %s", self)

        self._guessed_encoding = encoding
        return encoding


class SoustitreseuProvider(Provider, ProviderSubtitleArchiveMixin):
    """Sous-Titres.eu Provider."""
    subtitle_class = SoustitreseuSubtitle
    languages = {Language(l) for l in ['fra', 'eng']}
    video_types = (Episode, Movie)
    server_url = 'https://www.sous-titres.eu/'
    search_url = server_url + 'search.html'

    def __init__(self):
        self.session = None
        self.is_perfect_match = False

    def initialize(self):
        self.session = RetryingCFSession()
        self.session.headers['Referer'] = self.server_url

    def terminate(self):
        self.session.close()

    def query_series(self, video, title):
        subtitles = []

        r = self.session.get(self.search_url, params={'q': title}, timeout=30)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])

        # loop over series name
        self.is_perfect_match = False
        series_url = []
        series = soup.select('.serie > h3 > a')
        for item in series:
            # title
            if title in item.text:
                series_url.append(item.attrs['href'])
                self.is_perfect_match = True

        series_subs_archives_url = []
        for series_page in series_url:
            page_link = self.server_url + series_page
            r = self.session.get(page_link, timeout=30)
            r.raise_for_status()

            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])

            series_subs_archives = soup.select('a.subList')
            for item in series_subs_archives:
                matching_archive = False
                subtitles_archive_name = unquote(item.attrs['href'].split('/')[-1:][0][:-4])
                guessed_subs = guessit(subtitles_archive_name, {'type': 'episode'})
                try:
                    season, episode = item.select_one('.episodenum').text.split('×')
                    guessed_subs.update({'season': int(season), 'episode': int(episode)})
                except ValueError:
                    season = item.select_one('.episodenum').text[1:]
                    episode = None
                    guessed_subs.update({'season': int(season)})

                if guessed_subs['season'] == video.season:
                    if 'episode' in guessed_subs:
                        if guessed_subs['episode'] == video.episode:
                            matching_archive = True
                    else:
                        matching_archive = True

                if matching_archive:
                    download_link = self.server_url + 'series/' + item.attrs['href']
                    res = self.session.get(download_link, timeout=30)
                    res.raise_for_status()

                    archive = self._get_archive(res.content)
                    # extract the subtitle
                    if archive:
                        subtitles_from_archive = self._get_subtitle_from_archive(archive, video)
                        for subtitle in subtitles_from_archive:
                            subtitle.page_link = page_link
                            subtitle.download_link = download_link
                            subtitles.append(subtitle)

        return subtitles

    def query_movies(self, video, title):
        subtitles = []

        r = self.session.get(self.search_url, params={'q': title}, timeout=30)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])

        # loop over movies name
        movies_url = []
        self.is_perfect_match = False
        movies = soup.select('.film > h3 > a')
        for item in movies:
            # title
            if title.lower() in item.text.lower():
                movies_url.append(item.attrs['href'])
                self.is_perfect_match = True

        series_subs_archives_url = []
        for movies_page in movies_url:
            page_link = self.server_url + movies_page
            r = self.session.get(page_link, timeout=30)
            r.raise_for_status()

            soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])

            movies_subs_archives = soup.select('a.subList')
            for item in movies_subs_archives:
                download_link = self.server_url + 'films/' + item.attrs['href']
                res = self.session.get(download_link, timeout=30)
                res.raise_for_status()

                archive = self._get_archive(res.content)
                # extract the subtitle
                if archive:
                    subtitles_from_archive = self._get_subtitle_from_archive(archive, video)
                    for subtitle in subtitles_from_archive:
                        subtitle.page_link = page_link
                        subtitle.download_link = download_link
                        subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        subtitles = []

        # query for subtitles
        if isinstance(video, Episode):
            subtitles += [s for s in self.query_series(video, video.series) if s.language in languages]
        else:
            subtitles += [s for s in self.query_movies(video, video.title) if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        return subtitle

    def _get_archive(self, content):
        # open the archive
        archive_stream = io.BytesIO(content)
        if is_rarfile(archive_stream):
            logger.debug('Sous-Titres.eu: Identified rar archive')
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            logger.debug('Sous-Titres.eu: Identified zip archive')
            archive = ZipFile(archive_stream)
        else:
            logger.error('Sous-Titres.eu: Unsupported compressed format')
            return None
        return archive

    def _get_subtitle_from_archive(self, archive, video):
        subtitles = []

        # some files have a non subtitle with .txt extension
        _tmp = list(SUBTITLE_EXTENSIONS)
        _tmp.remove('.txt')
        _subtitle_extensions = tuple(_tmp)
        _scores = get_scores(video)

        for name in archive.namelist():
            # discard hidden files
            if os.path.split(name)[-1].startswith('.'):
                continue

            # discard non-subtitle files
            if not name.lower().endswith(_subtitle_extensions):
                continue

            # get subtitles language
            if '.en.' in name.lower():
                language = Language.fromopensubtitles('eng')
            else:
                language = Language.fromopensubtitles('fre')

            release = name[:-4].lower().rstrip('tag').rstrip('en').rstrip('fr')
            _guess = guessit(release)
            if isinstance(video, Episode):
                try:
                    if video.episode != _guess['episode'] or video.season != _guess['season']:
                        continue
                except KeyError:
                    # episode or season are missing from guessit result
                    continue

            matches = set()
            matches |= guess_matches(video, _guess)
            _score = sum((_scores.get(match, 0) for match in matches))
            content = archive.read(name)
            subtitles.append(SoustitreseuSubtitle(language, video, name, _guess, content, self.is_perfect_match))

        return subtitles
