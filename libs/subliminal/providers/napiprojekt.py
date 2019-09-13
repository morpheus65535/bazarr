# -*- coding: utf-8 -*-
import logging

from babelfish import Language
from requests import Session

from . import Provider
from .. import __short_version__
from ..subtitle import Subtitle

logger = logging.getLogger(__name__)


def get_subhash(hash):
    """Get a second hash based on napiprojekt's hash.

    :param str hash: napiprojekt's hash.
    :return: the subhash.
    :rtype: str

    """
    idx = [0xe, 0x3, 0x6, 0x8, 0x2]
    mul = [2, 2, 5, 4, 3]
    add = [0, 0xd, 0x10, 0xb, 0x5]

    b = []
    for i in range(len(idx)):
        a = add[i]
        m = mul[i]
        i = idx[i]
        t = a + int(hash[i], 16)
        v = int(hash[t:t + 2], 16)
        b.append(('%x' % (v * m))[-1])

    return ''.join(b)


class NapiProjektSubtitle(Subtitle):
    """NapiProjekt Subtitle."""
    provider_name = 'napiprojekt'

    def __init__(self, language, hash):
        super(NapiProjektSubtitle, self).__init__(language)
        self.hash = hash

    @property
    def id(self):
        return self.hash

    def get_matches(self, video):
        matches = set()

        # hash
        if 'napiprojekt' in video.hashes and video.hashes['napiprojekt'] == self.hash:
            matches.add('hash')

        return matches


class NapiProjektProvider(Provider):
    """NapiProjekt Provider."""
    languages = {Language.fromalpha2(l) for l in ['pl']}
    required_hash = 'napiprojekt'
    server_url = 'http://napiprojekt.pl/unit_napisy/dl.php'

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__

    def terminate(self):
        self.session.close()

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
        response = self.session.get(self.server_url, params=params, timeout=10)
        response.raise_for_status()

        # handle subtitles not found and errors
        if response.content[:4] == b'NPc0':
            logger.debug('No subtitles found')
            return None

        subtitle = NapiProjektSubtitle(language, hash)
        subtitle.content = response.content
        logger.debug('Found subtitle %r', subtitle)

        return subtitle

    def list_subtitles(self, video, languages):
        return [s for s in [self.query(l, video.hashes['napiprojekt']) for l in languages] if s is not None]

    def download_subtitle(self, subtitle):
        # there is no download step, content is already filled from listing subtitles
        pass
