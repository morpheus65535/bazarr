# -*- coding: utf-8 -*-
import logging
import io
import os
import re
import zipfile
from time import sleep
from urllib.parse import quote
from urllib.parse import parse_qs
from requests.exceptions import HTTPError
import rarfile
from bs4 import FeatureNotFound

from guessit import guessit
from requests.exceptions import RequestException
from subliminal.cache import region
from subliminal.exceptions import ConfigurationError, AuthenticationError, ServiceUnavailable, DownloadLimitExceeded
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import TooManyRequests, IPAddressBlocked, SearchLimitReached
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.providers import Provider, reinitialize_on_error
from subliminal_patch.score import get_scores, framerate_equal
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language
from dogpile.cache.api import NO_VALUE

logger = logging.getLogger(__name__)


class LegendasdivxSubtitle(Subtitle):
    """Legendasdivx Subtitle."""
    provider_name = 'legendasdivx'

    def __init__(self, language, video, data, skip_wrong_fps=True):
        super(LegendasdivxSubtitle, self).__init__(language)
        self.page_link = data['link']
        self.hits = data['hits']
        self.exact_match = data['exact_match']
        self.description = data['description']
        self.video = video
        self.sub_frame_rate = data['frame_rate']
        self.uploader = data['uploader']
        self.wrong_fps = False
        self.skip_wrong_fps = skip_wrong_fps
        self.release_info = self.description
        self.matches = set()

    @property
    def id(self):
        try:
            return parse_qs(self.page_link)["lid"][0]
        except (KeyError, IndexError):
            return f"legendasdivx_{self.video.imdb_id}_{self.release_info}_{self.uploader}"

    def get_matches(self, video):
        # if skip_wrong_fps = True no point to continue if they don't match
        subtitle_fps = None
        try:
            subtitle_fps = float(self.sub_frame_rate)
        except ValueError:
            pass

        # check fps match and skip based on configuration
        if video.fps and subtitle_fps and not framerate_equal(video.fps, subtitle_fps):
            self.wrong_fps = True

            if self.skip_wrong_fps:
                logger.debug("Legendasdivx :: Skipping subtitle due to FPS mismatch (expected: %s, got: %s)", video.fps,
                             self.sub_frame_rate)
                # not a single match :)
                return set()
            logger.debug("Legendasdivx :: Frame rate mismatch (expected: %s, got: %s, but continuing...)", video.fps,
                         self.sub_frame_rate)

        description = sanitize(self.description)

        video_filename = video.name
        video_filename = os.path.basename(video_filename)
        video_filename, _ = os.path.splitext(video_filename)
        video_filename = sanitize_release_group(video_filename)

        if sanitize(video_filename) in description:
            self.matches.update(['title'])
            # relying people won' use just S01E01 for the file name
            if isinstance(video, Episode):
                self.matches.update(['series'])
                self.matches.update(['season'])
                self.matches.update(['episode'])

        # can match both movies and series
        if video.year and '{:04d}'.format(video.year) in description:
            self.matches.update(['year'])

        type_ = "movie" if isinstance(video, Movie) else "episode"
        # match movie title (include alternative movie names)
        if type_ == "movie":
            if video.title:
                for movie_name in [video.title] + video.alternative_titles:
                    if sanitize(movie_name) in description:
                        self.matches.update(['title'])

        else:
            if video.title and sanitize(video.title) in description:
                self.matches.update(['title'])
            if video.series:
                for series_name in [video.series] + video.alternative_series:
                    if sanitize(series_name) in description:
                        self.matches.update(['series'])
            if video.season and 's{:02d}'.format(video.season) in description:
                self.matches.update(['season'])
            if video.episode and 'e{:02d}'.format(video.episode) in description:
                self.matches.update(['episode'])
            # All the search is already based on the series_imdb_id when present in the video and controlled via the
            # the legendasdivx backend it, so if there is a result, it matches, either inside of a pack or a specific
            # series and episode, so we can assume the season and episode matches.
            if video.series_imdb_id:
                self.matches.update(['series', 'series_imdb_id', 'season', 'episode'])

        # release_group
        if video.release_group and sanitize_release_group(video.release_group) in sanitize_release_group(description):
            self.matches.update(['release_group'])

        self.matches |= guess_matches(video, guessit(description, {"type": type_}))

        return self.matches


