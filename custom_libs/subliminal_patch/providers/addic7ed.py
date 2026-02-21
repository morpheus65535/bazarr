# coding=utf-8
import logging
import re
import datetime
import subliminal
import time

from random import randint
from urllib.parse import quote_plus

import babelfish
from dogpile.cache.api import NO_VALUE
from requests import Session
from requests.exceptions import RequestException
from subliminal.cache import region
from subliminal.video import Episode, Movie
from subliminal.exceptions import DownloadLimitExceeded, AuthenticationError, ConfigurationError
from subliminal.providers.addic7ed import Addic7edProvider as _Addic7edProvider, \
    Addic7edSubtitle as _Addic7edSubtitle, ParserBeautifulSoup
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import reinitialize_on_error
from subliminal_patch.utils import sanitize
from subliminal_patch.exceptions import TooManyRequests
from subliminal_patch.pitcher import pitchers, load_verification, store_verification
from subzero.language import Language

logger = logging.getLogger(__name__)

show_cells_re = re.compile(b'<td class="(?:version|vr)">.*?</td>', re.DOTALL)

#: Series header parsing regex
series_year_re = re.compile(r'^(?P<series>[ \w\'.:(),*&!?-]+?)(?: \((?P<year>\d{4})\))?$')

SHOW_EXPIRATION_TIME = datetime.timedelta(weeks=1).total_seconds()
MOVIE_EXPIRATION_TIME = datetime.timedelta(weeks=1).total_seconds()


class Addic7edSubtitle(_Addic7edSubtitle):
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, page_link, series, season, episode, title, year, version,
                 download_link, uploader=None):
        super(Addic7edSubtitle, self).__init__(language, hearing_impaired, page_link, series, season, episode,
                                               title, year, version, download_link)
        # Guessit will fail if the input is None
        self.release_info = version.replace('+', ',') if version else ""
        self.uploader = uploader
        self.matches = set()

    def get_matches(self, video):
        self.matches = super(Addic7edSubtitle, self).get_matches(video)
        if not subliminal.score.episode_scores.get("addic7ed_boost"):
            return self.matches

        # if the release group matches, the source is most likely correct, as well
        if "release_group" in self.matches:
            self.matches.add("source")

        if {"series", "season", "episode", "year"}.issubset(self.matches) and "source" in self.matches:
            self.matches.add("addic7ed_boost")
            logger.info("Boosting Addic7ed subtitle by %s" % subliminal.score.episode_scores.get("addic7ed_boost"))
        return self.matches

    def __repr__(self):
        return '<%s %r [%s]>' % (
            self.__class__.__name__, u"http://www.addic7ed.com/%s" % self.download_link, self.language)


