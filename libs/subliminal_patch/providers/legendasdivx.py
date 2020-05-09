# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import io
import os
import re
import zipfile
from time import sleep
from requests.exceptions import HTTPError
import rarfile

from guessit import guessit
from subliminal.cache import region
from subliminal.exceptions import ConfigurationError, AuthenticationError, ServiceUnavailable, DownloadLimitExceeded
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending, guess_matches
from subliminal.utils import sanitize, sanitize_release_group
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import TooManyRequests, IPAddressBlocked
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.providers import Provider
from subliminal_patch.score import get_scores, framerate_equal
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language
from dogpile.cache.api import NO_VALUE

logger = logging.getLogger(__name__)

class LegendasdivxSubtitle(Subtitle):
    """Legendasdivx Subtitle."""
    provider_name = 'legendasdivx'

    def __init__(self, language, video, data, skip_wrong_fps=True):
        super(LegendasdivxSubtitle, self).__init__(language)
        self.language = language
        self.page_link = data['link']
        self.hits = data['hits']
        self.exact_match = data['exact_match']
        self.description = data['description']
        self.video = video
        self.sub_frame_rate = data['frame_rate']
        self.video_filename = data['video_filename']
        self.uploader = data['uploader']
        self.wrong_fps = False
        self.skip_wrong_fps = skip_wrong_fps

    @property
    def id(self):
        return self.page_link

    @property
    def release_info(self):
        return self.description

    def get_matches(self, video):
        matches = set()

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
                logger.debug("Legendasdivx :: Skipping subtitle due to FPS mismatch (expected: %s, got: %s)", video.fps, self.sub_frame_rate)
                # not a single match :)
                return set()
            logger.debug("Legendasdivx :: Frame rate mismatch (expected: %s, got: %s, but continuing...)", video.fps, self.sub_frame_rate)

        description = sanitize(self.description)

        if sanitize(self.video_filename) in description:
            matches.update(['title'])
            matches.update(['season'])
            matches.update(['episode'])

        # episode
        if video.title and sanitize(video.title) in description:
            matches.update(['title'])
        if video.year and '{:04d}'.format(video.year) in description:
            matches.update(['year'])

        if isinstance(video, Episode):
            # already matched in search query
            if video.season and 's{:02d}'.format(video.season) in description:
                matches.update(['season'])
            if video.episode and 'e{:02d}'.format(video.episode) in description:
                matches.update(['episode'])
            if video.episode and video.season and video.series:
                if '{} s{:02d}e{:02d}'.format(sanitize(video.series), video.season, video.episode) in description:
                    matches.update(['series'])
                    matches.update(['season'])
                    matches.update(['episode'])

        # release_group
        if video.release_group and sanitize_release_group(video.release_group) in sanitize_release_group(description):
            matches.update(['release_group'])

        # resolution
        if video.resolution and video.resolution.lower() in description:
            matches.update(['resolution'])

        # format
        formats = []
        if video.format:
            formats = [video.format.lower()]
            if formats[0] == "web-dl":
                formats.append("webdl")
                formats.append("webrip")
                formats.append("web")
            for frmt in formats:
                if frmt in description:
                    matches.update(['format'])
                    break

        # video_codec
        if video.video_codec:
            video_codecs = [video.video_codec.lower()]
            if video_codecs[0] == "h264":
                video_codecs.append("x264")
            elif video_codecs[0] == "h265":
                video_codecs.append("x265")
            for vc in video_codecs:
                if vc in description:
                    matches.update(['video_codec'])
                    break

        return matches

