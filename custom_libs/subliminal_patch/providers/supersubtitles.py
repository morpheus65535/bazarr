# coding=utf-8
import logging
from random import randint
import re
import time
import urllib.parse

from babelfish import language_converters
from bs4.element import NavigableString
from bs4.element import Tag
from guessit import guessit
from requests import Session
from requests.exceptions import JSONDecodeError
from subliminal.providers import ParserBeautifulSoup
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize
from subliminal.utils import sanitize_release_group
from subliminal.video import Episode
from subliminal.video import Movie
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.utils import fix_inconsistent_naming
from subliminal_patch.utils import sanitize
from subzero.language import Language

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
from .utils import get_archive_from_bytes
from .utils import get_subtitle_from_archive
from .utils import update_matches

logger = logging.getLogger(__name__)

language_converters.register('supersubtitles = subliminal_patch.converters.supersubtitles:SuperSubtitlesConverter')


def fix_tv_naming(title):
    """Fix TV show titles with inconsistent naming using dictionary, but do not sanitize them.

    :param str title: original title.
    :return: new title.
    :rtype: str

    """
    return fix_inconsistent_naming(title, {"DC's Legends of Tomorrow": "Legends of Tomorrow",
                                           "Star Trek: The Next Generation": "Star Trek TNG",
                                           "Loki (aka. Marvel\'s Loki)": "Loki",
                                           "Marvel's": "",
                                           }, True)


def fix_movie_naming(title):
    return fix_inconsistent_naming(title, {
                                           }, True)


class SuperSubtitlesSubtitle(Subtitle):
    """SuperSubtitles Subtitle."""
    provider_name = 'supersubtitles'

    def __init__(self, language, page_link, subtitle_id, series, season, episode, version,
                 releases, year, imdb_id, uploader, asked_for_episode=None, asked_for_release_group=None):
        super(SuperSubtitlesSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.series = series
        self.season = season
        self.episode = episode
        self.version = version
        self.releases = releases or []
        self.year = year
        self.uploader = uploader
        if year:
            self.year = int(year)

        self.release_info = "\n".join([self.__get_name(), *self.releases])
        self.page_link = page_link
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
        self.imdb_id = imdb_id
        self.is_pack = True
        self.matches = set()

    def numeric_id(self):
        return self.subtitle_id

    @property
    def id(self):
        return str(self.subtitle_id)

    def __get_name(self):
        ep_addon = f"S{self.season:02}E{self.episode:02}" if self.episode else ""
        year_str = f" ({self.year})"
        return f"{self.series}{year_str or ''} {ep_addon}".strip()

    def get_matches(self, video):
        matches = set()
        update_matches(matches, video, self.release_info)

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.series) == sanitize(video.series):
                matches.add('series')
            # imdb_id
            if video.series_imdb_id and self.imdb_id and str(self.imdb_id) == str(video.series_imdb_id):
                matches.add('series_imdb_id')
                matches.add('series')
                matches.add('year')
            # year
            if 'year' not in matches and 'series' in matches and video.original_series and self.year is None:
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
        if video.release_group and self.releases:
            video_release_groups = get_equivalent_release_groups(sanitize_release_group(video.release_group))
            for release in self.releases:

                if any(r in sanitize_release_group(release) for r in video_release_groups):
                    matches.add('release_group')

                    if video.resolution and video.resolution in release.lower():
                        matches.add('resolution')

                    if video.source and video.source in release.lower():
                        matches.add('source')

                # We don't have to continue in case it is a perfect match
                if all(m in matches for m in ['release_group', 'resolution', 'source']):
                    break

        self.matches = matches
        return matches


