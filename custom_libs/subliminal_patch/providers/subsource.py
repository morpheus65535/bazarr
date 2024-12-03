# -*- coding: utf-8 -*-
import logging
import os
import time
import io

from zipfile import ZipFile, is_zipfile
from urllib.parse import urljoin
from requests import Session, JSONDecodeError

from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import ConfigurationError, DownloadLimitExceeded
from subliminal_patch.exceptions import APIThrottled
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

retry_amount = 3
retry_timeout = 5


class SubsourceSubtitle(Subtitle):
    provider_name = 'subsource'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, download_link, file_id, release_names, uploader,
                 season=None, episode=None):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.season = season
        self.episode = episode
        self.releases = release_names
        self.release_info = ', '.join(release_names)
        self.language = language
        self.forced = forced
        self.hearing_impaired = hearing_impaired
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = download_link
        self.uploader = uploader
        self.matches = None

    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # season
            if video.season == self.season:
                matches.add('season')
            # episode
            if video.episode == self.episode:
                matches.add('episode')
            # imdb
            matches.add('series_imdb_id')
        else:
            # title
            matches.add('title')
            # imdb
            matches.add('imdb_id')

        utils.update_matches(matches, video, self.release_info)

        self.matches = matches

        return matches


class SubsourceProvider(ProviderRetryMixin, Provider):
    """Subsource Provider"""
    server_url = 'https://api.subsource.net/api/'

    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'bul', 'ces', 'dan', 'deu', 'ell', 'eng', 'fin', 'fra', 'hun', 'ita', 'jpn', 'kor', 'nld', 'pol', 'por',
        'ron', 'rus', 'spa', 'swe', 'tur', 'ukr', 'zho'
    ]}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))

    video_types = (Episode, Movie)

    def __init__(self):
        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        self.video = None
        self._started = None

    def initialize(self):
        self._started = time.time()

    def terminate(self):
        self.session.close()

    @staticmethod
    def parse_json(response):
        try:
            return response.json()
        except JSONDecodeError:
            logging.debug("Unable to parse server response")
            return False

    def searchMovie(self, imdb_id=None, title=None):
        res = self.session.post(f"{self.server_url}searchMovie",
                                json={'query': imdb_id or title},
                                timeout=30)
        results = self.parse_json(res)
        if results and 'found' in results and isinstance(results['found'], list) and len(results['found']) > 0:
            return results['found'][0]['linkName']
        return False

    def getMovie(self, title, season=None):
        data = {'movieName': title}
        if season:
            data.update({'season': f"season-{season}"})
        res = self.session.post(f"{self.server_url}getMovie",
                                json=data,
                                timeout=30)
        results = self.parse_json(res)
        if results and 'subs' in results and isinstance(results['subs'], list) and len(results['subs']) > 0:
            subs_to_return = []
            for sub in results['subs']:
                subs_to_return.append({
                    'movie': sub['linkName'],
                    'lang': sub['lang'],
                    'id': sub['subId'],
                })
            return subs_to_return
        return False

    def getSub(self, title, season=None):
        data = {'movieName': title}
        if season:
            data.update({'season': f"season-{season}"})
        res = self.session.post(f"{self.server_url}getSub",
                                json=data,
                                timeout=30)
        results = self.parse_json(res)
        if results and 'subs' in results and isinstance(results['subs'], list) and len(results['subs']) > 0:
            subs_to_return = []
            for sub in results['subs']:
                subs_to_return.append({
                    'page_link': f"https://subsource.net{sub['fullLink']}",
                    'uploader': sub['uploadedBy'],
                    'release_info': sub['releaseName'],
                    'file_id': sub['subId'],
                    'language': sub['lang'],
                })
            return results['found'][0]['linkName']
        return False

    def query(self, languages, video):
        self.video = video
        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        imdb_id = None
        if isinstance(self.video, Episode) and self.video.series_imdb_id:
            imdb_id = self.video.series_imdb_id
        elif isinstance(self.video, Movie) and self.video.imdb_id:
            imdb_id = self.video.imdb_id

        linkName = self.search(imdb_id=imdb_id, title=title)

        # query the server
        if isinstance(self.video, Episode):
            res = self.retry(
                lambda: self.session.get(f"{self.server_url}subtitles",
                                         params=(('episode_number', self.video.episode),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('season_number', self.video.season),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('bazarr', 1)),  # this argument filter incompatible image based or
                                         # txt subtitles
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
        else:
            res = self.retry(
                lambda: self.session.get(f"{self.server_url}subtitles",
                                         params=(('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('subs_per_page', 30),
                                                 ('type', 'movie'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('bazarr', 1)),  # this argument filter incompatible image based or
                                         # txt subtitles
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )

        if res.status_code == 429:
            raise APIThrottled("Too many requests")
        elif res.status_code == 403:
            raise ConfigurationError("Invalid API key")
        elif res.status_code != 200:
            res.raise_for_status()

        subtitles = []

        result = res.json()

        if ('success' in result and not result['success']) or ('status' in result and not result['status']):
            logger.debug(result["error"])
            return []

        logger.debug(f"Query returned {len(result['subtitles'])} subtitles")

        if len(result['subtitles']):
            for item in result['subtitles']:
                if (isinstance(self.video, Episode) and
                        item.get('episode_from', False) != item.get('episode_end', False)):
                    # ignore season packs
                    continue
                else:
                    subtitle = SubsourceSubtitle(
                        language=item['language'],
                        forced=self._is_forced(item),
                        hearing_impaired=item.get('hi', False) or self._is_hi(item),
                        page_link=urljoin("https://api.subsource.net", item.get('subtitlePage', '')),
                        download_link=item['url'],
                        file_id=item['name'],
                        release_names=item.get('releases', []),
                        uploader=item.get('author', ''),
                        season=item.get('season', None),
                        episode=item.get('episode', None),
                    )
                    subtitle.get_matches(self.video)
                    if subtitle.language in languages:  # make sure only desired subtitles variants are returned
                        subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _is_hi(item):
        # Comments include specific mention of removed or non HI
        non_hi_tag = ['hi remove', 'non hi', 'nonhi', 'non-hi', 'non-sdh', 'non sdh', 'nonsdh', 'sdh remove']
        for tag in non_hi_tag:
            if tag in item.get('comment', '').lower():
                return False

        # Archive filename include _HI_
        if '_hi_' in item.get('name', '').lower():
            return True

        # Comments or release names include some specific strings
        hi_keys = [item.get('comment', '').lower(), [x.lower() for x in item.get('releases', [])]]
        hi_tag = ['_hi_', ' hi ', '.hi.', 'hi ', ' hi', 'sdh', '𝓢𝓓𝓗']
        for key in hi_keys:
            if any(x in key for x in hi_tag):
                return True

        # nothing match so we consider it as non-HI
        return False

    @staticmethod
    def _is_forced(item):
        # Comments include specific mention of forced subtitles
        forced_tags = ['forced', 'foreign']
        for tag in forced_tags:
            if tag in item.get('comment', '').lower():
                return True

        # nothing match so we consider it as normal subtitles
        return False

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r', subtitle)
        download_link = urljoin("https://api.subsource.net", subtitle.download_link)

        r = self.retry(
            lambda: self.session.get(download_link, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        if r.status_code == 429:
            raise DownloadLimitExceeded("Daily download limit exceeded")
        elif r.status_code == 403:
            raise ConfigurationError("Invalid API key")
        elif r.status_code != 200:
            r.raise_for_status()

        if not r:
            logger.error(f'Could not download subtitle from {download_link}')
            subtitle.content = None
            return
        else:
            archive_stream = io.BytesIO(r.content)
            if is_zipfile(archive_stream):
                archive = ZipFile(archive_stream)
                for name in archive.namelist():
                    # TODO when possible, deal with season pack / multiple files archive
                    subtitle_content = archive.read(name)
                    subtitle.content = fix_line_ending(subtitle_content)
                    return
            else:
                logger.error(f'Could not unzip subtitle from {download_link}')
                subtitle.content = None
                return
