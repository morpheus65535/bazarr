# coding=utf-8

import io
import logging
import os
import time
import traceback

import requests

import inflect
import re
import json
import HTMLParser
import urlparse

from zipfile import ZipFile
from babelfish import language_converters
from guessit import guessit
from dogpile.cache.api import NO_VALUE
from subliminal import Episode, ProviderError
from subliminal.exceptions import ConfigurationError, ServiceUnavailable
from subliminal.utils import sanitize_release_group
from subliminal.cache import region
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.converters.subscene import language_ids, supported_languages
from subscene_api.subscene import search, Subtitle as APISubtitle, SITE_DOMAIN
from subzero.language import Language

p = inflect.engine()

language_converters.register('subscene = subliminal_patch.converters.subscene:SubsceneConverter')
logger = logging.getLogger(__name__)


class SubsceneSubtitle(Subtitle):
    provider_name = 'subscene'
    hearing_impaired_verifiable = True
    is_pack = False
    page_link = None
    season = None
    episode = None
    releases = None

    def __init__(self, language, release_info, hearing_impaired=False, page_link=None, encoding=None, mods=None,
                 asked_for_release_group=None, asked_for_episode=None):
        super(SubsceneSubtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link,
                                               encoding=encoding, mods=mods)
        self.release_info = self.releases = release_info
        self.asked_for_episode = asked_for_episode
        self.asked_for_release_group = asked_for_release_group
        self.season = None
        self.episode = None

    @classmethod
    def from_api(cls, s):
        return cls(Language.fromsubscene(s.language.strip()), s.title, hearing_impaired=s.hearing_impaired,
                   page_link=s.url)

    @property
    def id(self):
        return self.page_link

    @property
    def numeric_id(self):
        return self.page_link.split("/")[-1]

    def get_matches(self, video):
        matches = set()

        if self.release_info.strip() == get_video_filename(video):
            logger.debug("Using hash match as the release name is the same")
            matches |= {"hash"}

        # episode
        if isinstance(video, Episode):
            guess = guessit(self.release_info, {'type': 'episode'})
            self.season = guess.get("season")
            self.episode = guess.get("episode")

            matches |= guess_matches(video, guess)
            if "season" in matches and "episode" not in guess:
                # pack
                matches.add("episode")
                logger.debug("%r is a pack", self)
                self.is_pack = True

        # movie
        else:
            guess = guessit(self.release_info, {'type': 'movie'})
            matches |= guess_matches(video, guess)

        if video.release_group and "release_group" not in matches and "release_group" in guess:
            if sanitize_release_group(video.release_group) in sanitize_release_group(guess["release_group"]):
                matches.add("release_group")

        self.matches = matches

        return matches

    def get_download_link(self, session):
        return APISubtitle.get_zipped_url(self.page_link, session)


def get_video_filename(video):
    return os.path.splitext(os.path.basename(video.original_name))[0]