class LegendasdivxProvider(Provider):
    """Legendasdivx Provider."""
    languages = {Language('por', 'BR')} | {Language('por')}
    SEARCH_THROTTLE = 8
    site = 'https://www.legendasdivx.pt'
    headers = {
        'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Origin': 'https://www.legendasdivx.pt',
        'Referer': 'https://www.legendasdivx.pt'
    }
    loginpage = site + '/forum/ucp.php?mode=login'
    searchurl = site + '/modules.php?name=Downloads&file=jz&d_op=search&op=_jz00&query={query}'
    download_link = site + '/modules.php{link}'

    def __init__(self, username, password, skip_wrong_fps=True):
        # make sure login credentials are configured.
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Legendasdivx.pt :: Username and password must be specified')
        self.username = username
        self.password = password
        self.skip_wrong_fps = skip_wrong_fps

    def initialize(self):
        logger.info("Legendasdivx.pt :: Creating session for requests")
        self.session = RetryingCFSession()
        # re-use PHP Session if present
        prev_cookies = region.get("legendasdivx_cookies2")
        if prev_cookies != NO_VALUE:
            logger.debug("Legendasdivx.pt :: Re-using previous legendasdivx cookies: %s", prev_cookies)
            self.session.cookies.update(prev_cookies)
        # Login if session has expired
        else:
            logger.debug("Legendasdivx.pt :: Session cookies not found!")
            self.session.headers.update(self.headers)
            self.login()

    def terminate(self):
        # session close
        self.session.close()

    def login(self):
        logger.info('Legendasdivx.pt :: Logging in')
        try:
            res = self.session.get(self.loginpage)
            res.raise_for_status()
            bsoup = ParserBeautifulSoup(res.content, ['lxml'])

            _allinputs = bsoup.findAll('input')
            data = {}
            # necessary to set 'sid' for POST request
            for field in _allinputs:
                data[field.get('name')] = field.get('value')

            data['username'] = self.username
            data['password'] = self.password

            res = self.session.post(self.loginpage, data)
            res.raise_for_status()
            #make sure we're logged in
            logger.debug('Legendasdivx.pt :: Logged in successfully: PHPSESSID: %s', self.session.cookies.get_dict()['PHPSESSID'])
            cj = self.session.cookies.copy()
            store_cks = ("PHPSESSID", "phpbb3_2z8zs_sid", "phpbb3_2z8zs_k", "phpbb3_2z8zs_u", "lang")
            for cn in iter(self.session.cookies.keys()):
                if cn not in store_cks:
                    del cj[cn]
            #store session cookies on cache
            logger.debug("Legendasdivx.pt :: Storing legendasdivx session cookies: %r", cj)
            region.set("legendasdivx_cookies2", cj)

        except KeyError:
            logger.error("Legendasdivx.pt :: Couldn't get session ID, check your credentials")
            raise AuthenticationError("Legendasdivx.pt :: Couldn't get session ID, check your credentials")
        except HTTPError as e:
            if "bloqueado" in res.text.lower(): # ip blocked on server
                logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                raise IPAddressBlocked("LegendasDivx.pt :: Your IP is blocked on this server.")
            if 'limite' in res.text.lower(): # daily downloads limit reached
                logger.error("LegendasDivx.pt :: Daily download limit reached!")
                raise DownloadLimitExceeded("Legendasdivx.pt :: Daily download limit reached!")
            logger.error("Legendasdivx.pt :: HTTP Error %s", e)
            raise TooManyRequests("Legendasdivx.pt :: HTTP Error %s", e)
        except Exception as e:
            logger.error("LegendasDivx.pt :: Uncaught error: %r", e)
            raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r", e)

    def _process_page(self, video, bsoup, video_filename):

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
            #get subtitle link
            download = _subbox.find("a", {"class": "sub_download"})

            # sometimes BSoup can't find 'a' tag and returns None.
            try:
                download_link = self.download_link.format(link=download.get('href'))
                logger.debug("Legendasdivx.pt :: Found subtitle link on: %s ", download_link)
            except:
                logger.debug("Legendasdivx.pt :: Couldn't find download link. Trying next...")
                continue

            # get subtitle uploader
            sub_header = _subbox.find("div", {"class" :"sub_header"})
            uploader = sub_header.find("a").text if sub_header else 'anonymous'

            exact_match = False
            if video.name.lower() in description.lower():
                exact_match = True
            data = {'link': download_link,
                    'exact_match': exact_match,
                    'hits': hits,
                    'uploader': uploader,
                    'frame_rate': frame_rate,
                    'video_filename': video_filename,
                    'description': description
                    }
            subtitles.append(
                LegendasdivxSubtitle(lang, video, data, skip_wrong_fps=self.skip_wrong_fps)
            )
        return subtitles

    def query(self, video, languages):

        video_filename = video.name
        video_filename = os.path.basename(video_filename)
        video_filename, _ = os.path.splitext(video_filename)
        video_filename = sanitize_release_group(video_filename)

        _searchurl = self.searchurl
        if video.imdb_id is None:
            if isinstance(video, Episode):
                querytext = "{} S{:02d}E{:02d}".format(video.series, video.season, video.episode)
            elif isinstance(video, Movie):
                querytext = video.title
        else:
            querytext = video.imdb_id

        # language query filter
        if isinstance(languages, (tuple, list, set)):
            language_ids = ','.join(sorted(l.opensubtitles for l in languages))
            if 'por' in language_ids: # prioritize portuguese subtitles
                lang_filter = '&form_cat=28' # pt
            elif 'pob' in language_ids:
                lang_filter = '&form_cat=29' # br
            else:
                lang_filter = ''

        querytext = querytext + lang_filter if lang_filter else querytext

        try:
            # sleep for a 1 second before another request
            sleep(1)
            self.headers['Referer'] = self.site + '/index.php'
            self.session.headers.update(self.headers)
            res = self.session.get(_searchurl.format(query=querytext), allow_redirects=False)
            res.raise_for_status()
            if (res.status_code == 200 and "A legenda não foi encontrada" in res.text):
                logger.warning('Legendasdivx.pt :: %s not found', querytext)
                return []
            if res.status_code == 302: # got redirected to login page.
                # Seems that our session cookies are no longer valid... clean them from cache
                region.delete("legendasdivx_cookies2")
                logger.debug("Legendasdivx.pt :: Logging in again. Cookies have expired!")
                self.login() # login and try again
                res = self.session.get(_searchurl.format(query=querytext))
                res.raise_for_status()
        except HTTPError as e:
            if "bloqueado" in res.text.lower(): # ip blocked on server
                logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                raise IPAddressBlocked("LegendasDivx.pt :: Your IP is blocked on this server.")
            if 'limite' in res.text.lower(): # daily downloads limit reached
                logger.error("LegendasDivx.pt :: Daily download limit reached!")
                raise DownloadLimitExceeded("Legendasdivx.pt :: Daily download limit reached!")
            logger.error("Legendasdivx.pt :: HTTP Error %s", e)
            raise TooManyRequests("Legendasdivx.pt :: HTTP Error %s", e)
        except Exception as e:
            logger.error("LegendasDivx.pt :: Uncaught error: %r", e)
            raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r", e)

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
        subtitles = self._process_page(video, bsoup, video_filename)

        # more pages?
        if num_pages > 1:
            for num_page in range(2, num_pages+1):
                sleep(1) # another 1 sec before requesting...
                _search_next = self.searchurl.format(query=querytext) + "&page={0}".format(str(num_page))
                logger.debug("Legendasdivx.pt :: Moving on to next page: %s", _search_next)
                res = self.session.get(_search_next)
                next_page = ParserBeautifulSoup(res.content, ['html.parser'])
                subs = self._process_page(video, next_page, video_filename)
                subtitles.extend(subs)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def download_subtitle(self, subtitle):
        res = self.session.get(subtitle.page_link)

        try:
            res.raise_for_status()
        except HTTPError as e:
            if "bloqueado" in res.text.lower(): # ip blocked on server
                logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                raise IPAddressBlocked("LegendasDivx.pt :: Your IP is blocked on this server.")
            if 'limite' in res.text.lower(): # daily downloads limit reached
                logger.error("LegendasDivx.pt :: Daily download limit reached!")
                raise DownloadLimitExceeded("Legendasdivx.pt :: Daily download limit reached!")
            logger.error("Legendasdivx.pt :: HTTP Error %s", e)
            raise TooManyRequests("Legendasdivx.pt :: HTTP Error %s", e)
        except Exception as e:
            logger.error("LegendasDivx.pt :: Uncaught error: %r", e)
            raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r", e)

        archive = self._get_archive(res.content)
        # extract the subtitle
        subtitle_content = self._get_subtitle_from_archive(archive, subtitle)
        subtitle.content = fix_line_ending(subtitle_content)
        subtitle.normalize()

        return subtitle

    def _get_archive(self, content):
        # open the archive
        # stole^H^H^H^H^H inspired from subvix provider
        archive_stream = io.BytesIO(content)
        if rarfile.is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive = rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive = zipfile.ZipFile(archive_stream)
        else:
            raise ValueError('Unsupported compressed format')

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
                logger.debug("guessing %s", name)
                logger.debug("subtitle S%sE%s video S%sE%s", _guess['season'], _guess['episode'], subtitle.video.season, subtitle.video.episode)

                if subtitle.video.episode != _guess['episode'] or subtitle.video.season != _guess['season']:
                    logger.debug('subtitle does not match video, skipping')
                    continue

            matches = set()
            matches |= guess_matches(subtitle.video, _guess)
            logger.debug('srt matches: %s', matches)
            _score = sum((_scores.get(match, 0) for match in matches))
            if _score > _max_score:
                _max_name = name
                _max_score = _score
                logger.debug("new max: %s %s", name, _score)

        if _max_score > 0:
            logger.debug("returning from archive: %s scored %s", _max_name, _max_score)
            return archive.read(_max_name)

        raise ValueError("No subtitle found on compressed file. Max score was 0")
