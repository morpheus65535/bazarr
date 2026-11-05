# -*- coding: utf-8 -*-
import logging
import re
from random import randint

from subzero.language import Language
from guessit import guessit
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.subtitle import guess_matches
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import Subtitle, fix_line_ending
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)


class GreekSubsSubtitle(Subtitle):
    """GreekSubs Subtitle."""
    provider_name = 'greeksubs'
    hearing_impaired_verifiable = False

    def __init__(self, language, page_link, version, uploader, referer, subtitle_id):
        super(GreekSubsSubtitle, self).__init__(language, page_link=page_link)
        self.version = version.replace('-', '.')
        self.release_info = version
        self.page_link = page_link
        self.download_link = page_link
        self.uploader = uploader
        self.referer = referer
        self.subtitle_id = subtitle_id
        self.matches = set()

    @property
    def id(self):
        return self.subtitle_id

    def get_matches(self, video):
        # episode
        if isinstance(video, Episode):
            # Blatanly match the year
            self.matches.add("year")
            # other properties
            self.matches |= guess_matches(video, guessit(self.version, {'type': 'episode'}), partial=True)
        # movie
        elif isinstance(video, Movie):
            # other properties
            self.matches |= guess_matches(video, guessit(self.version, {'type': 'movie'}), partial=True)

        return self.matches


class GreekSubsProvider(Provider):
    """GreekSubs Provider."""
    languages = {Language('ell')}
    video_types = (Episode, Movie)
    server_url = 'https://greeksubs.net/'
    subtitle_class = GreekSubsSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = RetryingCFSession()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        self.session.close()

    def _parse_subtitle_row(self, subtitles_item, sec_code, referer):
        try:
            download_button = subtitles_item.find('button', {'onclick': re.compile(r'^downloadMe')})
            subtitle_id = re.search(r"downloadMe\('([^']+)'\)", download_button.get('onclick')).group(1)
            language_image = subtitles_item.find('img', {'src': re.compile(r'/resources/lang/')})
            language = Language.fromalpha2(language_image.get('alt'))
            download_cell = download_button.find_parent('td')
            version_cell = download_cell.find_next_sibling('td').find_next_sibling('td')
            version = version_cell.get_text(strip=True)
            uploader = subtitles_item.find(class_='userNameBox').get_text(strip=True)
        except Exception as e:
            logging.debug(e)
            return None

        download_link = self.server_url + 'dll/' + subtitle_id + '/0/' + sec_code
        return self.subtitle_class(language, download_link, version, uploader, referer, subtitle_id)

    def query(self, video, languages, imdb_id, season=None, episode=None):
        logger.debug('Searching subtitles for %r', imdb_id)
        subtitles = []
        search_link = self.server_url + 'en/view/' + imdb_id

        r = self.session.get(search_link, timeout=30)

        # 404 is returned if the imdb_id was not found
        if r.status_code == 404:
            logger.debug('IMDB id {} not found on greeksubs'.format(imdb_id))
            return subtitles

        if r.status_code != 200:
            r.raise_for_status()

        soup_page = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])

        if isinstance(video, Episode):
            try:
                episodes = soup_page.select('div.col-lg-offset-2.col-md-8.text-center.top30.bottom10 > a')
                for item in episodes:
                    season_episode = re.search(r'Season (\d+) Episode (\d+)', item.text)
                    season_number = int(season_episode.group(1))
                    episode_number = int(season_episode.group(2))
                    if season_number == season and episode_number == episode:
                        episode_page = item.attrs['href']
                        r = self.session.get(episode_page, timeout=30)
                        soup_subs = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
                        try:
                            secCode = soup_subs.find('input', {'id': 'secCode'}).get('value')
                        except Exception as e:
                            logging.debug(e)
                        else:
                            for subtitles_item in soup_subs.select('#elSub > tbody > tr'):
                                subtitle = self._parse_subtitle_row(subtitles_item, secCode, episode_page)
                                if subtitle is not None and subtitle.language in languages:
                                    logger.debug('Found subtitle %r', subtitle)
                                    subtitles.append(subtitle)
                    else:
                        pass
            except Exception as e:
                logging.debug(e)
        elif isinstance(video, Movie):
            try:
                soup_subs = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
                try:
                    secCode = soup_subs.find('input', {'id': 'secCode'}).get('value')
                except Exception as e:
                    logging.debug(e)
                else:
                    for subtitles_item in soup_subs.select('#elSub > tbody > tr'):
                        subtitle = self._parse_subtitle_row(subtitles_item, secCode, search_link)
                        if subtitle is not None and subtitle.language in languages:
                            logger.debug('Found subtitle %r', subtitle)
                            subtitles.append(subtitle)
            except Exception as e:
                logging.debug(e)

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
        subtitles = []

        if isinstance(video, Episode):
            subtitles = self.query(video, languages, imdbId, season=video.season, episode=video.episode)
        elif isinstance(video, Movie):
            subtitles = self.query(video, languages, imdbId)

        return subtitles

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.page_link,
                             headers={'Referer': subtitle.referer},
                             timeout=30, allow_redirects=False)

        if r.status_code == 302:
            if not self._refresh_download_link(subtitle):
                logger.error("Unable to refresh Greeksubs single use download token")
                return False

            r = self.session.get(subtitle.page_link,
                                 headers={'Referer': subtitle.referer},
                                 timeout=30, allow_redirects=False)

            if r.status_code == 302:
                logger.error("Greeksubs single use download token is still invalid after refresh")
                return False

        r.raise_for_status()

        content_type = r.headers.get('Content-Type', '').lower()
        content_disposition = r.headers.get('Content-Disposition', '').lower()
        if r.content and ('attachment' in content_disposition or
                          content_type and not content_type.startswith('text/html')):
            subtitle.content = fix_line_ending(r.content)
            return

        download_req = None
        soup_dll = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
        try:
            langcode = soup_dll.find(attrs={"name": 'langcode'}).get('value')
            uid = soup_dll.find(attrs={"name": 'uid'}).get('value')
            output = soup_dll.find(attrs={"name": 'output'}).get('value')
            dll = soup_dll.find(attrs={"name": 'dll'}).get('value')
        except Exception as e:
            logging.debug(e)
        else:
            download_req = self.session.post(subtitle.download_link, data={'langcode': langcode,
                                                                           'uid': uid,
                                                                           'output': output,
                                                                           'dll': dll},
                                             headers={'Referer': subtitle.page_link}, timeout=10)

        if download_req is None or not download_req.content:
            logger.error('Unable to download subtitle. No data returned from provider')
            return False

        subtitle.content = fix_line_ending(download_req.content)

    def _refresh_download_link(self, subtitle):
        r = self.session.get(subtitle.referer, timeout=30)
        r.raise_for_status()

        soup_page = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
        sec_code_input = soup_page.find('input', {'id': 'secCode'})
        if sec_code_input is None or not sec_code_input.get('value'):
            return False

        download_link = self.server_url + 'dll/' + subtitle.subtitle_id + '/0/' + sec_code_input.get('value')
        subtitle.page_link = download_link
        subtitle.download_link = download_link
        return True
