# coding=utf-8
from __future__ import absolute_import
import logging
import re

from subliminal.providers.napiprojekt import NapiProjektProvider as _NapiProjektProvider, \
    NapiProjektSubtitle as _NapiProjektSubtitle, get_subhash
from subzero.language import Language
from subliminal.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal_patch.utils import fix_inconsistent_naming as _fix_inconsistent_naming
from subliminal_patch.providers.mixins import ProviderRetryMixin
from bs4 import BeautifulSoup
from guessit import guessit

logger = logging.getLogger(__name__)

QUERY_RETRIES = 3
QUERY_TIMEOUT = 15


def fix_inconsistent_naming(title):
    return _fix_inconsistent_naming(title, {}, True)


class NapiProjektSubtitle(_NapiProjektSubtitle):
    def __init__(self, language, hash, release_info, matches=None):
        super(NapiProjektSubtitle, self).__init__(language, hash)
        self.release_info = release_info
        self.matches = matches or set()

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.release_info, self.language)

    def get_matches(self, video):
        self.matches |= super().get_matches(video)
        return self.matches


class NapiProjektProvider(ProviderRetryMixin, _NapiProjektProvider):
    languages = {Language.fromalpha2(l) for l in ['pl']}
    video_types = (Episode, Movie)
    subtitle_class = NapiProjektSubtitle

    def __init__(self, only_authors=None, only_real_names=None):
        super().__init__()
        self.only_authors = only_authors
        self.only_real_names = only_real_names

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

        def query_retry(params):
            res = self.session.get(self.server_url, params=params, timeout=10)
            res.raise_for_status()
            return res

        r = self.retry(
            lambda: query_retry(params=params),
            amount=QUERY_RETRIES,
            retry_timeout=QUERY_TIMEOUT
        )

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
        def flatten(nested_list):
            """Flatten a nested list."""
            return [item for sublist in nested_list for item in sublist]

        # Determine the source of subtitles based on conditions
        hash_subtitles = []
        if not (self.only_authors or self.only_real_names):
            hash_subtitles = [
                subtitle
                for language in languages
                if (subtitle := self.query(language, video.hashes.get('napiprojekt'))) is not None
            ]

        # Scrape additional subtitles
        scraped_subtitles = flatten([self._scrape(video, language) for language in languages])

        return hash_subtitles + scraped_subtitles

    def download_subtitle(self, subtitle):
        if subtitle.content is not None:
            return
        subtitle.content = self.query(subtitle.language, subtitle.hash).content

    def _scrape(self, video, language):
        if language.alpha2 != 'pl':
            return []
        title, matches = self._find_title(video)

        if title is None:
            return []
        episode = f'-s{video.season:02d}e{video.episode:02d}' if isinstance(
            video, Episode) else ''

        def query_retry():
            res = self.session.get(f'https://www.napiprojekt.pl/napisy1,7,0-dla-{title}{episode}')
            res.raise_for_status()
            return res

        response = self.retry(
            lambda: query_retry(),
            amount=QUERY_RETRIES,
            retry_timeout=QUERY_TIMEOUT
        )

        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        subtitles = []

        # Find all rows with titles and napiprojekt links
        rows = soup.find_all("tr", title=True)

        for row in rows:
            for link in row.find_all('a'):
                if 'class' in link.attrs and 'tableA' in link.attrs['class']:
                    title = row['title']
                    hash = link.attrs['href'][len('napiprojekt:'):]

                    data = row.find_all('p')

                    size = data[1].contents[0] if len(data) > 1 and data[1].contents else ""
                    length = data[3].contents[0] if len(data) > 3 and data[3].contents else ""
                    author = data[4].contents[0] if len(data) > 4 and data[4].contents else ""
                    added = data[5].contents[0] if len(data) > 5 and data[5].contents else ""

                    if author == "":
                        match = re.search(r"<b>Autor:</b> (.*?)\(", title)
                        print(title)
                        if match:
                            author = match.group(1).strip()
                        else:
                            author = ""

                    if self.only_authors:
                        if author.lower() in ["brak", "automat", "si", "chatgpt", "ai", "robot", "maszynowe", "tłumaczenie maszynowe"]:
                            continue

                    if self.only_real_names:
                        # Check if `self.only_authors` contains exactly 2 uppercase letters and at least one lowercase letter
                        if not (re.match(r'^(?=(?:.*[A-Z]){2})(?=.*[a-z]).*$', author) or
                                re.match(r'^\w+\s\w+$', author)):
                            continue

                    match = re.search(r"<b>Video rozdzielczość:</b> (.*?)<", title)
                    if match:
                        resolution = match.group(1).strip()
                    else:
                        resolution = ""

                    match = re.search(r"<b>Video FPS:</b> (.*?)<", title)
                    if match:
                        fps = match.group(1).strip()
                    else:
                        fps = ""

                    added_lenght = "Autor: " + author + " | " + resolution + " | " + fps + " | " + size + " | " + added + " | " + length
                    subtitles.append(
                        NapiProjektSubtitle(language,
                                            hash,
                                            release_info=added_lenght,
                                            matches=matches | ({'season', 'episode'} if episode else set())))

        logger.debug(f'Found subtitles {subtitles}')
        return subtitles

    def _find_title(self, video):
        def query_retry():
            res = self.session.post('https://www.napiprojekt.pl/ajax/search_catalog.php', {
                'queryString': video.series if isinstance(video, Episode) else video.title,
                'queryKind': 1 if isinstance(video, Episode) else 2,
                'queryYear': str(video.year) if video.year is not None else '',
                'associate': '',
            })
            res.raise_for_status()
            return res

        search_response = self.retry(
            lambda: query_retry(),
            amount=QUERY_RETRIES,
            retry_timeout=QUERY_TIMEOUT
        )

        search_response.raise_for_status()

        soup = BeautifulSoup(search_response.content, 'html.parser')
        imdb_id = video.series_imdb_id if isinstance(
            video, Episode) else video.imdb_id

        def match_title_tag(
                tag):
            return tag.name == 'a' and 'class' in tag.attrs and 'movieTitleCat' in tag.attrs[
                'class'] and 'href' in tag.attrs

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