class SubsceneProvider(Provider, ProviderSubtitleArchiveMixin):
    """
    This currently only searches for the filename on SubScene. It doesn't open every found subtitle page to avoid
    massive hammering, thus it can't determine whether a subtitle is only-foreign or not.
    """
    subtitle_class = SubsceneSubtitle
    languages = supported_languages
    languages.update(set(Language.rebuild(l, forced=True) for l in languages))

    session = None
    skip_wrong_fps = False
    hearing_impaired_verifiable = True
    only_foreign = False
    username = None
    password = None

    search_throttle = 8  # seconds

    def __init__(self, only_foreign=False, username=None, password=None):
        if not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.only_foreign = only_foreign
        self.username = username
        self.password = password

    def initialize(self):
        logger.info("Creating session")
        self.session = RetryingCFSession()

        prev_cookies = region.get("subscene_cookies2")
        if prev_cookies != NO_VALUE:
            logger.debug("Re-using old subscene cookies: %r", prev_cookies)
            self.session.cookies.update(prev_cookies)

        else:
            logger.debug("Logging in")
            self.login()

    def login(self):
        r = self.session.get("https://subscene.com/account/login")
        if "Server Error" in r.content:
            logger.error("Login unavailable; Maintenance?")
            raise ServiceUnavailable("Login unavailable; Maintenance?")

        match = re.search(r"<script id='modelJson' type='application/json'>\s*(.+)\s*</script>", r.content)

        if match:
            h = HTMLParser.HTMLParser()
            data = json.loads(h.unescape(match.group(1)))
            login_url = urlparse.urljoin(data["siteUrl"], data["loginUrl"])
            time.sleep(1.0)

            r = self.session.post(login_url,
                                  {
                                      "username": self.username,
                                      "password": self.password,
                                      data["antiForgery"]["name"]: data["antiForgery"]["value"]
                                  })
            pep_content = re.search(r"<form method=\"post\" action=\"https://subscene\.com/\">"
                                    r".+name=\"id_token\".+?value=\"(?P<id_token>.+?)\".*?"
                                    r"access_token\".+?value=\"(?P<access_token>.+?)\".+?"
                                    r"token_type.+?value=\"(?P<token_type>.+?)\".+?"
                                    r"expires_in.+?value=\"(?P<expires_in>.+?)\".+?"
                                    r"scope.+?value=\"(?P<scope>.+?)\".+?"
                                    r"state.+?value=\"(?P<state>.+?)\".+?"
                                    r"session_state.+?value=\"(?P<session_state>.+?)\"",
                                    r.content, re.MULTILINE | re.DOTALL)

            if pep_content:
                r = self.session.post(SITE_DOMAIN, pep_content.groupdict())
                try:
                    r.raise_for_status()
                except Exception:
                    raise ProviderError("Something went wrong when trying to log in: %s", traceback.format_exc())
                else:
                    cj = self.session.cookies.copy()
                    store_cks = ("scene", "idsrv", "idsrv.xsrf", "idsvr.clients", "idsvr.session", "idsvr.username")
                    for cn in self.session.cookies.iterkeys():
                        if cn not in store_cks:
                            del cj[cn]

                    logger.debug("Storing cookies: %r", cj)
                    region.set("subscene_cookies2", cj)
                    return
        raise ProviderError("Something went wrong when trying to log in #1")

    def terminate(self):
        logger.info("Closing session")
        self.session.close()

    def _create_filters(self, languages):
        self.filters = dict(HearingImpaired="2")
        acc_filters = self.filters.copy()
        if self.only_foreign:
            self.filters["ForeignOnly"] = "True"
            acc_filters["ForeignOnly"] = self.filters["ForeignOnly"].lower()
            logger.info("Only searching for foreign/forced subtitles")

        selected_ids = []
        for l in languages:
            lid = language_ids.get(l.basename, language_ids.get(l.alpha3, None))
            if lid:
                selected_ids.append(str(lid))

        acc_filters["SelectedIds"] = selected_ids
        self.filters["LanguageFilter"] = ",".join(acc_filters["SelectedIds"])

        last_filters = region.get("subscene_filters")
        if last_filters != acc_filters:
            region.set("subscene_filters", acc_filters)
            logger.debug("Setting account filters to %r", acc_filters)
            self.session.post("https://u.subscene.com/filter", acc_filters, allow_redirects=False)

        logger.debug("Filter created: '%s'" % self.filters)

    def _enable_filters(self):
        self.session.cookies.update(self.filters)
        logger.debug("Filters applied")

    def list_subtitles(self, video, languages):
        if not video.original_name:
            logger.info("Skipping search because we don't know the original release name")
            return []

        self._create_filters(languages)
        self._enable_filters()
        return [s for s in self.query(video) if s.language in languages]

    def download_subtitle(self, subtitle):
        if subtitle.pack_data:
            logger.info("Using previously downloaded pack data")
            archive = ZipFile(io.BytesIO(subtitle.pack_data))
            subtitle.pack_data = None

            try:
                subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
                return
            except ProviderError:
                pass

        # open the archive
        r = self.session.get(subtitle.get_download_link(self.session), timeout=10)
        r.raise_for_status()
        archive_stream = io.BytesIO(r.content)
        archive = ZipFile(archive_stream)

        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

        # store archive as pack_data for later caching
        subtitle.pack_data = r.content

    def parse_results(self, video, film):
        subtitles = []
        for s in film.subtitles:
            try:
                subtitle = SubsceneSubtitle.from_api(s)
            except NotImplementedError, e:
                logger.info(e)
                continue
            subtitle.asked_for_release_group = video.release_group
            if isinstance(video, Episode):
                subtitle.asked_for_episode = video.episode

            if self.only_foreign:
                subtitle.language = Language.rebuild(subtitle.language, forced=True)

            subtitles.append(subtitle)
            logger.debug('Found subtitle %r', subtitle)

        return subtitles

    def do_search(self, *args, **kwargs):
        try:
            return search(*args, **kwargs)
        except requests.HTTPError:
            region.delete("subscene_cookies2")

    def query(self, video):
        # vfn = get_video_filename(video)
        subtitles = []
        # logger.debug(u"Searching for: %s", vfn)
        # film = search(vfn, session=self.session)
        #
        # if film and film.subtitles:
        #     logger.debug('Release results found: %s', len(film.subtitles))
        #     subtitles = self.parse_results(video, film)
        # else:
        #     logger.debug('No release results found')

        # time.sleep(self.search_throttle)

        # re-search for episodes without explicit release name
        if isinstance(video, Episode):
            titles = list(set([video.series] + video.alternative_series))[:2]
            # term = u"%s S%02iE%02i" % (video.series, video.season, video.episode)
            more_than_one = len(titles) > 1
            for series in titles:
                term = u"%s - %s Season" % (series, p.number_to_words("%sth" % video.season).capitalize())
                logger.debug('Searching for alternative results: %s', term)
                film = self.do_search(term, session=self.session, release=False, throttle=self.search_throttle)
                if film and film.subtitles:
                    logger.debug('Alternative results found: %s', len(film.subtitles))
                    subtitles += self.parse_results(video, film)
                else:
                    logger.debug('No alternative results found')

                # packs
                # if video.season_fully_aired:
                #     term = u"%s S%02i" % (series, video.season)
                #     logger.debug('Searching for packs: %s', term)
                #     time.sleep(self.search_throttle)
                #     film = search(term, session=self.session, throttle=self.search_throttle)
                #     if film and film.subtitles:
                #         logger.debug('Pack results found: %s', len(film.subtitles))
                #         subtitles += self.parse_results(video, film)
                #     else:
                #         logger.debug('No pack results found')
                # else:
                #     logger.debug("Not searching for packs, because the season hasn't fully aired")
                if more_than_one:
                    time.sleep(self.search_throttle)
        else:
            titles = list(set([video.title] + video.alternative_titles))[:2]
            more_than_one = len(titles) > 1
            for title in titles:
                logger.debug('Searching for movie results: %r', title)
                film = self.do_search(title, year=video.year, session=self.session, limit_to=None, release=False,
                                      throttle=self.search_throttle)
                if film and film.subtitles:
                    subtitles += self.parse_results(video, film)
                if more_than_one:
                    time.sleep(self.search_throttle)

        logger.info("%s subtitles found" % len(subtitles))
        return subtitles
