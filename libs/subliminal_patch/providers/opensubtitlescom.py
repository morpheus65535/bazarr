# -*- coding: utf-8 -*-
import logging
import os

from requests import Session, ConnectionError, Timeout, ReadTimeout
from subzero.language import Language

from babelfish import language_converters
from subliminal import Episode, Movie
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize_release_group, sanitize
from subliminal.exceptions import DownloadLimitExceeded, AuthenticationError, ConfigurationError, ServiceUnavailable, \
    ProviderError
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider
from subliminal.cache import region
from guessit import guessit

logger = logging.getLogger(__name__)


class OpenSubtitlesComSubtitle(Subtitle):
    provider_name = 'opensubtitlescom'
    hash_verifiable = False

    def __init__(self, language, hearing_impaired, page_link, file_id, releases, uploader, title, year,
                 hash_matched, hash=None, season=None, episode=None):
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.releases = releases
        self.release_info = releases
        self.language = language
        self.hearing_impaired = hearing_impaired
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = None
        self.uploader = uploader
        self.matches = None
        self.hash = hash
        self.encoding = 'utf-8'
        self.hash_matched = hash_matched


    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # year
            if video.year == self.year:
                matches.add('year')
            # season
            if video.season == self.season:
                matches.add('season')
            # episode
            if video.episode == self.episode:
                matches.add('episode')
        # movie
        elif isinstance(video, Movie):
            # title
            matches.add('title')
            # year
            if video.year == self.year:
                matches.add('year')

        # rest is same for both groups

        # release_group
        if (video.release_group and self.releases and
                any(r in sanitize_release_group(self.releases)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.releases and video.resolution in self.releases.lower():
            matches.add('resolution')
        # source
        if video.source and self.releases and video.source.lower() in self.releases.lower():
            matches.add('source')
        # hash
        if self.hash_matched:
            matches.add('hash')
        # other properties
        matches |= guess_matches(video, guessit(self.releases))

        self.matches = matches

        return matches


class OpenSubtitlesComProvider(ProviderRetryMixin, Provider):
    """OpenSubtitlesCom Provider"""
    server_url = 'https://www.opensubtitles.com/api/v1/'

    languages = {Language.fromopensubtitles(l) for l in language_converters['szopensubtitles'].codes}
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))

    def __init__(self, username=None, password=None, use_hash=True):
        if not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        self.token = None
        self.username = username
        self.password = password
        self.use_hash = use_hash

    def initialize(self):
        self.token = region.get("oscom_token")
        if self.token:
            self.session.headers.update({'Authorization': self.token})
            return True
        else:
            self.login()

    def terminate(self):
        self.session.close()

    def login(self):
        try:
            r = self.session.post(self.server_url + 'login',
                                  json={"username": self.username, "password": self.password},
                                  allow_redirects=False,
                                  timeout=10)
        except (ConnectionError, Timeout, ReadTimeout):
            raise ServiceUnavailable('Unknown Error, empty response: %s: %r' % (r.status_code, r))
        else:
            if r.status_code == 200:
                try:
                    self.token = r.json()['token']
                except ValueError:
                    raise ProviderError('Invalid JSON returned by provider')
                else:
                    self.session.headers.update({'Authorization': self.token})
                    region.set("oscom_token", self.token)
                    return True
            elif r.status_code == 401:
                raise AuthenticationError('Login failed: %s' % r.reason)
            else:
                raise ProviderError('Bad status code: ' + str(r.status_code))
        finally:
            return False

    def search_titles(self, title, video):
        title_id = None

        if isinstance(video, Episode):
            results = self.session.get(self.server_url + 'search/tv', params={'query': title}, timeout=10)
        else:
            results = self.session.get(self.server_url + 'search/movie', params={'query': title}, timeout=10)

        if results.status_code == 401:
            region.delete("oscom_token")
            self.login()

            if isinstance(video, Episode):
                results = self.session.get(self.server_url + 'search/tv', params={'query': title}, timeout=10)
            else:
                results = self.session.get(self.server_url + 'search/movie', params={'query': title}, timeout=10)

        results.raise_for_status()

        # deserialize results
        try:
            results_dict = results.json()['data']
        except ValueError:
            logger.debug('Unable to parse returned json')
        else:
            # loop over results
            for result in results_dict:
                if title.lower() == result['attributes']['title'].lower() and \
                        (not video.year or video.year == int(result['attributes']['year'])):
                    title_id = result['id']
                    break

            if title_id:
                return title_id
        finally:
            if not title_id:
                logger.debug('No match found for "%s"' % title)

    def query(self, languages, video):
        if self.use_hash:
            hash = video.hashes.get('opensubtitlescom')

        if isinstance(video, Episode):
            title = video.series
        else:
            title = video.title

        title_id = self.search_titles(title, video)
        if not title_id:
            return []
        lang_strings = [str(lang) for lang in languages]
        langs = ','.join(lang_strings)

        # query the server
        result = None
        if isinstance(video, Episode):
            res = self.session.get(self.server_url + 'find',
                                   params={'parent_id': title_id,
                                           'languages': langs,
                                           'episode_number': video.episode,
                                           'season_number': video.season,
                                           'moviehash': hash}, timeout=10)
        else:
            res = self.session.get(self.server_url + 'find',
                                   params={'id': title_id, 'languages': langs,
                                           'moviehash': hash}, timeout=10)
        res.raise_for_status()
        result = res.json()

        subtitles = []
        if len(result['data']):
            for item in result['data']:
                if item['type'] == 'subtitle':
                    subtitle = OpenSubtitlesComSubtitle(
                            language=Language.fromietf(item['attributes']['language']),
                            hearing_impaired=item['attributes']['hearing_impaired'],
                            page_link=item['attributes']['url'],
                            file_id=item['attributes']['files'][0]['id'],
                            releases=item['attributes']['release'],
                            uploader=item['attributes']['uploader']['name'],
                            title=item['attributes']['feature_details']['movie_name'],
                            year=video.year,
                            season=item['attributes']['feature_details']['season_number'] if isinstance(video, Episode) else None,
                            episode=item['attributes']['feature_details']['episode_number'] if isinstance(video, Episode) else None,
                            hash_matched=item['attributes']['moviehash_match'] if 'moviehash_match' in item['attributes'] else False
                        )
                    subtitle.get_matches(video)
                    subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        res = self.session.post(self.server_url + 'download',
                                json={'file_id': subtitle.file_id, 'sub_format': 'srt'},
                                headers=headers,
                                timeout=10)
        res.raise_for_status()
        subtitle.download_link = res.json()['link']

        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        subtitle_content = r.content

        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.debug('Could not download subtitle from %s', subtitle.download_link)
