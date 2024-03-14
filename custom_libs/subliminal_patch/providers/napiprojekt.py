# coding=utf-8
from __future__ import absolute_import
import logging

from subliminal.providers.napiprojekt import NapiProjektProvider as _NapiProjektProvider, \
    NapiProjektSubtitle as _NapiProjektSubtitle, get_subhash
from subzero.language import Language
from subliminal.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal_patch.utils import fix_inconsistent_naming as _fix_inconsistent_naming
from bs4 import BeautifulSoup
from guessit import guessit

logger = logging.getLogger(__name__)


def fix_inconsistent_naming(title):
    return _fix_inconsistent_naming(title, {}, True)


class NapiProjektSubtitle(_NapiProjektSubtitle):
    def __init__(self, language, hash, release_info, matches=None):
        super(NapiProjektSubtitle, self).__init__(language, hash)
        self.release_info = release_info
        self.matches = matches

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.release_info, self.language)

    def get_matches(self, video):
        matches = super().get_matches(video)
        if self.matches is not None:
            matches |= self.matches
        return matches


class NapiProjektProvider(_NapiProjektProvider):
    languages = {Language.fromalpha2(l) for l in ['pl']}
    video_types = (Episode, Movie)
    subtitle_class = NapiProjektSubtitle

    def query(self, language, hash):
        params = {
            'v': 'dreambox',
            'kolejka': 'false',
            'nick': '',
            'pass': '',
            'napios': 'Linux',
            'l': language.alpha2.upper(),
            'f': hash,
            't': get_subhash(hash)}
        logger.info('Searching subtitle %r', params)
        r = self.session.get(self.server_url, params=params, timeout=10)
        r.raise_for_status()

        # handle subtitles not found and errors
        if r.content[:4] == b'NPc0':
            logger.debug('No subtitles found')
            return None

        subtitle = self.subtitle_class(language, hash, release_info=hash)
        subtitle.content = r.content
        logger.debug('Found subtitle %r', subtitle)

        return subtitle

    def list_subtitles(self, video, languages):
        def flatten(l):
            return [item for sublist in l for item in sublist]
        return [s for s in [self.query(l, video.hashes['napiprojekt']) for l in languages] if s is not None] + \
            flatten([self._scrape(video, l) for l in languages])

    def download_subtitle(self, subtitle):
        if subtitle.content is not None:
            return
        subtitle.content = self.query(subtitle.language, subtitle.hash).content

    def _scrape(self, video, language):
        if language.alpha2 != 'pl':
            return []
        title, matches = self._find_title(video)
        if title == None:
            return []
        episode = f'-s{video.season:02d}e{video.episode:02d}' if isinstance(
            video, Episode) else ''
        response = self.session.get(
            f'https://www.napiprojekt.pl/napisy1,7,0-dla-{title}{episode}')
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        subtitles = []
        for link in soup.find_all('a'):
            if 'class' in link.attrs and 'tableA' in link.attrs['class']:
                hash = link.attrs['href'][len('napiprojekt:'):]
                subtitles.append(
                    NapiProjektSubtitle(language,
                                        hash,
                                        release_info=str(link.contents[0]),
                                        matches=matches | ({'season', 'episode'} if episode else set())))

        logger.debug(f'Found subtitles {subtitles}')
        return subtitles

    def _find_title(self, video):
        search_response = self.session.post('https://www.napiprojekt.pl/ajax/search_catalog.php', {
            'queryString': video.series if isinstance(video, Episode) else video.title,
            'queryKind': 1 if isinstance(video, Episode) else 2,
            'queryYear': str(video.year) if video.year is not None else '',
            'associate': '',
        })
        search_response.raise_for_status()
        soup = BeautifulSoup(search_response.content, 'html.parser')
        imdb_id = video.series_imdb_id if isinstance(
            video, Episode) else video.imdb_id

        def match_title_tag(
            tag): return tag.name == 'a' and 'class' in tag.attrs and 'movieTitleCat' in tag.attrs['class'] and 'href' in tag.attrs

        if imdb_id:
            for entry in soup.find_all(lambda tag: tag.name == 'div' and 'greyBoxCatcher' in tag['class']):
                if entry.find_all(href=lambda href: href and href.startswith(f'https://www.imdb.com/title/{imdb_id}')):
                    for link in entry.find_all(match_title_tag):
                        return link.attrs['href'][len('napisy-'):], \
                            {'series', 'year', 'series_imdb_id'} if isinstance(
                                video, Episode) else {'title', 'year', 'imdb_id'}

        type = 'episode' if isinstance(video, Episode) else 'movie'
        for link in soup.find_all(match_title_tag):
            title = fix_inconsistent_naming(str(link.contents[0].string))
            matches = guess_matches(video, guessit(title, {'type': type}))
            if video.year:
                matches |= {'year'}
            if isinstance(video, Episode):
                if title == fix_inconsistent_naming(video.series):
                    matches |= {'series'}
            else:
                if title == fix_inconsistent_naming(video.title):
                    matches |= {'title'}
            return link.attrs['href'][len('napisy-'):], matches

        return None, None
