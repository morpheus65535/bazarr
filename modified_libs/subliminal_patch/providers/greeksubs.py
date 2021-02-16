# -*- coding: utf-8 -*-
import logging
import re
from random import randint

from subzero.language import Language
from guessit import guessit
from subliminal_patch.http import RetryingCFSession
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending, guess_matches
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)


class GreekSubsSubtitle(Subtitle):
    """GreekSubs Subtitle."""
    provider_name = 'greeksubs'
    hearing_impaired_verifiable = False

    def __init__(self, language, page_link, version, uploader, referer):
        super(GreekSubsSubtitle, self).__init__(language, page_link=page_link)
        self.version = version.replace('-', '.')
        self.release_info = version
        self.page_link = page_link
        self.download_link = page_link
        self.uploader = uploader
        self.referer = referer

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


class GreekSubsProvider(Provider):
    """GreekSubs Provider."""
    languages = {Language('ell')}
    server_url = 'https://greeksubs.net/'
    subtitle_class = GreekSubsSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = RetryingCFSession()
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        self.session.close()

    def query(self, video, languages, imdb_id, season=None, episode=None):
        logger.debug('Searching subtitles for %r', imdb_id)
        subtitles = []
        search_link = self.server_url + 'en/view/' + imdb_id

        r = self.session.get(search_link, timeout=30)
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
                                try:
                                    subtitle_id = re.search(r'downloadMe\(\'(.*)\'\)', subtitles_item.contents[2].contents[2].contents[0].attrs['onclick']).group(1)
                                    page_link = self.server_url + 'dll/' + subtitle_id + '/0/' + secCode
                                    language = Language.fromalpha2(subtitles_item.parent.find('img')['alt'])
                                    version = subtitles_item.contents[2].contents[4].text.strip()
                                    uploader = subtitles_item.contents[2].contents[5].contents[0].contents[1].text.strip()
                                    referer = episode_page.encode('utf-8')

                                    r = self.session.get(page_link,
                                                         headers={'Referer': referer},
                                                         timeout=30, allow_redirects=False)
                                    r.raise_for_status()
                                    soup_dll = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
                                    try:
                                        langcode = soup_dll.find(attrs={"name": 'langcode'}).get('value')
                                        uid = soup_dll.find(attrs={"name": 'uid'}).get('value')
                                        output = soup_dll.find(attrs={"name": 'output'}).get('value')
                                        dll = soup_dll.find(attrs={"name": 'dll'}).get('value')
                                    except Exception as e:
                                        logging.debug(e)
                                    else:
                                        download_req = self.session.post(page_link, data={'langcode': langcode,
                                                                                          'uid': uid,
                                                                                          'output': output,
                                                                                          'dll': dll},
                                                                         headers={'Referer': page_link}, timeout=10)
                                except Exception as e:
                                    logging.debug(e)
                                else:
                                    if language in languages:
                                        subtitle = self.subtitle_class(language, page_link, version, uploader, referer)
                                        if not download_req.content:
                                            logger.error('Unable to download subtitle. No data returned from provider')
                                            continue

                                        subtitle.content = download_req.content

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
                        try:
                            subtitle_id = re.search(r'downloadMe\(\'(.*)\'\)',
                                                    subtitles_item.contents[2].contents[2].contents[0].attrs[
                                                        'onclick']).group(1)
                            page_link = self.server_url + 'dll/' + subtitle_id + '/0/' + secCode
                            language = Language.fromalpha2(subtitles_item.parent.find('img')['alt'])
                            version = subtitles_item.contents[2].contents[4].text.strip()
                            uploader = subtitles_item.contents[2].contents[5].contents[0].contents[
                                1].text.strip()
                            referer = page_link.encode('utf-8')

                            r = self.session.get(page_link,
                                                 headers={'Referer': referer},
                                                 timeout=30, allow_redirects=False)
                            r.raise_for_status()
                            soup_dll = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
                            try:
                                langcode = soup_dll.find(attrs={"name": 'langcode'}).get('value')
                                uid = soup_dll.find(attrs={"name": 'uid'}).get('value')
                                output = soup_dll.find(attrs={"name": 'output'}).get('value')
                                dll = soup_dll.find(attrs={"name": 'dll'}).get('value')
                            except Exception as e:
                                logging.debug(e)
                            else:
                                download_req = self.session.post(page_link, data={'langcode': langcode,
                                                                                  'uid': uid,
                                                                                  'output': output,
                                                                                  'dll': dll},
                                                                 headers={'Referer': page_link}, timeout=10)
                        except Exception as e:
                            logging.debug(e)
                        else:
                            if language in languages:
                                subtitle = self.subtitle_class(language, page_link, version, uploader, referer)
                                if not download_req.content:
                                    logger.error('Unable to download subtitle. No data returned from provider')
                                    continue

                                subtitle.content = download_req.content

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
        if isinstance(subtitle, GreekSubsSubtitle):
            subtitle.content = fix_line_ending(subtitle.content)
