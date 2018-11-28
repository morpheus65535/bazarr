# coding=utf-8

import logging


from subzero.language import Language
from subliminal.providers import ParserBeautifulSoup
from subliminal.cache import SHOW_EXPIRATION_TIME, region, EPISODE_EXPIRATION_TIME
from subliminal.providers.tvsubtitles import TVsubtitlesProvider as _TVsubtitlesProvider, \
    TVsubtitlesSubtitle as _TVsubtitlesSubtitle, link_re, episode_id_re
from subliminal.utils import sanitize

logger = logging.getLogger(__name__)


class TVsubtitlesSubtitle(_TVsubtitlesSubtitle):
    def __init__(self, language, page_link, subtitle_id, series, season, episode, year, rip, release):
        super(TVsubtitlesSubtitle, self).__init__(language, page_link, subtitle_id, series, season, episode,
                                                  year, rip, release)
        self.release_info = u"%s, %s" % (rip, release)


class TVsubtitlesProvider(_TVsubtitlesProvider):
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'bul', 'ces', 'dan', 'deu', 'ell', 'eng', 'fin', 'fra', 'hun', 'ita', 'jpn', 'kor', 'nld', 'pol', 'por',
        'ron', 'rus', 'spa', 'swe', 'tur', 'ukr', 'zho'
    ]}
    subtitle_class = TVsubtitlesSubtitle

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def search_show_id(self, series, year=None):
        """Search the show id from the `series` and `year`.
        :param string series: series of the episode.
        :param year: year of the series, if any.
        :type year: int or None
        :return: the show id, if any.
        :rtype: int or None
        """
        # make the search
        logger.info('Searching show id for %r', series)
        r = self.session.post(self.server_url + 'search.php', data={'q': series}, timeout=10)
        r.raise_for_status()

        # get the series out of the suggestions
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
        show_id = None
        for suggestion in soup.select('div.left li div a[href^="/tvshow-"]'):
            match = link_re.match(suggestion.text)
            if not match:
                logger.error('Failed to match %s', suggestion.text)
                continue

            if sanitize(match.group('series')).lower() == series.lower():
                if year is not None and int(match.group('first_year')) != year:
                    logger.debug('Year does not match')
                    continue
                show_id = int(suggestion['href'][8:-5])
                logger.debug('Found show id %d', show_id)
                break

        soup.decompose()
        soup = None

        return show_id

    @region.cache_on_arguments(expiration_time=EPISODE_EXPIRATION_TIME)
    def get_episode_ids(self, show_id, season):
        """Get episode ids from the show id and the season.

        :param int show_id: show id.
        :param int season: season of the episode.
        :return: episode ids per episode number.
        :rtype: dict

        """
        # get the page of the season of the show
        logger.info('Getting the page of show id %d, season %d', show_id, season)
        r = self.session.get(self.server_url + 'tvshow-%d-%d.html' % (show_id, season), timeout=10)
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over episode rows
        episode_ids = {}
        for row in soup.select('table#table5 tr'):
            # skip rows that do not have a link to the episode page
            if not row('a', href=episode_id_re):
                continue

            # extract data from the cells
            cells = row('td')
            episode = int(cells[0].text.split('x')[1])
            episode_id = int(cells[1].a['href'][8:-5])
            episode_ids[episode] = episode_id

        if episode_ids:
            logger.debug('Found episode ids %r', episode_ids)
        else:
            logger.warning('No episode ids found')

        soup.decompose()
        soup = None

        return episode_ids

    def query(self, show_id, series, season, episode, year=None):
        # get the episode ids
        episode_ids = self.get_episode_ids(show_id, season)
        # Provider doesn't store multi episode information
        episode = min(episode) if episode and isinstance(episode, list) else episode

        if episode not in episode_ids:
            logger.error('Episode %d not found', episode)
            return []

        # get the episode page
        logger.info('Getting the page for episode %d', episode_ids[episode])
        r = self.session.get(self.server_url + 'episode-%d.html' % episode_ids[episode], timeout=10)
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitles rows
        subtitles = []
        for row in soup.select('.subtitlen'):
            # read the item
            language = Language.fromtvsubtitles(row.h5.img['src'][13:-4])
            subtitle_id = int(row.parent['href'][10:-5])
            page_link = self.server_url + 'subtitle-%d.html' % subtitle_id
            rip = row.find('p', title='rip').text.strip() or None
            release = row.find('h5').text.strip() or None

            subtitle = self.subtitle_class(language, page_link, subtitle_id, series, season, episode, year, rip,
                                           release)
            logger.info('Found subtitle %s', subtitle)
            subtitles.append(subtitle)

        soup.decompose()
        soup = None

        return subtitles
