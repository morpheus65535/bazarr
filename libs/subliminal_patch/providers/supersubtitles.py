# coding=utf-8
import io
import logging
import re
import os
import time

from babelfish import language_converters
from subzero.language import Language
from requests import Session
import urllib.parse
from random import randint

from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal.providers import ParserBeautifulSoup
from bs4.element import Tag, NavigableString
from subliminal.score import get_equivalent_release_groups
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Episode, Movie
from zipfile import ZipFile
from rarfile import RarFile, is_rarfile
from subliminal_patch.utils import sanitize, fix_inconsistent_naming
from guessit import guessit
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST


logger = logging.getLogger(__name__)

language_converters.register('supersubtitles = subliminal_patch.converters.supersubtitles:SuperSubtitlesConverter')


def fix_tv_naming(title):
    """Fix TV show titles with inconsistent naming using dictionary, but do not sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    return fix_inconsistent_naming(title, {"Marvel's WandaVision": "WandaVision",
                                           "Marvel's Daredevil": "Daredevil",
                                           "Marvel's Luke Cage": "Luke Cage",
                                           "Marvel's Iron Fist": "Iron Fist",
                                           "Marvel's Jessica Jones": "Jessica Jones",
                                           "DC's Legends of Tomorrow": "Legends of Tomorrow",
                                           "Star Trek: The Next Generation": "Star Trek TNG",
                                           }, True)


def fix_movie_naming(title):
    return fix_inconsistent_naming(title, {
                                           }, True)


class SuperSubtitlesSubtitle(Subtitle):
    """SuperSubtitles Subtitle."""
    provider_name = 'supersubtitles'

    def __str__(self):
        subtit = "Subtitle id: " + str(self.subtitle_id) \
                 + " Series: " + self.series \
                 + " Season: " + str(self.season) \
                 + " Episode: " + str(self.episode) \
                 + " Version: " + str(self.version) \
                 + " Releases: " + str(self.releases) \
                 + " DownloadLink: " + str(self.page_link) \
                 + " Matches: " + str(self.matches)
        if self.year:
            subtit = subtit + " Year: " + str(self.year)
        return subtit.encode('utf-8')

    def __init__(self, language, page_link, subtitle_id, series, season, episode, version,
                 releases, year, imdb_id, uploader, asked_for_episode=None, asked_for_release_group=None):
        super(SuperSubtitlesSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.series = series
        self.season = season
        self.episode = episode
        self.version = version
        self.releases = releases
        self.year = year
        self.uploader = uploader
        if year:
            self.year = int(year)

        self.release_info = u", ".join(releases)
        self.page_link = page_link
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
        self.imdb_id = imdb_id
        self.is_pack = True
        self.matches = None

    def numeric_id(self):
        return self.subtitle_id

    def __repr__(self):
        ep_addon = (" S%02dE%02d" % (self.season, self.episode)) if self.episode else ""
        return '<%s %r [%s]>' % (
            self.__class__.__name__, u"%s%s%s [%s]" % (self.series, " (%s)" % self.year if self.year else "", ep_addon,
                                                       self.release_info), self.language)

    @property
    def id(self):
        return str(self.subtitle_id)

    def get_matches(self, video):
        matches = guess_matches(video, guessit(self.release_info))

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.series) == sanitize(video.series):
                matches.add('series')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            # imdb_id
            if video.series_imdb_id and self.imdb_id and str(self.imdb_id) == str(video.series_imdb_id):
                matches.add('series_imdb_id')
                matches.add('series')
                matches.add('year')
            # year
            if ('series' in matches and video.original_series and self.year is None or
                    video.year and video.year == self.year):
                matches.add('year')
        # movie
        elif isinstance(video, Movie):
            # title
            if video.title and (sanitize(self.series) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')
            # imdb_id
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')
                matches.add('title')
                matches.add('year')
            # year
            if video.year and self.year == video.year:
                matches.add('year')

        # release_group
        if (video.release_group and self.version and
                any(r in sanitize_release_group(self.version)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        # resolution
        if video.resolution and self.version and video.resolution in self.version.lower():
            matches.add('resolution')
        # source
        if video.source and self.version and video.source.lower() in self.version.lower():
            matches.add('source')

        self.matches = matches
        return matches


class SuperSubtitlesProvider(Provider, ProviderSubtitleArchiveMixin):
    """SuperSubtitles Provider."""
    languages = {Language('hun', 'HU')} | {Language(lang) for lang in [
        'hun', 'eng'
    ]}
    video_types = (Episode, Movie)
    # https://www.feliratok.info/?search=&soriSorszam=&nyelv=&sorozatnev=The+Flash+%282014%29&sid=3212&complexsearch=true&knyelv=0&evad=4&epizod1=1&cimke=0&minoseg=0&rlsr=0&tab=all
    server_url = 'https://www.feliratok.info/'
    hearing_impaired_verifiable = False
    multi_result_throttle = 2  # seconds

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers = {'User-Agent': AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]}

    def terminate(self):
        self.session.close()

    @staticmethod
    def get_language(text):
        if text == 'Magyar':
            return Language.fromsupersubtitles('hu')
        if text == 'Angol':
            return Language.fromsupersubtitles('en')
        return None

    def find_imdb_id(self, sub_id):
        """

        """

        url = self.server_url + "index.php?tipus=adatlap&azon=a_" + sub_id
        # url = https://www.feliratok.info/index.php?tipus=adatlap&azon=a_1518600916
        logger.info('Get IMDB id from URL %s', url)
        r = self.session.get(url, timeout=10).content

        soup = ParserBeautifulSoup(r, ['lxml'])
        links = soup.find_all("a")

        for value in links:
            if "imdb.com" in str(value):
                # <a alt="iMDB" href="http://www.imdb.com/title/tt2357547/" target="_blank"><img alt="iMDB"
                # src="img/adatlap/imdb.png"/></a>
                imdb_id = re.search(r'(?<=www\.imdb\.com/title/).*(?=/")', str(value))
                imdb_id = imdb_id.group() if imdb_id else ''
                return imdb_id

        return None

    def find_id(self, series, year, original_title):
        """
        We need to find the id of the series at the following url:
        https://www.feliratok.info/index.php?term=SERIESNAME&nyelv=0&action=autoname
        Where SERIESNAME is a searchable string.
        The result will be something like this:
        [{"name":"DC\u2019s Legends of Tomorrow (2016)","ID":"3725"},{"name":"Miles from Tomorrowland (2015)",
        "ID":"3789"},{"name":"No Tomorrow (2016)","ID":"4179"}]

        """

        # Search for exact name
        url = self.server_url + "index.php?term=" + series + "&nyelv=0&action=autoname"
        # url = self.server_url + "index.php?term=" + "fla"+ "&nyelv=0&action=autoname"
        logger.info('Get series id from URL %s', url)
        r = self.session.get(url, timeout=10)

        # r is something like this:
        # [{"name":"DC\u2019s Legends of Tomorrow (2016)","ID":"3725"},{"name":"Miles from Tomorrowland (2015)",
        # "ID":"3789"},{"name":"No Tomorrow (2016)","ID":"4179"}]

        results = r.json()

        # check all of the results:
        for result in results:
            try:
                # "name":"Miles from Tomorrowland (2015)","ID":"3789"
                result_year = re.search(r"(?<=\()\d\d\d\d(?=\))", result['name'])
                result_year = result_year.group() if result_year else ''
            except IndexError:
                result_year = ""

            try:
                # "name":"Miles from Tomorrowland (2015)","ID":"3789"
                result_title = re.search(r".*(?=\(\d\d\d\d\))", result['name'])
                result_title = result_title.group() if result_title else ''
                result_id = result['ID']
            except IndexError:
                continue

            result_title = fix_tv_naming(result_title).strip().replace("�", "").replace("& ", "").replace(" ", ".")
            if not result_title:
                continue

            guessable = result_title.strip() + ".s01e01." + result_year
            guess = guessit(guessable, {'type': "episode"})

            if sanitize(original_title.replace('& ', '')) == sanitize(guess['title']) and year and guess['year'] and \
                    year == guess['year']:
                # Return the founded id
                return result_id
            elif sanitize(original_title.replace('& ', '')) == sanitize(guess['title']) and not year:
                # Return the founded id
                return result_id

        return None

    def query(self, series, languages, video=None):
        year = video.year
        subtitle = None
        if isinstance(video, Episode):
            series = video.series
            season = video.season
            episode = video.episode
            # seriesa = series.replace(' ', '+')

            # Get ID of series with original name
            series_id = self.find_id(series, year, series)
            if not series_id:
                # If not founded try without ' char
                modified_series = urllib.parse.quote_plus(series.replace('\'', ''))
                series_id = self.find_id(modified_series, year, series)
                if not series_id and modified_series:
                    # If still not founded try with the longest word is series title
                    modified_series = modified_series.split('+')
                    modified_series = max(modified_series, key=len)
                    series_id = self.find_id(modified_series, year, series)

                    if not series_id:
                        return None

            # https://www.feliratok.info/index.php?search=&soriSorszam=&nyelv=&sorozatnev=&sid=2075&complexsearch=true&
            # knyelv=0&evad=6&epizod1=16&cimke=0&minoseg=0&rlsr=0&tab=all
            url = self.server_url + "index.php?search=&soriSorszam=&nyelv=&sorozatnev=&sid=" + \
                str(series_id) + "&complexsearch=true&knyelv=0&evad=" + str(season) + "&epizod1=" + \
                str(episode) + "&cimke=0&minoseg=0&rlsr=0&tab=all"
            subtitle = self.process_subs(languages, video, url)

            if not subtitle:
                # No Subtitle found. Maybe already archived to season pack
                url = self.server_url + "index.php?search=&soriSorszam=&nyelv=&sorozatnev=&sid=" + \
                      str(series_id) + "&complexsearch=true&knyelv=0&evad=" + \
                      str(season) + "&epizod1=&evadpakk=on&cimke=0&minoseg=0&rlsr=0&tab=all"
                subtitle = self.process_subs(languages, video, url)

        if isinstance(video, Movie):
            title = urllib.parse.quote_plus(series)

            # https://www.feliratok.info/index.php?search=The+Hitman%27s+BodyGuard&soriSorszam=&nyelv=&tab=film
            url = self.server_url + "index.php?search=" + title + "&soriSorszam=&nyelv=&tab=film"
            subtitle = self.process_subs(languages, video, url)

        return subtitle

    def process_subs(self, languages, video, url):

        subtitles = []

        logger.info('URL for subtitles %s', url)
        r = self.session.get(url, timeout=10).content

        soup = ParserBeautifulSoup(r, ['lxml'])
        tables = soup.find_all("table")
        tables = tables[0].find_all("tr")
        i = 0
        series_imdb_id = None
        for table in tables:
            if "vilagit" in str(table) and i > 1:
                asked_for_episode = None
                sub_season = None
                sub_episode = None
                sub_english = table.findAll("div", {"class": "eredeti"})
                sub_english_name = None
                if isinstance(video, Episode):
                    asked_for_episode = video.episode
                    if "Season" not in str(sub_english):
                        # [<div class="eredeti">Gossip Girl (Season 3) (DVDRip-REWARD)</div>]
                        sub_english_name = re.search(r'(?<=<div class="eredeti">).*?(?= -)',
                                                     str(sub_english))
                        sub_english_name = sub_english_name.group() if sub_english_name else ''

                        sub_season = re.search(r"(?<=- ).*?(?= - )", str(sub_english))
                        sub_season = sub_season.group() if sub_season else ''
                        sub_season = int((sub_season.split('x')[0]).strip())

                        sub_episode = re.search(r"(?<=- ).*?(?= - )", str(sub_english))
                        sub_episode = sub_episode.group() if sub_episode else ''
                        sub_episode = int((sub_episode.split('x')[1]).strip())

                    else:
                        # [<div class="eredeti">DC's Legends of Tomorrow - 3x11 - Here I Go Again (HDTV-AFG, HDTV-RMX,
                        # 720p-SVA, 720p-PSA </div>]
                        sub_english_name = \
                            re.search(r'(?<=<div class="eredeti">).*?(?=\(Season)', str(sub_english))
                        sub_english_name = sub_english_name.group() if sub_english_name else ''
                        sub_season = re.search(r"(?<=Season )\d+(?=\))", str(sub_english))
                        sub_season = int(sub_season.group()) if sub_season else None
                        sub_episode = int(video.episode)
                if isinstance(video, Movie):
                    sub_english_name = re.search(r'(?<=<div class="eredeti">).*?(?=</div>)', str(sub_english))
                    sub_english_name = sub_english_name.group() if sub_english_name else ''
                    sub_english_name = sub_english_name.split(' (')[0]

                sub_english_name = sub_english_name.replace('&amp;', '&')
                sub_version = 'n/a'
                if len(str(sub_english).split('(')) > 1:
                    sub_version = (str(sub_english).split('(')[len(str(sub_english).split('(')) - 1]).split(')')[0]
                # <small>Angol</small>
                lang = table.find("small")
                sub_language = re.search(r"(?<=<small>).*(?=</small>)", str(lang))
                sub_language = sub_language.group() if sub_language else ''
                sub_language = self.get_language(sub_language)

                # <a href="/index.php?action=letolt&amp;fnev=DCs Legends of Tomorrow - 03x11 - Here I Go Again.SVA.
                # English.C.orig.Addic7ed.com.srt&amp;felirat=1519162191">
                link = str(table.findAll("a")[len(table.findAll("a")) - 1]).replace("amp;", "")
                sub_downloadlink = re.search(r'(?<=href="/).*(?=">)', link)
                sub_downloadlink = sub_downloadlink.group() if sub_downloadlink else ''
                sub_downloadlink = self.server_url + sub_downloadlink

                sub_id = re.search(r"(?<=felirat=).*(?=\">)", link)
                sub_id = sub_id.group() if sub_id else ''
                sub_year = video.year
                sub_releases = [s.strip() for s in sub_version.split(',')]

                uploader = ''
                for item in table.contents[7].contents:
                    if isinstance(item, Tag):
                        uploader = item.text.lstrip('\r\n\t\t\t\t\t').rstrip('\r\n\t\t\t\t')
                    elif isinstance(item, NavigableString):
                        uploader = item.lstrip('\r\n\t\t\t\t\t').rstrip('\r\n\t\t\t\t')

                # For episodes we open the series page so all subtitles imdb_id must be the same. no need to check all
                if isinstance(video, Episode) and series_imdb_id is not None:
                    sub_imdb_id = series_imdb_id
                else:
                    sub_imdb_id = self.find_imdb_id(sub_id)
                    series_imdb_id = sub_imdb_id

                subtitle = SuperSubtitlesSubtitle(sub_language, sub_downloadlink, sub_id, sub_english_name.strip(),
                                                  sub_season, sub_episode, sub_version, sub_releases, sub_year,
                                                  sub_imdb_id, uploader, asked_for_episode,
                                                  asked_for_release_group=video.release_group)
                if subtitle.language in languages:
                    subtitles.append(subtitle)
            i = i + 1
        return subtitles

    def list_subtitles(self, video, languages):
        titles = []
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
        elif isinstance(video, Movie):
            titles = [video.title] + video.alternative_titles

        subtitles = []

        for title in titles:
            subs = self.query(title, languages, video=video)
            if subs:
                for item in subs:
                    if isinstance(video, Episode):
                        fixed_title = fix_tv_naming(item.series)
                    else:
                        fixed_title = fix_movie_naming(item.series)
                    if fixed_title in titles:
                        subtitles.append(item)

            time.sleep(self.multi_result_throttle)
            return subtitles

    def download_subtitle(self, subtitle):

        # download as a zip
        logger.info('Downloading subtitle %r', subtitle.subtitle_id)
        r = self.session.get(subtitle.page_link, timeout=10)
        r.raise_for_status()

        if ".rar" in subtitle.page_link:
            logger.debug('Archive identified as rar')
            archive_stream = io.BytesIO(r.content)
            archive = RarFile(archive_stream)
            subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
        elif ".zip" in subtitle.page_link:
            logger.debug('Archive identified as zip')
            archive_stream = io.BytesIO(r.content)
            archive = ZipFile(archive_stream)
            subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
        else:
            subtitle.content = fix_line_ending(r.content)
