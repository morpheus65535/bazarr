import logging
import os
from io import BytesIO
from zipfile import ZipFile

from requests import Session

from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal import __short_version__
from subliminal.exceptions import AuthenticationError, ConfigurationError
from subliminal.subtitle import fix_line_ending
from subzero.language import Language

logger = logging.getLogger(__name__)


class Napisy24Subtitle(Subtitle):
    '''Napisy24 Subtitle.'''
    provider_name = 'napisy24'

    def __init__(self, language, hash, imdb_id, napis_id):
        super(Napisy24Subtitle, self).__init__(language)
        self.hash = hash
        self.imdb_id = imdb_id
        self.napis_id = napis_id

    @property
    def id(self):
        return self.hash

    def get_matches(self, video):
        matches = set()

        # hash
        if 'napisy24' in video.hashes and video.hashes['napisy24'] == self.hash:
            matches.add('hash')

        # imdb_id
        if video.imdb_id and self.imdb_id == video.imdb_id:
            matches.add('imdb_id')

        return matches


class Napisy24Provider(Provider):
    '''Napisy24 Provider.'''
    languages = {Language(l) for l in ['pol']}
    required_hash = 'napisy24'
    api_url = 'http://napisy24.pl/run/CheckSubAgent.php'

    def __init__(self, username=None, password=None):
        if all((username, password)):
            self.username = username
            self.password = password
        else:
            self.username = 'subliminal'
            self.password = 'lanimilbus'

        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

    def terminate(self):
        self.session.close()

    def query(self, language, size, name, hash):
        params = {
            'postAction': 'CheckSub',
            'ua': self.username,
            'ap': self.password,
            'fs': size,
            'fh': hash,
            'fn': os.path.basename(name),
            'n24pref': 1
        }

        response = self.session.post(self.api_url, data=params, timeout=10)
        response.raise_for_status()

        response_content = response.content.split(b'||', 1)
        n24_data = response_content[0].decode()

        if n24_data[:2] != 'OK':
            if n24_data[:11] == 'login error':
                raise AuthenticationError('Login failed')
            logger.error('Unknown response: %s', response.content)
            return None

        n24_status = n24_data[:4]
        if n24_status == 'OK-0':
            logger.info('No subtitles found')
            return None

        subtitle_info = dict(p.split(':', 1) for p in n24_data.split('|')[1:])
        logger.debug('Subtitle info: %s', subtitle_info)

        if n24_status == 'OK-1':
            logger.info('No subtitles found but got video info')
            return None
        elif n24_status == 'OK-2':
            logger.info('Found subtitles')
        elif n24_status == 'OK-3':
            logger.info('Found subtitles but not from Napisy24 database')
            return None
        
        subtitle_content = response_content[1]

        subtitle = Napisy24Subtitle(language, hash, 'tt%s' % subtitle_info['imdb'].zfill(7), subtitle_info['napisId'])
        with ZipFile(BytesIO(subtitle_content)) as zf:
            subtitle.content = fix_line_ending(zf.open(zf.namelist()[0]).read())

        return subtitle

    def list_subtitles(self, video, languages):
        subtitles = [self.query(l, video.size, video.name, video.hashes['napisy24']) for l in languages]
        return [s for s in subtitles if s is not None]

    def download_subtitle(self, subtitle):
        # there is no download step, content is already filled from listing subtitles
        pass
