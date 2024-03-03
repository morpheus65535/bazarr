# -*- coding: utf-8 -*-
import io
import json
import logging
from zipfile import ZipFile

from babelfish import Language
from guessit import guessit
from requests import Session
from six.moves import urllib

from . import Provider
from ..cache import EPISODE_EXPIRATION_TIME, region
from ..exceptions import ProviderError
from ..matches import guess_matches
from ..subtitle import Subtitle, fix_line_ending
from ..video import Episode

logger = logging.getLogger(__name__)


class ArgenteamSubtitle(Subtitle):
    provider_name = 'argenteam'

    def __init__(self, language, download_link, series, season, episode, release, version):
        super(ArgenteamSubtitle, self).__init__(language, download_link)
        self.download_link = download_link
        self.series = series
        self.season = season
        self.episode = episode
        self.release = release
        self.version = version

    @property
    def id(self):
        return self.download_link

    @property
    def info(self):
        return urllib.parse.unquote(self.download_link.rsplit('/')[-1])

    def get_matches(self, video):
        matches = guess_matches(video, {
            'title': self.series,
            'season': self.season,
            'episode': self.episode,
            'release_group': self.version
        })

        # resolution
        if video.resolution and self.version and video.resolution in self.version.lower():
            matches.add('resolution')

        matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)
        return matches


class ArgenteamProvider(Provider):
    provider_name = 'argenteam'
    language = Language.fromalpha2('es')
    languages = {language}
    video_types = (Episode,)
    server_url = "http://argenteam.net/api/v1/"
    subtitle_class = ArgenteamSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = self.user_agent

    def terminate(self):
        self.session.close()

    @region.cache_on_arguments(expiration_time=EPISODE_EXPIRATION_TIME, should_cache_fn=lambda value: value)
    def search_episode_id(self, series, season, episode):
        """Search the episode id from the `series`, `season` and `episode`.

        :param str series: series of the episode.
        :param int season: season of the episode.
        :param int episode: episode number.
        :return: the episode id, if any.
        :rtype: int or None

        """
        # make the search
        query = '%s S%#02dE%#02d' % (series, season, episode)
        logger.info('Searching episode id for %r', query)
        r = self.session.get(self.server_url + 'search', params={'q': query}, timeout=10)
        r.raise_for_status()
        results = json.loads(r.text)
        if results['total'] == 1:
            return results['results'][0]['id']

        logger.error('No episode id found for %r', series)

    def query(self, series, season, episode):
        episode_id = self.search_episode_id(series, season, episode)
        if episode_id is None:
            return []

        response = self.session.get(self.server_url + 'episode', params={'id': episode_id}, timeout=10)
        response.raise_for_status()
        content = json.loads(response.text)
        subtitles = []
        for r in content['releases']:
            for s in r['subtitles']:
                subtitle = self.subtitle_class(self.language, s['uri'], series, season, episode, r['team'], r['tags'])
                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        titles = [video.series] + video.alternative_series
        for title in titles:
            subs = self.query(title, video.season, video.episode)
            if subs:
                return subs

        return []

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            if len(zf.namelist()) > 1:
                raise ProviderError('More than one file to unzip')

            subtitle.content = fix_line_ending(zf.read(zf.namelist()[0]))
