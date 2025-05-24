# -*- coding: utf-8 -*-
import logging
import os
import time

from babelfish import language_converters
from requests import Session, JSONDecodeError
from guessit import guessit

from subzero.language import Language
from subliminal import Episode, Movie
from subliminal_patch.exceptions import APIThrottled
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

language_converters.register('subsource = subliminal_patch.converters.subsource:SubsourceConverter')

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

    languages = ({Language.fromsubsource(l) for l in language_converters['subsource'].codes} |
                 {Language("spa", "MX")} |
                 {Language("zho", "CN")} |
                 {Language("zho", "TW")})
    languages.update(set(Language.rebuild(lang, hi=True) for lang in languages))
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))

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

    def getMovie(self, languages, title, season=None):
        data = {'movieName': title}
        if season:
            data.update({'season': f"season-{season}"})
        res = self.session.post(f"{self.server_url}getMovie",
                                json=data,
                                timeout=30)
        results = self.parse_json(res)
        if results and 'subs' in results and isinstance(results['subs'], list) and len(results['subs']) > 0:
            subs_seen = []
            subs_to_return = []
            for sub in results['subs']:
                if sub['subId'] in subs_seen:
                    # subtitles ID already included in results so we don't query further for duplicates
                    continue

                if 'lang' not in sub:
                    logger.debug(f"No language found for https://subsource.net{sub['fullLink']}")
                    continue
                language = Language.fromsubsource(sub['lang'])
                if language.alpha3 == "zho" and "traditional" in sub['commentary'].lower():
                        language = Language.rebuild(language, country="TW")
                elif language.alpha3 == "spa" and "latin" in sub['commentary'].lower():
                        language = Language.rebuild(language, country="MX")

                if language in languages:
                    if isinstance(self.video, Episode):
                        guess = guessit(sub['releaseName'])
                        if 'episode' not in guess or guess['episode'] != self.video.episode:
                            # episode number guessed from release name doesn't match the video episode number
                            continue

                    sub_details = self.getSub(lang=sub['lang'], title=sub['linkName'], sub_id=sub['subId'])
                    if sub_details:
                        subs_to_return.append(
                            SubsourceSubtitle(language=language,
                                              forced=sub_details['forced'],
                                              hearing_impaired=sub['hi'] == 1,
                                              page_link=f"https://subsource.net{sub['fullLink']}",
                                              download_link=sub_details['download_link'],
                                              file_id=sub['subId'],
                                              release_names=sub_details['releases_info'],
                                              uploader=sub['uploadedBy'],
                                              season=None,
                                              episode=None),
                        )
                        subs_seen.append(sub['subId'])
            return subs_to_return
        return []

    def getSub(self, lang, title, sub_id):
        data = {'movie': title,
                'lang': lang.replace(' ', '_'),
                'id': sub_id}
        res = self.session.post(f"{self.server_url}getSub",
                                json=data,
                                timeout=30)
        result = self.parse_json(res)
        if result and 'sub' in result and isinstance(result['sub'], dict):
            return {
                'download_link': f"{self.server_url}downloadSub/{result['sub']['downloadToken']}",
                'forced': result['sub']['fp'] == 1,
                'releases_info': result['sub']['ri'],
            }
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

        movie_name = self.searchMovie(imdb_id=imdb_id, title=title)
        if movie_name:
            return self.getMovie(languages=languages, title=movie_name, season=self.video.season if hasattr(self.video, 'season') else None)
        else:
            return []

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        # download the subtitle
        logger.debug("Downloading subtitle %r", subtitle)

        response = self.session.get(
            subtitle.download_link,
            headers={"Referer": self.server_url},
            timeout=30,
        )
        response.raise_for_status()

        # TODO: add MustGetBlacklisted support

        archive = utils.get_archive_from_bytes(response.content)
        if archive is None:
            raise APIThrottled("Unknwon compressed format")

        subtitle.content = utils.get_subtitle_from_archive(archive, get_first_subtitle=True)
