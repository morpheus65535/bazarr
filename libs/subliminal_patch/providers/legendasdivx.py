# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import io
import re
import os
import rarfile
import zipfile

from requests import Session
from guessit import guessit
from subliminal.exceptions import ConfigurationError, AuthenticationError, ServiceUnavailable, DownloadLimitExceeded
from subliminal_patch.providers import Provider
from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.subtitle import Subtitle
from subliminal.video import Episode, Movie
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending, guess_matches
from subzero.language import Language
from subliminal_patch.score import get_scores
from subliminal.utils import sanitize, sanitize_release_group

logger = logging.getLogger(__name__)

class LegendasdivxSubtitle(Subtitle):
    """Legendasdivx Subtitle."""
    provider_name = 'legendasdivx'

    def __init__(self, language, video, data):
        super(LegendasdivxSubtitle, self).__init__(language)
        self.language = language
        self.page_link = data['link']
        self.hits = data['hits']
        self.exact_match = data['exact_match']
        self.description = data['description']
        self.video = video
        self.video_filename = data['video_filename']
        self.uploader = data['uploader']

    @property
    def id(self):
        return self.page_link

    @property
    def release_info(self):
        return self.description

    def get_matches(self, video):
        matches = set()

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

        # running guessit on a huge description may break guessit
        # matches |= guess_matches(video, guessit(self.description))
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
        'Referer': 'https://www.legendasdivx.pt',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    loginpage = site + '/forum/ucp.php?mode=login'
    logoutpage = site + '/sair.php'
    searchurl = site + '/modules.php?name=Downloads&file=jz&d_op=search&op=_jz00&query={query}'
    download_link = site + '/modules.php{link}'

    def __init__(self, username, password):
        # make sure login credentials are configured.
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')
        self.username = username
        self.password = password
        self.logged_in = False

    def initialize(self):
        self.session = Session()
        self.session.headers.update(self.headers)
        self.login()

    def terminate(self):
        self.logout()
        self.session.close()

    def login(self):
        logger.info('Logging in')
        
        res = self.session.get(self.loginpage)
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
        
        try:
            logger.debug('Logged in successfully: PHPSESSID: %s' %
                         self.session.cookies.get_dict()['PHPSESSID'])
            self.logged_in = True   
        except KeyError:
            logger.error("Couldn't retrieve session ID, check your credentials")
            raise AuthenticationError("Please check your credentials.")
        except Exception as e:
            if 'bloqueado' in res.text.lower(): # blocked IP address 
                logger.error("LegendasDivx.pt :: Your IP is blocked on this server.")
                raise ParseResponseError("Legendasdivx.pt :: %r" % res.text)
            logger.error("LegendasDivx.pt :: Uncaught error: %r" % repr(e))
            raise ServiceUnavailable("LegendasDivx.pt :: Uncaught error: %r" % repr(e))

    def logout(self):
        if self.logged_in:
            logger.info('Legendasdivx:: Logging out')
            r = self.session.get(self.logoutpage, timeout=10)
            r.raise_for_status()
            logger.debug('Legendasdivx :: Logged out')
            self.logged_in = False

    def _process_page(self, video, bsoup, video_filename):

        subtitles = []

        _allsubs = bsoup.findAll("div", {"class": "sub_box"})

        for _subbox in _allsubs:
            hits = 0
            for th in _subbox.findAll("th", {"class": "color2"}):
                if th.string == 'Hits:':
                    hits = int(th.parent.find("td").string)
                if th.string == 'Idioma:':
                    lang = th.parent.find("td").find("img").get('src')
                    if 'brazil' in lang.lower():
                        lang = Language.fromopensubtitles('pob')
                    elif 'portugal' in lang.lower():
                        lang = Language.fromopensubtitles('por')
                    else:
                        continue
            # get description for matches
            description = _subbox.find("td", {"class": "td_desc brd_up"}).get_text()
            #get subtitle link
            download = _subbox.find("a", {"class": "sub_download"})
            
            # sometimes BSoup can't find 'a' tag and returns None. 
            i = 0
            while not (download): # must get it... trying again...
                download = _subbox.find("a", {"class": "sub_download"})
                i=+1
                logger.debug("Try number {0} try!".format(str(i)))
            dl = download.get('href')
            logger.debug("Found subtitle on: %s" % self.download_link.format(link=dl))

            # get subtitle uploader
            sub_header = _subbox.find("div", {"class" :"sub_header"}) 
            uploader = sub_header.find("a").text if sub_header else '<n/a>'

            exact_match = False
            if video.name.lower() in description.lower():
                exact_match = True
            data = {'link': self.site + '/modules.php' + download.get('href'),
                    'exact_match': exact_match,
                    'hits': hits,
                    'uploader': uploader,
                    'video_filename': video_filename,
                    'description': description
                    }
            subtitles.append(
                LegendasdivxSubtitle(lang, video, data)
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

        self.headers['Referer'] = self.site + '/index.php'
        self.session.headers.update(self.headers.items())
        res = self.session.get(_searchurl.format(query=querytext))

        if "A legenda não foi encontrada" in res.text:
            logger.warning('%s not found', querytext)
            return []

        bsoup = ParserBeautifulSoup(res.content, ['html.parser'])
        subtitles = self._process_page(video, bsoup, video_filename)

        # search for more than 10 results (legendasdivx uses pagination)
        # don't throttle - maximum results = 6 * 10
        MAX_PAGES = 6
        
        #get number of pages bases on results found
        page_header = bsoup.find("div", {"class": "pager_bar"})
        results_found = re.search(r'\((.*?) encontradas\)', page_header.text).group(1)
        num_pages = (int(results_found) // 10) + 1
        num_pages = min(MAX_PAGES, num_pages)

        if num_pages > 1:
            for num_page in range(2, num_pages+2):
                _search_next = self.searchurl.format(query=querytext) + "&page={0}".format(str(num_page))
                logger.debug("Moving to next page: %s" % _search_next)
                res = self.session.get(_search_next)
                next_page = ParserBeautifulSoup(res.content, ['html.parser'])
                subs = self._process_page(video, next_page, video_filename)
                subtitles.extend(subs)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def download_subtitle(self, subtitle):
        res = self.session.get(subtitle.page_link)
        res.raise_for_status()
        if res:
            if res.status_code in ['500', '503']:
                raise ServiceUnavailable("Legendasdivx.pt :: 503 - Service Unavailable")
            elif 'limite' in res.text.lower(): # daily downloads limit reached
                raise DownloadLimitReached("Legendasdivx.pt :: Download limit reached")
            elif 'bloqueado' in res.text.lower(): # blocked IP address 
                raise ParseResponseError("Legendasdivx.pt :: %r" % res.text)

            archive = self._get_archive(res.content)
            # extract the subtitle
            subtitle_content = self._get_subtitle_from_archive(archive, subtitle)
            subtitle.content = fix_line_ending(subtitle_content)
            subtitle.normalize()

            return subtitle

        logger.error("Legendasdivx.pt :: there was a problem retrieving subtitle (status %s)" % res.status_code)
        return

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
            raise Exception('Unsupported compressed format')

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

            _guess = guessit (name)
            if isinstance(subtitle.video, Episode):
                logger.debug ("guessing %s" % name)
                logger.debug("subtitle S{}E{} video S{}E{}".format(_guess['season'],_guess['episode'],subtitle.video.season,subtitle.video.episode))

                if subtitle.video.episode != _guess['episode'] or subtitle.video.season != _guess['season']:
                    logger.debug('subtitle does not match video, skipping')
                    continue

            matches = set()
            matches |= guess_matches (subtitle.video, _guess)
            logger.debug('srt matches: %s' % matches)
            _score = sum ((_scores.get (match, 0) for match in matches))
            if _score > _max_score:
                _max_name = name
                _max_score = _score
                logger.debug("new max: {} {}".format(name, _score))

        if _max_score > 0:
            logger.debug("returning from archive: {} scored {}".format(_max_name, _max_score))
            return archive.read(_max_name)

        raise ValueError("No subtitle found on compressed file. Max score was 0") 