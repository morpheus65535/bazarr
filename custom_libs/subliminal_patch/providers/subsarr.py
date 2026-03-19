# -*- coding: utf-8 -*-
import logging
from babelfish import language_converters
from requests import Session
from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import ConfigurationError, ProviderError
from subliminal.subtitle import fix_line_ending
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider, utils
from .mixins import ProviderRetryMixin

logger = logging.getLogger(__name__)

language_converters.register('subsarr = subliminal_patch.converters.subsarr:SubsarrConverter')


class SubsarrSubtitle(Subtitle):
    provider_name = 'subsarr'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, record_id, download_url, title,
                 releases, filename, season=None, episode=None):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired)

        self.language = language
        self.hearing_impaired = hearing_impaired
        self.record_id = record_id
        self.download_url = download_url
        self.title = title
        self.releases = releases
        self.release_info = ', '.join(releases) if releases else filename
        self.filename = filename
        self.season = season
        self.episode = episode
        self.matches = set()

    @property
    def id(self):
        return self.record_id

    def get_matches(self, video):
        self.matches = set()

        if isinstance(video, Episode):
            if video.series and self.title and video.series.lower() == self.title.lower():
                self.matches.add('series')
            if video.season and self.season == video.season:
                self.matches.add('season')
            if video.episode and self.episode == video.episode:
                self.matches.add('episode')
        else:
            if video.title and self.title and video.title.lower() == self.title.lower():
                self.matches.add('title')

        utils.update_matches(self.matches, video, self.release_info)

        return self.matches


class SubsarrProvider(ProviderRetryMixin, Provider):
    """Subsarr Provider — self-hosted Subscene subtitle provider."""
    provider_name = 'subsarr'

    languages = {Language(*lang) for lang in list(language_converters['subsarr'].to_subsarr.keys())}
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))

    video_types = (Episode, Movie)
    subtitle_class = SubsarrSubtitle

    def __init__(self, base_url=None):
        if not base_url:
            raise ConfigurationError('Base URL must be specified')

        if not base_url.startswith(('http://', 'https://')):
            raise ConfigurationError('Base URL must include scheme (http:// or https://)')

        self.base_url = base_url.rstrip('/')
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/2 Bazarr/1'

    def terminate(self):
        self.session.close()

    def _url(self, path):
        return f'{self.base_url}/api/v1{path}'

    def ping(self):
        try:
            r = self.session.get(self._url('/info'), timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def _search(self, params):
        r = self.retry(
            lambda: self.session.get(self._url('/subtitles/search'), params=params, timeout=30),
            amount=3,
            retry_timeout=5,
        )
        if r.status_code != 200:
            r.raise_for_status()
        return r.json().get('items', [])

    def query(self, languages, video):
        imdb_id = None
        season = None
        episode = None
        year = None

        if isinstance(video, Episode):
            title = video.series
            imdb_id = video.series_imdb_id
            season = video.season
            episode = video.episode
        else:
            title = video.title
            imdb_id = video.imdb_id
            year = getattr(video, 'year', None)

        subtitles = []
        lang_names = set()

        for lang in languages:
            base_lang = Language.rebuild(lang, hi=False, forced=False)
            try:
                lang_name = language_converters['subsarr'].convert(
                    base_lang.alpha3, base_lang.country, base_lang.script
                )
            except ConfigurationError:
                logger.debug('Language %s not supported by subsarr', lang)
                continue
            lang_names.add(lang_name)

        for lang_name in lang_names:
            params = {'language': lang_name, 'per_page': 100}
            if season is not None:
                params['season'] = season
            if episode is not None:
                params['episode'] = episode

            items = []
            if imdb_id:
                imdb_params = {**params, 'imdb_id': imdb_id}
                if year is not None:
                    imdb_params['year'] = year
                items = self._search(imdb_params)

            # Fall back to title query if IMDB search returned nothing
            if not items and title:
                items = self._search({**params, 'query': title})

            for item in items:
                try:
                    lang_obj = Language(*language_converters['subsarr'].reverse(item['language']))
                except (ConfigurationError, KeyError):
                    logger.debug('Skipping unsupported language: %s', item.get('language'))
                    continue

                hi = item.get('hi', False)
                if hi:
                    lang_obj = Language.rebuild(lang_obj, hi=True)

                if lang_obj not in languages:
                    continue

                raw_releases = item.get('releases')
                releases = raw_releases if isinstance(raw_releases, list) else []

                subtitle = SubsarrSubtitle(
                    language=lang_obj,
                    hearing_impaired=hi,
                    record_id=item['id'],
                    download_url=item['download_url'],
                    title=item.get('title', ''),
                    releases=releases,
                    filename=item.get('filename', ''),
                    season=season,
                    episode=episode,
                )
                subtitle.get_matches(video)
                subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r from %s', subtitle, subtitle.download_url)
        r = self.retry(
            lambda: self.session.get(subtitle.download_url, timeout=30, allow_redirects=True),
            amount=3,
            retry_timeout=5,
        )
        if r.status_code != 200:
            raise ProviderError(f'Download failed with status {r.status_code}')

        subtitle.content = fix_line_ending(r.content)
