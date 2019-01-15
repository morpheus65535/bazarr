# coding=utf-8

import logging
import re
import io

from zipfile import ZipFile

from guessit import guessit
from subliminal.subtitle import guess_matches
from subliminal.utils import sanitize
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree
from babelfish import language_converters
from subliminal import Episode
from subliminal import Movie
from subliminal.providers.podnapisi import PodnapisiProvider as _PodnapisiProvider, \
    PodnapisiSubtitle as _PodnapisiSubtitle
from subliminal_patch.utils import sanitize, fix_inconsistent_naming as _fix_inconsistent_naming
from subzero.language import Language

logger = logging.getLogger(__name__)


def fix_inconsistent_naming(title):
    """Fix titles with inconsistent naming using dictionary and sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    d = {}
    nt = title.replace("Marvels", "").replace("Marvel's", "")
    if nt != title:
        d[title] = nt

    return _fix_inconsistent_naming(title, d)


class PodnapisiSubtitle(_PodnapisiSubtitle):
    provider_name = 'podnapisi'
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, page_link, pid, releases, title, season=None, episode=None,
                 year=None, asked_for_release_group=None, asked_for_episode=None):
        super(PodnapisiSubtitle, self).__init__(language, hearing_impaired, page_link, pid, releases, title,
                                                season=season, episode=episode, year=year)
        self.release_info = u", ".join(releases)
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
        self.matches = None

    def get_matches(self, video):
        """
        patch: set guessit to single_value
        :param video:
        :return:
        """
        matches = set()

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and (fix_inconsistent_naming(self.title) in (
                    fix_inconsistent_naming(name) for name in [video.series] + video.alternative_series)):
                matches.add('series')
            # year
            if video.original_series and self.year is None or video.year and video.year == self.year:
                matches.add('year')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'episode', "single_value": True}))
        # movie
        elif isinstance(video, Movie):
            # title
            if video.title and (sanitize(self.title) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {'type': 'movie', "single_value": True}))

        self.matches = matches

        return matches


class PodnapisiProvider(_PodnapisiProvider, ProviderSubtitleArchiveMixin):
    languages = ({Language('por', 'BR'), Language('srp', script='Latn'), Language('srp', script='Cyrl')} |
                 {Language.fromalpha2(l) for l in language_converters['alpha2'].codes})
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))

    server_url = 'https://podnapisi.net/subtitles/'
    only_foreign = False
    also_foreign = False
    subtitle_class = PodnapisiSubtitle
    hearing_impaired_verifiable = True

    def __init__(self, only_foreign=False, also_foreign=False):
        self.only_foreign = only_foreign
        self.also_foreign = also_foreign

        if only_foreign:
            logger.info("Only searching for foreign/forced subtitles")

        super(PodnapisiProvider, self).__init__()

    def list_subtitles(self, video, languages):
        if video.is_special:
            logger.info("%s can't search for specials right now, skipping", self)
            return []

        season = episode = None
        if isinstance(video, Episode):
            titles = [fix_inconsistent_naming(title) for title in [video.series] + video.alternative_series]
            season = video.season
            episode = video.episode
        else:
            titles = [video.title] + video.alternative_titles

        for title in titles:
            subtitles = [s for l in languages for s in
                         self.query(l, title, video, season=season, episode=episode, year=video.year,
                                    only_foreign=self.only_foreign, also_foreign=self.also_foreign)]
            if subtitles:
                return subtitles

        return []

    def query(self, language, keyword, video, season=None, episode=None, year=None, only_foreign=False,
              also_foreign=False):
        search_language = str(language).lower()

        # sr-Cyrl specialcase
        if search_language == "sr-cyrl":
            search_language = "sr"

        # set parameters, see http://www.podnapisi.net/forum/viewtopic.php?f=62&t=26164#p212652
        params = {'sXML': 1, 'sL': search_language, 'sK': keyword}

        is_episode = False
        if season and episode:
            is_episode = True
            params['sTS'] = season
            params['sTE'] = episode

        if year:
            params['sY'] = year

        # loop over paginated results
        logger.info('Searching subtitles %r', params)
        subtitles = []
        pids = set()
        while True:
            # query the server
            content = None
            try:
                content = self.session.get(self.server_url + 'search/old', params=params, timeout=10).content
                xml = etree.fromstring(content)
            except etree.ParseError:
                logger.error("Wrong data returned: %r", content)
                break

            # exit if no results
            if not int(xml.find('pagination/results').text):
                logger.debug('No subtitles found')
                break

            # loop over subtitles
            for subtitle_xml in xml.findall('subtitle'):
                # read xml elements
                pid = subtitle_xml.find('pid').text
                # ignore duplicates, see http://www.podnapisi.net/forum/viewtopic.php?f=62&t=26164&start=10#p213321
                if pid in pids:
                    continue

                _language = Language.fromietf(subtitle_xml.find('language').text)
                hearing_impaired = 'n' in (subtitle_xml.find('flags').text or '')
                foreign = 'f' in (subtitle_xml.find('flags').text or '')
                if only_foreign and not foreign:
                    continue

                elif not only_foreign and not also_foreign and foreign:
                    continue

                elif also_foreign and foreign:
                    _language = Language.rebuild(_language, forced=True)

                if language != _language:
                    continue

                page_link = subtitle_xml.find('url').text
                releases = []
                if subtitle_xml.find('release').text:
                    for release in subtitle_xml.find('release').text.split():
                        releases.append(re.sub(r'\.+$', '', release))  # remove trailing dots
                title = subtitle_xml.find('title').text
                r_season = int(subtitle_xml.find('tvSeason').text)
                r_episode = int(subtitle_xml.find('tvEpisode').text)
                r_year = int(subtitle_xml.find('year').text)

                if is_episode:
                    subtitle = self.subtitle_class(_language, hearing_impaired, page_link, pid, releases, title,
                                                   season=r_season, episode=r_episode, year=r_year,
                                                   asked_for_release_group=video.release_group,
                                                   asked_for_episode=episode)
                else:
                    subtitle = self.subtitle_class(_language, hearing_impaired, page_link, pid, releases, title,
                                                   year=r_year, asked_for_release_group=video.release_group)


                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)
                pids.add(pid)

            # stop on last page
            if int(xml.find('pagination/current').text) >= int(xml.find('pagination/count').text):
                break

            # increment current page
            params['page'] = int(xml.find('pagination/current').text) + 1
            logger.debug('Getting page %d', params['page'])
            xml = None

        return subtitles

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(self.server_url + subtitle.pid + '/download', params={'container': 'zip'}, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            subtitle.content = self.get_subtitle_from_archive(subtitle, zf)
