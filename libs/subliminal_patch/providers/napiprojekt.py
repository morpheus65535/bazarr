# coding=utf-8
import logging

from subliminal.providers.napiprojekt import NapiProjektProvider as _NapiProjektProvider, \
    NapiProjektSubtitle as _NapiProjektSubtitle, get_subhash
from subzero.language import Language

logger = logging.getLogger(__name__)


class NapiProjektSubtitle(_NapiProjektSubtitle):
    def __init__(self, language, hash):
        super(NapiProjektSubtitle, self).__init__(language, hash)
        self.release_info = hash

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, self.release_info, self.language)


class NapiProjektProvider(_NapiProjektProvider):
    languages = {Language.fromalpha2(l) for l in ['pl']}
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

        subtitle = self.subtitle_class(language, hash)
        subtitle.content = r.content
        logger.debug('Found subtitle %r', subtitle)

        return subtitle

    def list_subtitles(self, video, languages):
        return [s for s in [self.query(l, video.hashes['napiprojekt']) for l in languages] if s is not None]