class SuperSubtitlesProvider(Provider, ProviderSubtitleArchiveMixin):
    """SuperSubtitles Provider."""
    languages = {Language('hun', 'HU')} | {Language(lang) for lang in [
        'hun', 'eng'
    ]}
    languages.update(set(Language.rebuild(language, forced=True) for language in languages))
    video_types = (Episode, Movie)
    # https://www.feliratok.eu/?search=&soriSorszam=&nyelv=&sorozatnev=The+Flash+%282014%29&sid=3212&complexsearch=true&knyelv=0&evad=4&epizod1=1&cimke=0&minoseg=0&rlsr=0&tab=all
    server_url = 'https://www.feliratok.eu/'
    hearing_impaired_verifiable = False
    multi_result_throttle = 2  # seconds

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            'User-Agent': AGENT_LIST[randint(0, len(AGENT_LIST) - 1)],
            'Referer': 'https://www.feliratok.eu/index.php'
        }

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
        # TODO: add memoization to this method logic

        url = self.server_url + "index.php?tipus=adatlap&azon=a_" + str(sub_id)
        # url = https://www.feliratok.eu/index.php?tipus=adatlap&azon=a_1518600916
        logger.info('Get IMDB id from URL %s', url)
        r = self.session.get(url, timeout=30).content

        soup = ParserBeautifulSoup(r, ['lxml'])
        links = soup.find_all("a")

        for value in links:
            if "imdb.com" in str(value):
                # <a alt="iMDB" href="http://www.imdb.com/title/tt2357547/" target="_blank"><img alt="iMDB"
                # src="img/adatlap/imdb.png"/></a>
                imdb_id = re.search(r'(?<=www\.imdb\.com/title/).*(?=/")', str(value))
                imdb_id = imdb_id.group() if imdb_id else ''
                logger.debug("IMDB ID found: %s", imdb_id)
                return imdb_id

        return None

    def find_id(self, series, year, original_title):
        """
        We need to find the id of the series at the following url:
        https://www.feliratok.eu/index.php?term=SERIESNAME&nyelv=0&action=autoname
        Where SERIESNAME is a searchable string.
        The result will be something like this:
        [{"name":"DC\u2019s Legends of Tomorrow (2016)","ID":"3725"},{"name":"Miles from Tomorrowland (2015)",
        "ID":"3789"},{"name":"No Tomorrow (2016)","ID":"4179"}]

        """

        # Search for exact name
        url = self.server_url + "index.php?term=" + series + "&nyelv=0&action=autoname"
        # url = self.server_url + "index.php?term=" + "fla"+ "&nyelv=0&action=autoname"
        logger.info('Get series id from URL %s', url)
        r = self.session.get(url, timeout=30)

        # r is something like this:
        # [{"name":"DC\u2019s Legends of Tomorrow (2016)","ID":"3725"},{"name":"Miles from Tomorrowland (2015)",
        # "ID":"3789"},{"name":"No Tomorrow (2016)","ID":"4179"}]

        try:
            results = r.json()
        except JSONDecodeError:
            logger.error('Unable to parse returned JSON from URL %s', url)
            return None

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

            for title in (result_title, fix_tv_naming(result_title)):

                title = title.strip().replace("�", "").replace("& ", "").replace(" ", ".")
                if not title:
                    continue

                guessable = title.strip() + ".s01e01." + result_year
                guess = guessit(guessable, {'type': "episode"})

                sanitized_original_title = sanitize(original_title.replace('& ', ''))
                guess_title = sanitize(guess['title'])

                if sanitized_original_title == guess_title and year and guess['year'] and \
                        year == guess['year']:
                    # Return the founded id
                    return result_id
                elif sanitized_original_title == guess_title and not year:
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

            subtitle = self.retrieve_series_subtitles(series_id, season, episode, video, languages)

        if isinstance(video, Movie):
            title = urllib.parse.quote_plus(series)

            # https://www.feliratok.eu/index.php?search=The+Hitman%27s+BodyGuard&soriSorszam=&nyelv=&tab=film
            url = self.server_url + "index.php?search=" + title + "&soriSorszam=&nyelv=&tab=film"
            subtitle = self.process_subs(languages, video, url)

        return subtitle

    def retrieve_series_subtitles(self, series_id, season, episode, video, languages):
        """
        Retrieve subtitles for a given episode

        :param series_id: the ID of the series returned by @find_id.
        :param season: the season number
        :param episode: the episode number
        :param video: video details
        :param languages: languages to search for
        :return: list of subtitles for the given episode
        """
        if isinstance(video, Movie):
            return None

        subtitles = []

        logger.info('Getting the list of subtitles for %s', video)

        # First, try using every param that we got
        episode_subs, season_subs = self.get_subtitle_list(series_id, season, episode, video)

        if episode_subs:
            sub_list = episode_subs
        else:
            ''' 
            Sometimes the site is a bit buggy when you are searching for an episode sub that is only present in a
            season pack, so we have to make a separate call for that without supplying the episode number
            '''
            _, sub_list = self.get_subtitle_list(series_id, season, None, video)

        series_imdb_id = None

        # Convert the list of subtitles for the proper format
        for sub in sub_list.values():
            '''
            Since it is not possible to narrow down the languages in the request, we need to filter out the
            inappropriate elements
            '''
            if sub['language'] in languages:
                link = self.server_url + '/index.php?action=letolt&felirat=' + str(sub['id'])

                # For episodes we open the series page so all subtitles imdb_id must be the same
                if series_imdb_id is None:
                    series_imdb_id = self.find_imdb_id(sub['id'])

                # Let's create a SuperSubtitlesSubtitle instance from the data that we got and add it to the list
                subtitles.append(SuperSubtitlesSubtitle(sub['language'], link, sub['id'], sub['name'], sub['season'],
                                                        sub['episode'], ', '.join(sub['releases']), sub['releases'],
                                                        video.year, series_imdb_id, sub['uploader'], video.episode,
                                                        asked_for_release_group=video.release_group))

        return subtitles

    def get_subtitle_list(self, series_id, season, episode, video):
        """
        We can retrieve the list of subtitles for a given show via the following url:
        https://www.feliratok.eu/index.php?action=xbmc&sid=SERIES_ID&ev=SEASON&rtol=EPISODE
        SERIES_ID is the ID of the show returned by the @find_id method. It is a mandatory parameter.
        SEASON is the season number. Optional paramter.
        EPISODE is the episode number. Optional parameter (using this param can cause problems).

        NOTE: you gonna get back multiple records for the same subtitle, in case it is compatible with multiple releases
        """

        # Construct the url
        url = self.server_url + "index.php?action=xbmc&sid=" + str(series_id) + "&ev=" + str(season)

        # Use the 'rtol' param in case we have a valid episode number
        if episode:
            url += "&rtol=" + str(episode)

        try:
            results = self.session.get(url, timeout=30).json()
        except JSONDecodeError:
            # provider returned improper JSON
            results = None

        '''
        In order to work, the result should be a JSON like this:
        {
            "10": {
                "language":"Angol",
                "nev":"The Flash (Season 5) (1080p)",
                "baselink":"http://www.feliratok.eu/index.php",
                "fnev":"The.Flash.S05.HDTV.WEB.720p.1080p.ENG.zip",
                "felirat":"1560706755",
                "evad":"5",
                "ep":"-1",
                "feltolto":"J1GG4",
                "pontos_talalat":"111",
                "evadpakk":"1"
            }, ...
        }
        '''

        subtitle_list = {}
        season_pack_list = {}

        # Check the results. If a list or a Nonetype is returned, ignore it:
        if results and not isinstance(results, list):
            for result in results.values():
                '''
                Gonna get back multiple records for the same subtitle, in case it is compatible with multiple releases,
                so we have to group them manually
                '''
                sub_id = int(result['felirat'])

                # 'Nev' is something like this:
                #   Marvel's The Falcon and the Winter Soldier - 1x05 (WEB.2160p-KOGi)
                # or
                #   Loki (Season 1) (DSNP.WEB-DL.720p-TOMMY)
                search_name = re.search(r'^(.*)\s(?:-\s\d+x\d+|(\(Season\s\d+\)))?\s\((.*)\)$', result['nev'])

                name = search_name.group(1) if search_name else ''
                release = search_name.group(3) if search_name else ''

                # In case of 0 it is an episode sub, in other cases, it is a season pack
                target = subtitle_list if not int(result['evadpakk']) else season_pack_list

                # Check that this sub_id is not already in the list
                if sub_id not in target.keys():
                    target[sub_id] = {
                        'id': sub_id,
                        'name': name,
                        'language': self.get_language(result['language']),
                        'season': int(result['evad']),
                        'episode': result['ep'] if not result['evadpakk'] else int(video.episode),
                        'uploader': result['feltolto'],
                        'releases': [release],
                        'fname': result['fnev']
                    }
                else:
                    target[sub_id]['releases'].append(release)
        else:
            logger.debug("Invalid results: %s", results)

        return subtitle_list, season_pack_list

    def process_subs(self, languages, video, url):
        if isinstance(video, Episode):
            return None

        subtitles = []

        logger.info('URL for subtitles %s', url)
        r = self.session.get(url, timeout=30).content

        soup = ParserBeautifulSoup(r, ['lxml'])
        tables = soup.find_all("table")

        try:
            tables = tables[0].find_all("tr")
        except IndexError:
            logger.debug("No tables found for %s", url)
            return []

        i = 0

        for table in tables:
            if "vilagit" in str(table) and i > 1:
                asked_for_episode = None
                sub_season = None
                sub_episode = None
                sub_english = table.findAll("div", {"class": "eredeti"})
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

                # detect forced subtitles
                szinkronoshoz_sub = table.find("div", {"class": "magyar"})
                sub_forced = False
                if szinkronoshoz_sub:
                    sub_forced = 'szinkronoshoz' in szinkronoshoz_sub.text
                if sub_forced or 'forced' in sub_downloadlink:
                    sub_language = Language.rebuild(sub_language, forced=True)

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

                sub_imdb_id = self.find_imdb_id(sub_id)

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
                    # Check for the original and the fixed titles too
                    if any(x in (fixed_title.strip(), item.series) for x in titles):
                        subtitles.append(item)

            time.sleep(self.multi_result_throttle)
            return subtitles

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.page_link, timeout=30)
        r.raise_for_status()

        archive = get_archive_from_bytes(r.content)

        if archive is None:
            subtitle.content = r.content
            return

        subtitle.content = get_subtitle_from_archive(archive, episode=subtitle.episode or None)