class LegendasdivxProvider(Provider):
    """Legendasdivx Provider."""
    languages = {Language('por', 'BR')} | {Language('por')}
    video_types = (Episode, Movie)
    SEARCH_THROTTLE = 8
    SAFE_SEARCH_LIMIT = 145  # real limit is 150, but we use 145 to keep a buffer and prevent IPAddressBlocked exception to be raised
    site = 'https://www.legendasdivx.pt'
    headers = {
        'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Origin': 'https://www.legendasdivx.pt',
        'Referer': 'https://www.legendasdivx.pt'
    }
    loginpage = site + '/forum/ucp.php?mode=login'
    searchurl = site + '/modules.php?name=Downloads&file=jz&d_op={d_op}&op={op}&query={query}&temporada={season}&episodio={episode}&imdb={imdbid}'
    download_link = site + '/modules.php{link}'

    def __init__(self, username, password, skip_wrong_fps=True):
        # make sure login credentials are configured.
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Legendasdivx.pt :: Username and password must be specified')
        self.username = username
        self.password = password
        self.skip_wrong_fps = skip_wrong_fps

    def initialize(self):
        logger.debug("Legendasdivx.pt :: Creating session for requests")
        self.session = RetryingCFSession()
        # re-use PHP Session if present
        prev_cookies = region.get("legendasdivx_cookies2")
        if prev_cookies != NO_VALUE:
            logger.debug("Legendasdivx.pt :: Re-using previous legendasdivx cookies: %s", prev_cookies)
            self.session.cookies.update(prev_cookies)
        # login if session has expired
        else:
            logger.debug("Legendasdivx.pt :: Session cookies not found!")
            self.session.headers.update(self.headers)
            self.login()

    def terminate(self):
        # session close
        self.session.close()

    def login(self):
        logger.debug('Legendasdivx.pt :: Logging in')
        try:
            # sleep for a 1 second before another request
            sleep(1)
            res = self.session.get(self.loginpage)
            res.raise_for_status()
            bsoup = ParserBeautifulSoup(res.content, ['lxml'])

            _allinputs = bsoup.findAll('input')
            data = {}
            # necessary to set 'sid' for POST request
            for field in _allinputs:
                data[field.get('name')] = field.get('value')

            # sleep for a 1 second before another request
            sleep(1)
            data['username'] = self.username
            data['password'] = self.password
            res = self.session.post(self.loginpage, data)
            res.raise_for_status()
            # make sure we're logged in
            logger.debug('Legendasdivx.pt :: Logged in successfully: PHPSESSID: %s',
                         self.session.cookies.get_dict()['PHPSESSID'])
            cj = self.session.cookies.copy()
            store_cks = ("PHPSESSID", "phpbb3_2z8zs_sid", "phpbb3_2z8zs_k", "phpbb3_2z8zs_u", "lang")
            for cn in iter(self.session.cookies.keys()):
                if cn not in store_cks:
                    del cj[cn]
            # store session cookies on cache
            logger.debug("Legendasdivx.pt :: Storing legendasdivx session cookies: %r", cj)
            region.set("legendasdivx_cookies2", cj)

        except KeyError:
            logger.error("Legendasdivx.pt :: Couldn't get session ID, check your credentials")
            raise AuthenticationError("Legendasdivx.pt :: Couldn't get session ID, check your credentials")
        except HTTPError as e:
            if "bloqueado" in res.text.lower():
                logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                raise IPAddressBlocked("LegendasDivx.pt :: Your IP is blocked on this server.")
            logger.error("Legendasdivx.pt :: HTTP Error %s", e)
            raise TooManyRequests("Legendasdivx.pt :: HTTP Error %s", e)
        except FeatureNotFound:
            logger.error("LegendasDivx.pt :: lxml Python module isn't installed. Make sure to install requirements.")
            raise ConfigurationError("LegendasDivx.pt :: lxml Python module isn't installed. Make sure to install "
                                     "requirements.")
        except Exception as e:
            logger.error("LegendasDivx.pt :: Uncaught error: %r", e)
            raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r", e)

    def _process_page(self, video, bsoup):

        subtitles = []

        _allsubs = bsoup.findAll("div", {"class": "sub_box"})

        for _subbox in _allsubs:

            hits = 0
            for th in _subbox.findAll("th"):
                if th.text == 'Hits:':
                    hits = int(th.find_next("td").text)
                if th.text == 'Idioma:':
                    lang = th.find_next("td").find("img").get('src')
                    if 'brazil' in lang.lower():
                        lang = Language.fromopensubtitles('pob')
                    elif 'portugal' in lang.lower():
                        lang = Language.fromopensubtitles('por')
                    else:
                        continue
                if th.text == "Frame Rate:":
                    frame_rate = th.find_next("td").text.strip()

            # get description for matches
            description = _subbox.find("td", {"class": "td_desc brd_up"}).get_text()

            # get subtitle link from footer
            sub_footer = _subbox.find("div", {"class": "sub_footer"})
            download = sub_footer.find("a", {"class": "sub_download"}) if sub_footer else None

            # sometimes 'a' tag is not found and returns None. Most likely HTML format error!
            try:
                download_link = self.download_link.format(link=download.get('href'))
                logger.debug("Legendasdivx.pt :: Found subtitle link on: %s ", download_link)
            except:
                logger.debug("Legendasdivx.pt :: Couldn't find download link. Trying next...")
                continue

            # get subtitle uploader
            sub_header = _subbox.find("div", {"class": "sub_header"})
            uploader = sub_header.find("a").text if sub_header else 'anonymous'

            exact_match = False
            if video.name.lower() in description.lower():
                exact_match = True

            data = {'link': download_link,
                    'exact_match': exact_match,
                    'hits': hits,
                    'uploader': uploader,
                    'frame_rate': frame_rate,
                    'description': description
                    }
            subtitles.append(
                LegendasdivxSubtitle(lang, video, data, skip_wrong_fps=self.skip_wrong_fps)
            )
        return subtitles

    @reinitialize_on_error((RequestException,), attempts=1)
    def query(self, video, languages):

        _searchurl = self.searchurl

        subtitles = []

        # Set the default search criteria
        d_op = 'search'
        op = '_jz00'

        lang_filter_key = 'form_cat'

        if isinstance(video, Movie):
            querytext = video.imdb_id if video.imdb_id else video.title
        if isinstance(video, Episode):
            # Overwrite the parameters to refine via imdb_id
            if video.series_imdb_id:
                querytext = '&faz=pesquisa_episodio'
                lang_filter_key = 'idioma'
                d_op = 'jz_00'
                op = ''
            else:
                querytext = '%22{}%22%20S{:02d}E{:02d}'.format(video.series, video.season, video.episode)
                querytext = quote(querytext.lower())

        # language query filter
        if not isinstance(languages, (tuple, list, set)):
            languages = [languages]

        for language in languages:
            logger.debug("Legendasdivx.pt :: searching for %s subtitles.", language)
            language_id = language.opensubtitles
            if 'por' in language_id:
                lang_filter = '&{}=28'.format(lang_filter_key)
            elif 'pob' in language_id:
                lang_filter = '&{}=29'.format(lang_filter_key)
            else:
                lang_filter = ''

            querytext = querytext + lang_filter if lang_filter else querytext

            search_url = _searchurl.format(
                    query=querytext,
                    season='' if isinstance(video, Movie) else video.season,
                    episode='' if isinstance(video, Movie) else video.episode,
                    imdbid='' if isinstance(video, Movie) else video.series_imdb_id.replace('tt', '') if video.series_imdb_id else None,
                    op=op,
                    d_op=d_op,
            )

            try:
                # sleep for a 1 second before another request
                sleep(1)
                searchLimitReached = False
                self.headers['Referer'] = self.site + '/index.php'
                self.session.headers.update(self.headers)
                res = self.session.get(search_url, allow_redirects=False)
                res.raise_for_status()
                if res.status_code == 200 and "<!--pesquisas:" in res.text:
                    searches_count_groups = re.search(r'<!--pesquisas: (\d*)-->', res.text)
                    if searches_count_groups:
                        try:
                            searches_count = int(searches_count_groups.group(1))
                        except TypeError:
                            pass
                        else:
                            if searches_count >= self.SAFE_SEARCH_LIMIT:
                                searchLimitReached = True
                if (res.status_code == 200 and "A legenda não foi encontrada" in res.text):
                    logger.warning('Legendasdivx.pt :: query %s return no results!', querytext)
                    # for series, if no results found, try again just with series and season (subtitle packs)
                    if isinstance(video, Episode):
                        logger.debug("Legendasdivx.pt :: trying again with just series and season on query.")
                        querytext = re.sub(r"(e|E)(\d{2})", "", querytext)
                        # sleep for a 1 second before another request
                        sleep(1)
                        res = self.session.get(search_url, allow_redirects=False)
                        res.raise_for_status()
                        if res.status_code == 200 and "<!--pesquisas:" in res.text:
                            searches_count_groups = re.search(r'<!--pesquisas: (\d*)-->', res.text)
                            if searches_count_groups:
                                try:
                                    searches_count = int(searches_count_groups.group(1))
                                except TypeError:
                                    pass
                                else:
                                    if searches_count >= self.SAFE_SEARCH_LIMIT:
                                        searchLimitReached = True
                        if (res.status_code == 200 and "A legenda não foi encontrada" in res.text):
                            logger.warning(
                                'Legendasdivx.pt :: query {0} return no results for language {1}(for series and season only).'.format(
                                    querytext, language_id))
                            continue
                if res.status_code == 302:  # got redirected to login page.
                    # seems that our session cookies are no longer valid... clean them from cache
                    region.delete("legendasdivx_cookies2")
                    logger.debug("Legendasdivx.pt :: Logging in again. Cookies have expired!")
                    # login and try again
                    self.login()
                    # sleep for a 1 second before another request
                    sleep(1)
                    res = self.session.get(search_url, allow_redirects=False)
                    res.raise_for_status()
                    if res.status_code == 200 and "<!--pesquisas:" in res.text:
                        searches_count_groups = re.search(r'<!--pesquisas: (\d*)-->', res.text)
                        if searches_count_groups:
                            try:
                                searches_count = int(searches_count_groups.group(1))
                            except TypeError:
                                pass
                            else:
                                if searches_count >= self.SAFE_SEARCH_LIMIT:
                                    searchLimitReached = True
            except HTTPError as e:
                if "bloqueado" in res.text.lower():
                    logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                    raise IPAddressBlocked("LegendasDivx.pt :: Your IP is blocked on this server.")
                logger.error("Legendasdivx.pt :: HTTP Error %s", e)
                raise TooManyRequests("Legendasdivx.pt :: HTTP Error %s", e)
            except Exception as e:
                logger.error("LegendasDivx.pt :: Uncaught error: %r", e)
                raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r", e)

            if searchLimitReached:
                raise SearchLimitReached(
                    "LegendasDivx.pt :: You've reached maximum number of search for the day.")

            bsoup = ParserBeautifulSoup(res.content, ['html.parser'])

            # search for more than 10 results (legendasdivx uses pagination)
            # don't throttle - maximum results = 6 * 10
            MAX_PAGES = 6

            # get number of pages bases on results found
            page_header = bsoup.find("div", {"class": "pager_bar"})
            results_found = re.search(r'\((.*?) encontradas\)', page_header.text).group(1) if page_header else 0
            logger.debug("Legendasdivx.pt :: Found %s subtitles", str(results_found))
            num_pages = (int(results_found) // 10) + 1
            num_pages = min(MAX_PAGES, num_pages)

            # process first page
            subtitles += self._process_page(video, bsoup)

            # more pages?
            if num_pages > 1:
                for num_page in range(2, num_pages + 1):
                    sleep(1) # another 1 sec before requesting...
                    _search_next = search_url + "&page={0}".format(str(num_page))
                    logger.debug("Legendasdivx.pt :: Moving on to next page: %s", _search_next)
                    # sleep for a 1 second before another request
                    sleep(1)
                    res = self.session.get(_search_next)
                    next_page = ParserBeautifulSoup(res.content, ['html.parser'])
                    subs = self._process_page(video, next_page)
                    subtitles.extend(subs)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    @reinitialize_on_error((RequestException,), attempts=1)
    def download_subtitle(self, subtitle):

        try:
            # sleep for a 1 second before another request
            sleep(1)
            res = self.session.get(subtitle.page_link)
            res.raise_for_status()
        except HTTPError as e:
            if "bloqueado" in res.text.lower():
                logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                raise IPAddressBlocked("LegendasDivx.pt :: Your IP is blocked on this server.")
            logger.error("Legendasdivx.pt :: HTTP Error %s", e)
            raise TooManyRequests("Legendasdivx.pt :: HTTP Error %s", e)
        except Exception as e:
            logger.error("LegendasDivx.pt :: Uncaught error: %r", e)
            raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r", e)

        # make sure we haven't maxed out our daily limit
        if (res.status_code == 200 and 'limite de downloads diário atingido' in res.text.lower()):
            logger.error("LegendasDivx.pt :: Daily download limit reached!")
            raise DownloadLimitExceeded("Legendasdivx.pt :: Daily download limit reached!")

        archive = self._get_archive(res.content)
        # extract the subtitle
        if archive:
            subtitle_content = self._get_subtitle_from_archive(archive, subtitle)
            if subtitle_content:
                subtitle.content = fix_line_ending(subtitle_content)
                subtitle.normalize()
                return subtitle
        return

    def _get_archive(self, content):
        # open the archive
        archive_stream = io.BytesIO(content)
        if rarfile.is_rarfile(archive_stream):
            logger.debug('Legendasdivx.pt :: Identified rar archive')
            archive = rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug('Legendasdivx.pt :: Identified zip archive')
            archive = zipfile.ZipFile(archive_stream)
        else:
            logger.error('Legendasdivx.pt :: Unsupported compressed format')
            return None
        return archive

    def _get_subtitle_from_archive(self, archive, subtitle):
        # some files have a non subtitle with .txt extension
        _tmp = list(SUBTITLE_EXTENSIONS)
        _tmp.remove('.txt')
        _subtitle_extensions = tuple(_tmp)
        _max_score = 0
        _scores = get_scores(subtitle.video)

        for name in archive.namelist():
            # discard hidden files
            if os.path.split(name)[-1].startswith('.'):
                continue

            # discard non-subtitle files
            if not name.lower().endswith(_subtitle_extensions):
                continue

            _guess = guessit(name)
            if isinstance(subtitle.video, Episode):
                if all(key in _guess for key in ('season', 'episode')):
                    logger.debug("Legendasdivx.pt :: guessing %s", name)
                    logger.debug("Legendasdivx.pt :: subtitle S%sE%s video S%sE%s", _guess['season'], _guess['episode'],
                                 subtitle.video.season, subtitle.video.episode)

                    if subtitle.video.episode != _guess['episode'] or subtitle.video.season != _guess['season']:
                        logger.debug('Legendasdivx.pt :: subtitle does not match video, skipping')
                        continue
                else:
                    logger.debug('Legendasdivx.pt :: no "season" and/or "episode" on "_guess" , skipping')
                    continue
            matches = set()
            matches |= guess_matches(subtitle.video, _guess)
            logger.debug('Legendasdivx.pt :: sub matches: %s', matches)
            _score = sum((_scores.get(match, 0) for match in matches))
            if _score > _max_score:
                _max_name = name
                _max_score = _score
                logger.debug("Legendasdivx.pt :: new max: %s %s", name, _score)

        if _max_score > 0:
            logger.debug("Legendasdivx.pt :: returning from archive: %s scored %s", _max_name, _max_score)
            return archive.read(_max_name)

        logger.error("Legendasdivx.pt :: No subtitle found on compressed file. Max score was 0")
        return None
