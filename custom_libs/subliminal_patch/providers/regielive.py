# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import io
import os

from requests import Session, JSONDecodeError
from guessit import guessit
from subliminal_patch.exceptions import TooManyRequests, APIThrottled, ProviderError
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal.video import Episode, Movie
from subzero.language import Language
import urllib
import zipfile

logger = logging.getLogger(__name__)


class RegieLiveSubtitle(Subtitle):
    """RegieLive Subtitle."""
    provider_name = 'regielive'
    hash_verifiable = False

    def __init__(self, filename, video, link, rating, language):
        super(RegieLiveSubtitle, self).__init__(language)
        self.filename = filename
        self.page_link = link
        self.video = video
        self.rating = rating
        self.release_info = filename
        self.matches = set()

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        type_ = "movie" if isinstance(video, Movie) else "episode"
        subtitle_filename = self.filename.lower()

        # episode
        if type_ == "episode":
            # already matched in search query
            self.matches.update(['title', 'series', 'season', 'episode', 'year'])
        # movie
        else:
            # already matched in search query
            self.matches.update(['title', 'year'])

        if video.release_group and video.release_group.lower() in subtitle_filename:
            self.matches.update(['release_group', 'hash'])

        self.matches |= guess_matches(video, guessit(self.filename, {"type": type_}))

        return self.matches


class RegieLiveProvider(Provider):
    """RegieLive Provider."""
    languages = {Language(l) for l in ['ron']}
    language = list(languages)[0]
    video_types = (Episode, Movie)
    SEARCH_THROTTLE = 8
    hash_verifiable = False

    def __init__(self):
        self.initialize()

    def initialize(self):
        self.session = Session()
        self.url = 'https://api.regielive.ro/bazarr/search.php'
        self.api = 'API-BAZARR-YTZ-SL'
        self.headers = {'RL-API': self.api}

    def terminate(self):
        self.session.close()

    def query(self, video, language):
        payload = {}
        if isinstance(video, Episode):
            payload['nume'] = video.series
            payload['sezon'] = video.season
            payload['episod'] = video.episode
        elif isinstance(video, Movie):
            payload['nume'] = video.title
        payload['an'] = video.year

        response = self.checked(
            lambda: self.session.get(
                self.url + "?" + urllib.parse.urlencode(payload),
                data=payload, headers=self.headers)
        )

        subtitles = []
        if response.status_code == 200:
            try:
                results = response.json()
            except JSONDecodeError:
                raise ProviderError('Unable to parse JSON response')
            if len(results) > 0:
                results_subs = results['rezultate']
                for film in results_subs:
                    for sub in results_subs[film]['subtitrari']:
                        subtitles.append(
                            RegieLiveSubtitle(
                                results_subs[film]['subtitrari'][sub]['titlu'],
                                video,
                                results_subs[film]['subtitrari'][sub]['url'],
                                results_subs[film]['subtitrari'][sub]['rating']['nota'],
                                language))
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, self.language)

    def download_subtitle(self, subtitle):
        session = self.session
        _addheaders = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Origin': 'https://subtitrari.regielive.ro',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://subtitrari.regielive.ro',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        session.headers.update(_addheaders)
        res = self.checked(
            lambda: session.get('https://subtitrari.regielive.ro')
        )
        cookies = res.cookies
        _zipped = self.checked(
            lambda: session.get(subtitle.page_link, cookies=cookies, allow_redirects=False)
        )
        if _zipped:
            if _zipped.text == '500':
                raise ValueError('Error 500 on server')
            archive = zipfile.ZipFile(io.BytesIO(_zipped.content))
            subtitle_content = self._get_subtitle_from_archive(archive)
            subtitle.content = fix_line_ending(subtitle_content)

            return subtitle
        raise ValueError('Problems conecting to the server')

    @staticmethod
    def _get_subtitle_from_archive(archive):
        # some files have a non subtitle with .txt extension
        _tmp = list(SUBTITLE_EXTENSIONS)
        _tmp.remove('.txt')
        _subtitle_extensions = tuple(_tmp)

        for name in archive.namelist():
            # discard hidden files
            if os.path.split(name)[-1].startswith('.'):
                continue

            # discard non-subtitle files
            if not name.lower().endswith(_subtitle_extensions):
                continue

            return archive.read(name)

        raise APIThrottled('Can not find the subtitle in the compressed file')

    @staticmethod
    def checked(fn):
        """Run :fn: and check the response status before returning it.

        :param fn: the function to make an API call to provider.
        :return: the response.

        """
        response = None
        try:
            response = fn()
        except Exception:
            logger.exception('Unhandled exception raised.')
            raise ProviderError('Unhandled exception raised. Check log.')
        else:
            status_code = response.status_code

            if status_code == 301:
                raise APIThrottled()
            elif status_code == 429:
                raise TooManyRequests()

        return response
