# -*- coding: utf-8 -*-
import io
import logging
import os
import re

from subzero.language import Language
from guessit import guessit
from requests import Session

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending, guess_matches
from subliminal.video import Episode, Movie
from subliminal.exceptions import ServiceUnavailable

from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class SubztvSubtitle(Subtitle):
    """Subztv Subtitle."""
    provider_name = 'subztv'

    def __init__(self, language, page_link, version, uploader, referer):
        super(SubztvSubtitle, self).__init__(language, page_link=page_link)
        self.version = version
        self.release_info = version
        self.page_link = page_link
        self.uploader = uploader
        self.referer = referer
        self.hearing_impaired = None

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # other properties
            matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)
        # movie
        elif isinstance(video, Movie):
            # other properties
            matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)

        return matches


class SubztvProvider(Provider):
    """Subztv Provider."""
    languages = {Language('ell')}
    server_url = 'https://subztv.online/'
    subtitle_class = SubztvSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")

    def terminate(self):
        self.session.close()

    def query(self, video, imdb_id, season=None, episode=None):
        logger.debug('Searching subtitles for %r', imdb_id)
        subtitles = []
        search_link = self.server_url + 'en/view/' + imdb_id

        r = self.session.get(search_link, timeout=30)
        r.raise_for_status()

        if isinstance(video, Episode):
            soup_page = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
            for item in soup_page.select('div.col-lg-offset-2.col-md-8.text-center.top30.bottom10 > a'):
                season_episode = re.search(r'Season (\d+) Episode (\d+)', item.text)
                season_number = int(season_episode.group(1))
                episode_number = int(season_episode.group(2))
                if season_number == season and episode_number == episode:
                    episode_page = item.attrs['href']
                    r = self.session.get(episode_page, timeout=30)
                    soup_subs = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
                    secCode = soup_subs.find('input', {'id': 'secCode'}).get('value')
                    for subtitles in soup_subs.select('#elSub > tbody > tr'):
                        subtitle_id = re.search(r'downloadMe\(\'(.*)\'\)', subtitles.contents[2].contents[2].contents[0].attrs['onclick']).group(1)
                        page_link = self.server_url + 'dll/' + subtitle_id + '/0/' + secCode
                        language = Language.fromalpha2(subtitles.parent.find('img')['alt'])
                        version = subtitles.contents[2].contents[4].text.strip()
                        uploader = subtitles.contents[2].contents[5].contents[0].contents[1].text.strip()
                        referer = episode_page

                        subtitle = self.subtitle_class(language, page_link, version, uploader, referer)

                        logger.debug('Found subtitle %r', subtitle)
                        subtitles.append(subtitle)
                else:
                    pass
        elif isinstance(video, Movie):
            pass

        return subtitles

    def list_subtitles(self, video, languages):
        imdbId = None
        subtitles = []

        if isinstance(video, Episode):
            imdbId = video.series_imdb_id
        elif isinstance(video, Movie):
            imdbId = video.imdb_id

        if not imdbId:
            logger.debug('No imdb number available to search with provider')
            return subtitles

        # query for subtitles with the imdbId
        response = None
        status_code = None
        try:
            if isinstance(video, Episode):
                response = self.query(video, imdbId, season=video.season, episode=video.episode)
            elif isinstance(video, Movie):
                response = self.query(video, imdbId)
            for s in response:
                if s.language in languages:
                    subtitles += s
        except RequestException as e:
            status_code = e.response.status_code
        else:
            status_code = int(response['status'][:3])

        if status_code == 503:
            raise ServiceUnavailable(str(status_code))

        return subtitles

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, SubztvSubtitle):
            # download the subtitle
            logger.info('Downloading subtitle %r', subtitle)
            r = self.session.get(subtitle.download_link, headers={'Referer': subtitle.referer},
                                 timeout=30)
            r.raise_for_status()

            if not r.content:
                logger.debug('Unable to download subtitle. No data returned from provider')
                return

            subtitle.content = fix_line_ending(r.content)