class Addic7edProvider(_Addic7edProvider):
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'aze', 'ben', 'bos', 'bul', 'cat', 'ces', 'dan', 'deu', 'ell', 'eng', 'eus', 'fas', 'fin', 'fra', 'glg',
        'heb', 'hrv', 'hun', 'hye', 'ind', 'ita', 'jpn', 'kor', 'mkd', 'msa', 'nld', 'nor', 'pol', 'por', 'ron', 'rus',
        'slk', 'slv', 'spa', 'sqi', 'srp', 'swe', 'tha', 'tur', 'ukr', 'vie', 'zho'
    ]} | {Language.fromietf(l) for l in ["sr-Latn", "sr-Cyrl"]}
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))

    video_types = (Episode, Movie)
    vip = False
    USE_ADDICTED_RANDOM_AGENTS = False
    hearing_impaired_verifiable = True
    subtitle_class = Addic7edSubtitle
    server_url = 'https://www.addic7ed.com/'

    sanitize_characters = {'-', ':', '(', ')', '.', '/'}
    last_show_ids_fetch_key = "addic7ed_last_id_fetch"

    def __init__(self, username=None, password=None, cookies=None, user_agent=None, use_random_agents=False,
                 is_vip=False):
        super(Addic7edProvider, self).__init__(username=username, password=password, cookies=cookies,
                                               user_agent=user_agent)
        self.USE_ADDICTED_RANDOM_AGENTS = use_random_agents
        self.vip = is_vip

        if not all((username, password)) and not cookies:
            raise ConfigurationError('Username and password or cookies must be specified')

    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % subliminal.__short_version__

        from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
        logger.debug("Addic7ed: using random user agents")
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]
        self.session.headers['Referer'] = self.server_url

        if self.user_agent:
            self.session.headers['User-Agent'] = self.user_agent
        if self.cookies:
            cookies_string = self.cookies.split(";")
            from requests.cookies import RequestsCookieJar
            self.session.cookies = RequestsCookieJar()
            for c in cookies_string:
                k, v = c.split("=")
                self.session.cookies.set(k,v)

            rr = self.session.get(self.server_url + 'panel.php', allow_redirects=False, timeout=10,
                                  headers={"Referer": self.server_url})
            if rr.status_code == 302:
                logger.info('Addic7ed: Login expired')
                raise AuthenticationError("cookies not valid anymore")

            store_verification("addic7ed", self.session)
            logger.debug('Addic7ed: Logged in')
            self.logged_in = True
            time.sleep(2)
            return True

        # login
        if self.username and self.password:
            def check_verification(cache_region):
                rr = self.session.get(self.server_url + 'panel.php', allow_redirects=False, timeout=10,
                                      headers={"Referer": self.server_url})
                if rr.status_code == 302:
                    logger.info('Addic7ed: Login expired')
                    cache_region.delete("addic7ed_data")
                else:
                    logger.info('Addic7ed: Re-using old login')
                    self.logged_in = True
                    return True

            if load_verification("addic7ed", self.session, callback=check_verification):
                return

            logger.info('Addic7ed: Logging in')
            data = {'username': self.username, 'password': self.password, 'Submit': 'Log in', 'url': '',
                    'remember': 'true'}

            tries = 0
            while tries <= 3:
                tries += 1
                r = self.session.get(self.server_url + 'login.php', timeout=10, headers={"Referer": self.server_url})
                if "g-recaptcha" in r.text or "grecaptcha" in r.text:
                    logger.info('Addic7ed: Solving captcha. This might take a couple of minutes, but should only '
                                'happen once every so often')

                    for g, s in (("g-recaptcha-response", r'g-recaptcha.+?data-sitekey=\"(.+?)\"'),
                                 ("recaptcha_response", r'grecaptcha.execute\(\'(.+?)\',')):
                        site_key = re.search(s, r.text).group(1)
                        if site_key:
                            break
                    if not site_key:
                        logger.error("Addic7ed: Captcha site-key not found!")
                        return

                    pitcher = pitchers.get_pitcher()("Addic7ed", self.server_url + 'login.php', site_key,
                                                     user_agent=self.session.headers["User-Agent"],
                                                     cookies=self.session.cookies.get_dict(),
                                                     is_invisible=True)

                    result = pitcher.throw()
                    if not result:
                        if tries >= 3:
                            raise Exception("Addic7ed: Couldn't solve captcha!")
                        logger.info("Addic7ed: Couldn't solve captcha! Retrying")
                        time.sleep(4)
                        continue

                    data[g] = result

                time.sleep(1)
                r = self.session.post(self.server_url + 'dologin.php', data, allow_redirects=False, timeout=10,
                                      headers={"Referer": self.server_url + "login.php"})

                if "relax, slow down" in r.text:
                    raise TooManyRequests(self.username)

                if "Wrong password" in r.text or "doesn't exist" in r.text:
                    raise AuthenticationError(self.username)

                if r.status_code != 302:
                    if tries >= 3:
                        logger.error("Addic7ed: Something went wrong when logging in")
                        raise AuthenticationError(self.username)
                    logger.info("Addic7ed: Something went wrong when logging in; retrying")
                    time.sleep(4)
                    continue
                break

            store_verification("addic7ed", self.session)

            logger.debug('Addic7ed: Logged in')
            self.logged_in = True

            time.sleep(2)

    def terminate(self):
        self.session.close()

    def get_show_id(self, series, year=None, country_code=None, ignore_cache=False):
        """Get the best matching show id for `series`, `year` and `country_code`.

        First search in the result of :meth:`_get_show_ids` and fallback on a search with :meth:`_search_show_id`.

        :param str series: series of the episode.
        :param year: year of the series, if any.
        :type year: int
        :param country_code: country code of the series, if any.
        :type country_code: str
        :return: the show id, if found.
        :rtype: int
        """
        show_id = None
        ids_to_look_for = {sanitize(series).lower(), sanitize(series.replace(".", "")).lower(),
                           sanitize(series.replace("&", "and")).lower(), sanitize(series.replace("and", "&")).lower()}
        show_ids = self._get_show_ids()
        if ignore_cache or not show_ids:
            show_ids = self._get_show_ids.refresh(self)

        logger.debug("Trying show ids: %s", ids_to_look_for)
        for series_sanitized in ids_to_look_for:
            # attempt with country
            if not show_id and country_code:
                logger.debug('Getting show id with country')
                show_id = show_ids.get('%s %s' % (series_sanitized, country_code.lower()))

            # attempt with year
            if not show_id and year:
                logger.debug('Getting show id with year')
                show_id = show_ids.get('%s %d' % (series_sanitized, year))

            # attempt clean
            if not show_id:
                logger.debug('Getting show id')
                show_id = show_ids.get(series_sanitized)

                if not show_id:
                    now = datetime.datetime.now()
                    last_fetch = region.get(self.last_show_ids_fetch_key)

                    # re-fetch show ids once per day if any show ID not found
                    if not ignore_cache and last_fetch != NO_VALUE and last_fetch + datetime.timedelta(days=1) < now:
                        logger.info("Show id not found; re-fetching show ids")
                        return self.get_show_id(series, year=year, country_code=country_code, ignore_cache=True)
                    logger.debug("Not refreshing show ids, as the last fetch has been too recent")

            # search as last resort
            # broken right now
            # if not show_id:
            #     logger.warning('Series %s not found in show ids', series)
            #     show_id = self._search_show_id(series)

        return show_id

    @region.cache_on_arguments(expiration_time=MOVIE_EXPIRATION_TIME)
    def get_movie_id(self, movie, year=None):
        """Get the best matching movie id for `movie`, `year`.

        :param str movie: movie.
        :param year: year of the movie, if any.
        :type year: int
        :return: the movie id, if found.
        :rtype: int
        """
        movie_id = None

        # get the movie id
        logger.info('Getting movie id')

        r = self.session.get(self.server_url + 'search.php?search=' + quote_plus(movie), timeout=10)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['lxml', 'html.parser'])

        # populate the movie id
        movies_table = soup.find('table', {'class': 'tabel'})
        movies = movies_table.find_all('tr')
        for item in movies:
            link = item.find('a', href=True)
            if link:
                if link['href'].startswith('movie/'):
                    splitted_uri = link['href'].split('/')
                    if len(splitted_uri) == 2:
                        media_id = splitted_uri[1]
                    else:
                        continue
                    media_title = link.text
                    match = re.search(r'(.+)\s\((\d{4})\)$', media_title)
                    if match:
                        media_name = match.group(1)
                        media_year = match.group(2)
                        if sanitize(media_name.lower()) == sanitize(movie.lower()) and media_year == str(year):
                            movie_id = media_id

        soup.decompose()
        soup = None

        logger.debug(f'Found this movie id: {movie_id}')

        if not movie_id:
            logging.debug(f"Addic7ed: Cannot find this movie with guessed year {year}: {movie}")

        return movie_id

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _get_show_ids(self):
        """Get the ``dict`` of show ids per series by querying the `shows.php` page.
        :return: show id per series, lower case and without quotes.
        :rtype: dict

        # patch: add punctuation cleaning
        """
        # get the show page
        logger.info('Getting show ids')
        region.set(self.last_show_ids_fetch_key, datetime.datetime.now())

        r = self.session.get(self.server_url + 'shows.php', timeout=10)
        r.raise_for_status()

        # LXML parser seems to fail when parsing Addic7ed.com HTML markup.
        # Last known version to work properly is 3.6.4 (next version, 3.7.0, fails)
        # Assuming the site's markup is bad, and stripping it down to only contain what's needed.
        show_cells = [cell.decode("utf-8", "ignore") for cell in re.findall(show_cells_re, r.content)]
        if show_cells:
            soup = ParserBeautifulSoup(''.join(show_cells), ['lxml', 'html.parser'])
        else:
            # If RegEx fails, fall back to original r.content and use 'html.parser'
            soup = ParserBeautifulSoup(r.content, ['html.parser'])

        # populate the show ids
        show_ids = {}
        shows = soup.select('td > h3 > a[href^="/show/"]')
        for show in shows:
            show_clean = sanitize(show.text, default_characters=self.sanitize_characters)
            try:
                show_id = int(show['href'][6:])
            except ValueError:
                continue

            show_ids[show_clean] = show_id
            match = series_year_re.match(show_clean)
            if match and match.group(2) and match.group(1) not in show_ids:
                # year found, also add it without year
                show_ids[match.group(1)] = show_id

        soup.decompose()
        soup = None

        logger.debug('Found %d show ids', len(show_ids))

        if not show_ids:
            raise Exception("Addic7ed: No show IDs found!")

        return show_ids

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _search_show_id(self, series, year=None):
        """Search the show id from the `series` and `year`.

        :param str series: series of the episode.
        :param year: year of the series, if any.
        :type year: int
        :return: the show id, if found.
        :rtype: int

        """
        # addic7ed doesn't support search with quotes
        series = series.replace('\'', ' ')

        # build the params
        series_year = '%s %d' % (series, year) if year is not None else series
        params = {'search': series_year, 'Submit': 'Search'}

        # make the search
        logger.info('Searching show ids with %r', params)

        # currently addic7ed searches via srch.php from the front page, then a re-search is needed which calls
        # search.php
        for endpoint in ("srch.php", "search.php",):
            headers = None
            if endpoint == "search.php":
                headers = {
                    "referer": self.server_url + "srch.php"
                }
            r = self.session.get(self.server_url + endpoint, params=params, timeout=10, headers=headers)
            r.raise_for_status()

            if r.text and "Sorry, your search" not in r.text:
                break

            time.sleep(4)

        if r.status_code == 304:
            raise TooManyRequests()

        soup = ParserBeautifulSoup(r.text, ['lxml', 'html.parser'])

        suggestion = None

        # get the suggestion
        try:
            suggestion = soup.select('span.titulo > a[href^="/show/"]')
            if not suggestion:
                logger.warning('Show id not found: no suggestion')
                return None
            if not sanitize(suggestion[0].i.text.replace('\'', ' '),
                            default_characters=self.sanitize_characters) == \
                    sanitize(series_year, default_characters=self.sanitize_characters):
                logger.warning('Show id not found: suggestion does not match')
                return None
            show_id = int(suggestion[0]['href'][6:])
            logger.debug('Found show id %d', show_id)

            return show_id
        finally:
            soup.decompose()
            soup = None

    def query(self, show_id, series, season, year=None, country=None):
        # patch: fix logging

        # get the page of the season of the show
        logger.info('Getting the page of show id %d, season %d', show_id, season)
        r = self.session.get(self.server_url + 'ajax_loadShow.php',
                             params={'show': show_id, 'season': season, 'langs': '|'},
                             timeout=10,
                             headers={
                                 "referer": "%sshow/%s" % (self.server_url, show_id),
                                 "X-Requested-With": "XMLHttpRequest"
                             }
                             )

        r.raise_for_status()

        if r.status_code == 304:
            raise TooManyRequests()

        if not r.text:
            # Provider wrongful return a status of 304 Not Modified with an empty content
            # raise_for_status won't raise exception for that status code
            logger.error('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.text, ['lxml', 'html.parser'])

        # loop over subtitle rows
        subtitles = []
        for row in soup.select('tr.epeven'):
            cells = row('td')

            # ignore incomplete subtitles
            status = cells[5].text
            if "%" in status:
                logger.debug('Ignoring subtitle with status %s', status)
                continue

            # read the item
            try:
                language = Language.fromaddic7ed(cells[3].text)
            except babelfish.exceptions.LanguageReverseError as error:
                logger.debug("Language error: %s, Ignoring subtitle", error)
                continue

            hearing_impaired = bool(cells[6].text)
            page_link = self.server_url + cells[2].a['href'][1:]
            season = int(cells[0].text)
            episode = int(cells[1].text)
            title = cells[2].text
            version = cells[4].text
            download_link = cells[9].a['href'][1:]

            # set subtitle language to hi if it's hearing_impaired
            if hearing_impaired:
                language = Language.rebuild(language, hi=True)

            subtitle = self.subtitle_class(language, hearing_impaired, page_link, series, season, episode, title,
                                           year,
                                           version, download_link)
            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        soup.decompose()
        soup = None

        return subtitles

    def query_movie(self, movie_id, title, year=None):
        # get the page of the movie
        logger.info('Getting the page of movie id %s', movie_id)
        r = self.session.get(self.server_url + 'movie/' + movie_id,
                             timeout=10,
                             headers={
                                 "referer": self.server_url,
                                 "X-Requested-With": "XMLHttpRequest"
                             }
                             )

        r.raise_for_status()

        if r.status_code == 304:
            raise TooManyRequests()

        if not r.text:
            # Provider wrongful return a status of 304 Not Modified with an empty content
            # raise_for_status won't raise exception for that status code
            logger.error('No data returned from provider')
            return []

        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitle rows
        tables = []
        subtitles = []
        for table in soup.find_all('table', {'align': 'center',
                                             'border': '0',
                                             'class': 'tabel95',
                                             'width': '100%'}):
            if table.find_all('td', {'class': 'NewsTitle'}):
                tables.append(table)
        for table in tables:
            row1 = table.contents[1]
            row2 = table.contents[4]
            row3 = table.contents[6]
            # other rows are useless

            # ignore incomplete subtitles
            status = row2.contents[6].text
            if "%" in status:
                logger.debug('Ignoring subtitle with status %s', status)
                continue

            # read the item
            try:
                language = Language.fromaddic7ed(row2.contents[4].text.strip('\n'))
            except babelfish.exceptions.LanguageReverseError as error:
                logger.debug("Language error: %s, Ignoring subtitle", error)
                continue

            hearing_impaired = bool(row3.contents[1].contents[1].attrs['src'].endswith('hi.jpg'))
            page_link = self.server_url + 'movie/' + movie_id

            # Seems like Addic7ed returns the first word in the language of the user (Version, Versión, etc)
            # As we can't match a regex, we will just strip the first word
            try:
                version = " ".join(str(row1.contents[1].contents[1]).split()[1:])
                version_matches = re.search(r"(.+),.+", version)
                version = version_matches.group(1) if version_matches else None
            except IndexError:
                version = None

            try:
                download_link = row2.contents[8].contents[3].attrs['href'][1:]
            except IndexError:
                download_link = row2.contents[8].contents[2].attrs['href'][1:]
            uploader = row1.contents[2].contents[8].text.strip()

            # set subtitle language to hi if it's hearing_impaired
            if hearing_impaired:
                language = Language.rebuild(language, hi=True)

            subtitle = self.subtitle_class(language, hearing_impaired, page_link, None, None, None, title, year,
                                           version, download_link, uploader)
            logger.debug('Found subtitle %r', subtitle)
            subtitles.append(subtitle)

        soup.decompose()
        soup = None

        return subtitles

    @reinitialize_on_error((RequestException,), attempts=1)
    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            # lookup show_id
            titles = [video.series] + video.alternative_series[:5]
            show_id = None
            for title in titles:
                show_id = self.get_show_id(title, video.year)
                if show_id is not None:
                    break

            # query for subtitles with the show_id
            if show_id is not None:
                subtitles = [s for s in self.query(show_id, title, video.season, video.year)
                             if s.language in languages and s.episode == video.episode]
                if subtitles:
                    return subtitles
            else:
                logger.error('No show id found for %r (%r)', video.series, {'year': video.year})
        else:
            titles = [video.title] + video.alternative_titles[:5]

            for title in titles:
                movie_id = self.get_movie_id(title, video.year)
                if movie_id is not None:
                    break

            # query for subtitles with the movie_id
            if movie_id is not None:
                subtitles = [s for s in self.query_movie(movie_id, title, video.year) if s.language in languages]
                if subtitles:
                    return subtitles
            else:
                logger.error('No movie id found for %r (%r)', video.title, {'year': video.year})

        return []

    @reinitialize_on_error((RequestException,), attempts=1)
    def download_subtitle(self, subtitle):
        last_dls = region.get("addic7ed_dls")
        now = datetime.datetime.now()
        one_day = datetime.timedelta(hours=24)

        def raise_limit():
            logger.info("Addic7ed: Downloads per day exceeded (%s)", cap)
            raise DownloadLimitExceeded("Addic7ed: Downloads per day exceeded (%s)" % cap)

        if type(last_dls) is not list:
            last_dls = []
        else:
            # filter all non-expired DLs
            last_dls = list(filter(lambda t: t + one_day > now, last_dls))
            region.set("addic7ed_dls", last_dls)

        cap = self.vip and 80 or 40
        amount = len(last_dls)

        if amount >= cap:
            raise_limit()

        # download the subtitle
        r = self.session.get(self.server_url + subtitle.download_link, headers={'Referer': subtitle.page_link},
                             timeout=10)
        r.raise_for_status()

        if r.status_code == 304:
            raise TooManyRequests()

        if not r.text:
            # Provider wrongful return a status of 304 Not Modified with an empty content
            # raise_for_status won't raise exception for that status code
            logger.error('Unable to download subtitle. No data returned from provider')
            return

        # detect download limit exceeded
        if r.headers['Content-Type'] == 'text/html':
            raise DownloadLimitExceeded

        subtitle.content = fix_line_ending(r.content)
        last_dls.append(datetime.datetime.now())
        region.set("addic7ed_dls", last_dls)
        logger.info("Addic7ed: Used %s/%s downloads", amount + 1, cap)

        if amount + 1 >= cap:
            raise_limit()
