# coding=utf-8
import base64
import logging
import os
import traceback
import zlib
import time
import requests

from babelfish import language_converters
from dogpile.cache.api import NO_VALUE
from subliminal.exceptions import ConfigurationError, ServiceUnavailable
from subliminal.providers.opensubtitles import OpenSubtitlesProvider as _OpenSubtitlesProvider,\
    OpenSubtitlesSubtitle as _OpenSubtitlesSubtitle, Episode, Movie, ServerProxy, Unauthorized, NoSession, \
    DownloadLimitReached, InvalidImdbid, UnknownUserAgent, DisabledUserAgent, OpenSubtitlesError
from mixins import ProviderRetryMixin
from subliminal.subtitle import fix_line_ending
from subliminal_patch.http import SubZeroRequestsTransport
from subliminal_patch.utils import sanitize
from subliminal.cache import region
from subliminal_patch.score import framerate_equal
from subzero.language import Language

from ..exceptions import TooManyRequests, APIThrottled

logger = logging.getLogger(__name__)


class OpenSubtitlesSubtitle(_OpenSubtitlesSubtitle):
    hash_verifiable = True
    hearing_impaired_verifiable = True

    def __init__(self, language, hearing_impaired, page_link, subtitle_id, matched_by, movie_kind, hash, movie_name,
                 movie_release_name, movie_year, movie_imdb_id, series_season, series_episode, query_parameters,
                 filename, encoding, fps, skip_wrong_fps=True):
        super(OpenSubtitlesSubtitle, self).__init__(language, hearing_impaired, page_link, subtitle_id,
                                                    matched_by, movie_kind, hash,
                                                    movie_name, movie_release_name, movie_year, movie_imdb_id,
                                                    series_season, series_episode, filename, encoding)
        self.query_parameters = query_parameters or {}
        self.fps = fps
        self.release_info = movie_release_name
        self.wrong_fps = False
        self.skip_wrong_fps = skip_wrong_fps

    def get_matches(self, video, hearing_impaired=False):
        matches = super(OpenSubtitlesSubtitle, self).get_matches(video)

        # episode
        if isinstance(video, Episode) and self.movie_kind == 'episode':
            # series
            if video.series and (sanitize(self.series_name) in (
                    sanitize(name) for name in [video.series] + video.alternative_series)):
                matches.add('series')
        # movie
        elif isinstance(video, Movie) and self.movie_kind == 'movie':
            # title
            if video.title and (sanitize(self.movie_name) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')

        sub_fps = None
        try:
            sub_fps = float(self.fps)
        except ValueError:
            pass

        # video has fps info, sub also, and sub's fps is greater than 0
        if video.fps and sub_fps and not framerate_equal(video.fps, self.fps):
            self.wrong_fps = True

            if self.skip_wrong_fps:
                logger.debug("Wrong FPS (expected: %s, got: %s, lowering score massively)", video.fps, self.fps)
                # fixme: may be too harsh
                return set()
            else:
                logger.debug("Wrong FPS (expected: %s, got: %s, continuing)", video.fps, self.fps)

        # matched by tag?
        if self.matched_by == "tag":
            # treat a tag match equally to a hash match
            logger.debug("Subtitle matched by tag, treating it as a hash-match. Tag: '%s'",
                         self.query_parameters.get("tag", None))
            matches.add("hash")

        return matches


class OpenSubtitlesProvider(ProviderRetryMixin, _OpenSubtitlesProvider):
    only_foreign = False
    also_foreign = False
    subtitle_class = OpenSubtitlesSubtitle
    hash_verifiable = True
    hearing_impaired_verifiable = True
    skip_wrong_fps = True
    is_vip = False
    use_ssl = True
    timeout = 15

    default_url = "//api.opensubtitles.org/xml-rpc"
    vip_url = "//vip-api.opensubtitles.org/xml-rpc"

    languages = {Language.fromopensubtitles(l) for l in language_converters['szopensubtitles'].codes}
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))

    def __init__(self, username=None, password=None, use_tag_search=False, only_foreign=False, also_foreign=False,
                 skip_wrong_fps=True, is_vip=False, use_ssl=True, timeout=15):
        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.username = username or ''
        self.password = password or ''
        self.use_tag_search = use_tag_search
        self.only_foreign = only_foreign
        self.also_foreign = also_foreign
        self.skip_wrong_fps = skip_wrong_fps
        self.token = None
        self.is_vip = is_vip
        self.use_ssl = use_ssl
        self.timeout = timeout

        logger.debug("Using timeout: %d", timeout)

        if use_ssl:
            logger.debug("Using HTTPS connection")

        self.default_url = ("https:" if use_ssl else "http:") + self.default_url
        self.vip_url = ("https:" if use_ssl else "http:") + self.vip_url

        if use_tag_search:
            logger.info("Using tag/exact filename search")

        if only_foreign:
            logger.info("Only searching for foreign/forced subtitles")

    def get_server_proxy(self, url, timeout=None):
        return ServerProxy(url, SubZeroRequestsTransport(use_https=self.use_ssl, timeout=timeout or self.timeout,
                                                         user_agent=os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")))

    def log_in(self, server_url=None):
        if server_url:
            self.terminate()

            self.server = self.get_server_proxy(server_url)

        response = self.retry(
            lambda: checked(
                lambda: self.server.LogIn(self.username, self.password, 'eng',
                                          os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"))
            )
        )

        self.token = response['token']
        logger.debug('Logged in with token %r', self.token[:10]+"X"*(len(self.token)-10))

        region.set("os_token", self.token)

    def use_token_or_login(self, func):
        if not self.token:
            self.log_in()
            return func()
        try:
            return func()
        except Unauthorized:
            self.log_in()
            return func()

    def initialize(self):
        if self.is_vip:
            self.server = self.get_server_proxy(self.vip_url)
            logger.info("Using VIP server")
        else:
            self.server = self.get_server_proxy(self.default_url)

        logger.info('Logging in')

        token = region.get("os_token")
        if token is not NO_VALUE:
            try:
                logger.debug('Trying previous token: %r', token[:10]+"X"*(len(token)-10))
                checked(lambda: self.server.NoOperation(token))
                self.token = token
                logger.debug("Using previous login token: %r", token[:10]+"X"*(len(token)-10))
                return
            except (NoSession, Unauthorized):
                logger.debug('Token not valid.')
                pass

        try:
            self.log_in()

        except Unauthorized:
            if self.is_vip:
                logger.info("VIP server login failed, falling back")
                self.log_in(self.default_url)
                if self.token:
                    return

            logger.error("Login failed, please check your credentials")
                
    def terminate(self):
        if self.token:
            try:
                checked(lambda: self.server.LogOut(self.token))
            except:
                logger.error("Logout failed: %s", traceback.format_exc())

        self.server = None
        self.token = None

    def list_subtitles(self, video, languages):
        """
        :param video:
        :param languages:
        :return:

         patch: query movies even if hash is known; add tag parameter
        """

        season = episode = None
        if isinstance(video, Episode):
            query = [video.series] + video.alternative_series
            season = video.season
            episode = episode = min(video.episode) if isinstance(video.episode, list) else video.episode

            if video.is_special:
                season = None
                episode = None
                query = [u"%s %s" % (series, video.title) for series in [video.series] + video.alternative_series]
                logger.info("%s: Searching for special: %r", self.__class__, query)
        # elif ('opensubtitles' not in video.hashes or not video.size) and not video.imdb_id:
        #    query = video.name.split(os.sep)[-1]
        else:
            query = [video.title] + video.alternative_titles

        return self.query(languages, hash=video.hashes.get('opensubtitles'), size=video.size, imdb_id=video.imdb_id,
                          query=query, season=season, episode=episode, tag=video.original_name,
                          use_tag_search=self.use_tag_search, only_foreign=self.only_foreign,
                          also_foreign=self.also_foreign)

    def query(self, languages, hash=None, size=None, imdb_id=None, query=None, season=None, episode=None, tag=None,
              use_tag_search=False, only_foreign=False, also_foreign=False):
        # fill the search criteria
        criteria = []
        if hash and size:
            criteria.append({'moviehash': hash, 'moviebytesize': str(size)})
        if use_tag_search and tag:
            criteria.append({'tag': tag})
        if imdb_id:
            if season and episode:
                criteria.append({'imdbid': imdb_id[2:], 'season': season, 'episode': episode})
            else:
                criteria.append({'imdbid': imdb_id[2:]})
        if query and season and episode:
            for q in query:
                criteria.append({'query': q.replace('\'', ''), 'season': season, 'episode': episode})
        elif query:
            for q in query:
                criteria.append({'query': q.replace('\'', '')})
        if not criteria:
            raise ValueError('Not enough information')

        # add the language
        for criterion in criteria:
            criterion['sublanguageid'] = ','.join(sorted(l.opensubtitles for l in languages))

        # query the server
        logger.info('Searching subtitles %r', criteria)
        response = self.use_token_or_login(
            lambda: self.retry(lambda: checked(lambda: self.server.SearchSubtitles(self.token, criteria)))
        )

        subtitles = []

        # exit if no data
        if not response['data']:
            logger.info('No subtitles found')
            return subtitles

        # loop over subtitle items
        for subtitle_item in response['data']:
            _subtitle_item = subtitle_item

            # in case OS messes their API results up again, check whether we've got a dict or a string as subtitle_item
            if hasattr(_subtitle_item, "startswith"):
                _subtitle_item = response["data"][subtitle_item]

            # read the item
            language = Language.fromopensubtitles(_subtitle_item['SubLanguageID'])
            hearing_impaired = bool(int(_subtitle_item['SubHearingImpaired']))
            page_link = _subtitle_item['SubtitlesLink']
            subtitle_id = int(_subtitle_item['IDSubtitleFile'])
            matched_by = _subtitle_item['MatchedBy']
            movie_kind = _subtitle_item['MovieKind']
            hash = _subtitle_item['MovieHash']
            movie_name = _subtitle_item['MovieName']
            movie_release_name = _subtitle_item['MovieReleaseName']
            movie_year = int(_subtitle_item['MovieYear']) if _subtitle_item['MovieYear'] else None
            movie_imdb_id = 'tt' + _subtitle_item['IDMovieImdb']
            movie_fps = _subtitle_item.get('MovieFPS')
            series_season = int(_subtitle_item['SeriesSeason']) if _subtitle_item['SeriesSeason'] else None
            series_episode = int(_subtitle_item['SeriesEpisode']) if _subtitle_item['SeriesEpisode'] else None
            filename = _subtitle_item['SubFileName']
            encoding = _subtitle_item.get('SubEncoding') or None
            foreign_parts_only = bool(int(_subtitle_item.get('SubForeignPartsOnly', 0)))

            # foreign/forced subtitles only wanted
            if only_foreign and not foreign_parts_only:
                continue

            # foreign/forced not wanted
            elif not only_foreign and not also_foreign and foreign_parts_only:
                continue

            # set subtitle language to forced if it's foreign_parts_only
            elif (also_foreign or only_foreign) and foreign_parts_only:
                language = Language.rebuild(language, forced=True)

            if language not in languages:
                continue

            query_parameters = _subtitle_item.get("QueryParameters")

            subtitle = self.subtitle_class(language, hearing_impaired, page_link, subtitle_id, matched_by,
                                           movie_kind,
                                           hash, movie_name, movie_release_name, movie_year, movie_imdb_id,
                                           series_season, series_episode, query_parameters, filename, encoding,
                                           movie_fps, skip_wrong_fps=self.skip_wrong_fps)
            logger.debug('Found subtitle %r by %s', subtitle, matched_by)
            subtitles.append(subtitle)

        return subtitles

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)
        response = self.use_token_or_login(
            lambda: checked(
                lambda: self.server.DownloadSubtitles(self.token, [str(subtitle.subtitle_id)])
            )
        )
        subtitle.content = fix_line_ending(zlib.decompress(base64.b64decode(response['data'][0]['data']), 47))


def checked(fn, raise_api_limit=False):
    """Run :fn: and check the response status before returning it.

    :param fn: the function to make an XMLRPC call to OpenSubtitles.
    :return: the response.
    :raise: :class:`OpenSubtitlesError`

    """
    response = None
    try:
        try:
            response = fn()
        except APIThrottled:
            if not raise_api_limit:
                logger.info("API request limit hit, waiting and trying again once.")
                time.sleep(12)
                return checked(fn, raise_api_limit=True)
            raise

        except requests.RequestException as e:
            status_code = e.response.status_code
        else:
            status_code = int(response['status'][:3])
    except:
        status_code = None

    if status_code == 401:
        raise Unauthorized
    if status_code == 406:
        raise NoSession
    if status_code == 407:
        raise DownloadLimitReached
    if status_code == 413:
        raise InvalidImdbid
    if status_code == 414:
        raise UnknownUserAgent
    if status_code == 415:
        raise DisabledUserAgent
    if status_code == 429:
        if not raise_api_limit:
            raise TooManyRequests
        else:
            raise APIThrottled
    if status_code == 503:
        raise ServiceUnavailable(str(status_code))
    if status_code != 200:
        if response and "status" in response:
            raise OpenSubtitlesError(response['status'])
        raise ServiceUnavailable("Unknown Error, empty response: %s: %r" % (status_code, response))

    return response
