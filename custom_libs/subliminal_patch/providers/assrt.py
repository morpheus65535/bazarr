# -*- coding: utf-8 -*-
import logging
import os
import re

from babelfish import language_converters
from guessit import guessit
from requests import Session
from requests.exceptions import JSONDecodeError
from time import sleep
from math import ceil

from subliminal import Movie, Episode
from subliminal.exceptions import ConfigurationError, ProviderError
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subzero.language import Language

logger = logging.getLogger(__name__)

language_converters.register('assrt = subliminal_patch.converters.assrt:AssrtConverter')

server_url = 'https://api.assrt.net/v1'
supported_languages = list(language_converters['assrt'].to_assrt.keys())


def get_request_delay(max_request_per_minute):
    return ceil(60 / max_request_per_minute)


def language_contains(subset, superset):
    if subset.alpha3 != superset.alpha3:
        return False
    if superset.country is not None and subset.country != superset.country:
        return False
    if superset.script is not None and subset.script != superset.script:
        return False
    return True


def search_language_in_list(lang, langlist):
    for language in langlist:
        if language_contains(lang, language):
            return language
    return None


def check_status_code(resp):
    try:
        response = resp.json()
        if 'status' in response and 'errmsg' in response:
            raise ProviderError(f'{response["errmsg"]} ({response["status"]})')
    except JSONDecodeError:
        pass


class AssrtSubtitle(Subtitle):
    """Assrt Sbutitle."""
    provider_name = 'assrt'
    guessit_options = {
        'allowed_languages': [lang[0] for lang in supported_languages],
        # 'allowed_countries': [ l[1] for l in supported_languages if len(l) > 1 ],
        'enforce_list': True
    }

    def __init__(self, language, subtitle_id, video_name, session, token, max_request_per_minute):
        super(AssrtSubtitle, self).__init__(language)
        self.session = session
        self.token = token
        self.max_request_per_minute = max_request_per_minute
        self.subtitle_id = subtitle_id
        self.video_name = video_name
        self.release_info = video_name
        self.url = None
        self._detail = None

    def _get_detail(self):
        if self._detail:
            return self._detail
        params = {'token': self.token, 'id': self.id}
        logger.info('Get subtitle detail: GET /sub/detail %r', params)
        sleep(get_request_delay(self.max_request_per_minute))
        r = self.session.get(server_url + '/sub/detail', params=params, timeout=15)
        check_status_code(r)
        r.raise_for_status()

        result = r.json()
        if not len(result['sub']['subs']):
            logger.error('Can\'t get subtitle details')
            return False
        sub = result['sub']['subs'][0]
        if not len(sub['filelist']):
            logger.error('Can\'t get filelist from subtitle details')
            return False
        files = sub['filelist']

        # first pass: guessit
        for f in files:
            guess = guessit(f['f'], self.guessit_options)
            langs = set()
            if 'language' in guess:
                langs.update(guess['language'])
            if 'subtitle_language' in guess:
                langs.update(guess['subtitle_language'])
            if self.language in langs:
                self._detail = f
                return f

        # second pass: keyword matching
        codes = language_converters['assrt'].codes
        for f in files:
            langs = set([Language.fromassrt(k) for k in codes if k in f['f']])
            if self.language in langs:
                self._detail = f
                return f

        # fallback: pick up first file if nothing matches
        return files[0]

    @property
    def id(self):
        return self.subtitle_id

    @property
    def download_link(self):
        detail = self._get_detail()
        return detail['url']

    def get_matches(self, video):
        matches = guess_matches(video, guessit(self.video_name))
        return matches


class AssrtProvider(Provider):
    """Assrt Provider."""
    languages = {Language(*lang) for lang in supported_languages}
    video_types = (Episode, Movie)

    def __init__(self, token=None):
        if not token:
            raise ConfigurationError('Token must be specified')
        self.token = token
        self.session = Session()
        self.max_request_per_minute = None

    def initialize(self):
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        res = self.session.get(server_url + '/user/quota', params={'token': self.token}, timeout=15)
        check_status_code(res)
        res.raise_for_status()
        result = res.json()
        if 'user' in result and 'quota' in result['user']:
            self.max_request_per_minute = result['user']['quota']

        if not isinstance(self.max_request_per_minute, int):
            raise ProviderError(f'Cannot get user request quota per minute from provider: {result}')

        if self.max_request_per_minute <= 0:
            raise ProviderError(f'User request quota is not a positive integer: {self.max_request_per_minute}')

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        # query the server
        keywords = []
        if isinstance(video, Movie):
            if video.title:
                # title = "".join(e for e in video.title if e.isalnum())
                title = video.title
                keywords.append(title)
            if video.year:
                keywords.append(str(video.year))
        elif isinstance(video, Episode):
            if video.series:
                # series = "".join(e for e in video.series if e.isalnum())
                series = video.series
                keywords.append(series)
            if video.season and video.episode:
                keywords.append('S%02dE%02d' % (video.season, video.episode))
            elif video.episode:
                keywords.append('E%02d' % video.episode)
        query = ' '.join(keywords)

        params = {'token': self.token, 'q': query, 'is_file': 1}
        logger.debug('Searching subtitles: GET /sub/search %r', params)
        sleep(get_request_delay(self.max_request_per_minute))
        res = self.session.get(server_url + '/sub/search', params=params, timeout=15)
        check_status_code(res)
        res.raise_for_status()
        result = res.json()

        # parse the subtitles
        pattern = re.compile(r'lang(?P<code>\w+)')
        subtitles = []
        for sub in result['sub']['subs']:
            if 'lang' not in sub:
                continue
            for key in sub['lang']['langlist'].keys():
                match = pattern.match(key)
                try:
                    language = Language.fromassrt(match.group('code'))
                    output_language = search_language_in_list(language, languages)
                    if output_language:
                        subtitles.append(AssrtSubtitle(output_language, sub['id'], sub['videoname'], self.session,
                                                       self.token, self.max_request_per_minute))
                except:
                    pass

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        sleep(get_request_delay(self.max_request_per_minute))
        r = self.session.get(subtitle.download_link, timeout=15)
        check_status_code(r)
        r.raise_for_status()

        subtitle.content = fix_line_ending(r.content)
