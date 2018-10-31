# coding=utf-8

import io
import logging
import os
import time

from random import randint
from zipfile import ZipFile

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subliminal import Episode, ProviderError
from subliminal.utils import sanitize_release_group
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.converters.subscene import language_ids, supported_languages
from subscene_api.subscene import search, Subtitle as APISubtitle
from subzero.language import Language


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

    search_throttle = 2  # seconds

    def __init__(self, only_foreign=False):
        self.only_foreign = only_foreign

    def initialize(self):
        logger.info("Creating session")
        self.session = Session()
        from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
        self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        logger.info("Closing session")
        self.session.close()

    def _create_filters(self, languages):
        self.filters = dict(HearingImpaired="2")
        if self.only_foreign:
            self.filters["ForeignOnly"] = "True"
            logger.info("Only searching for foreign/forced subtitles")

        self.filters["LanguageFilter"] = ",".join((str(language_ids[l.alpha3]) for l in languages
                                                   if l.alpha3 in language_ids))

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
            subtitle = SubsceneSubtitle.from_api(s)
            subtitle.asked_for_release_group = video.release_group
            if isinstance(video, Episode):
                subtitle.asked_for_episode = video.episode

            if self.only_foreign:
                subtitle.language = Language.rebuild(subtitle.language, forced=True)

            subtitles.append(subtitle)
            logger.debug('Found subtitle %r', subtitle)

        return subtitles

    def query(self, video):
        vfn = get_video_filename(video)
        logger.debug(u"Searching for: %s", vfn)
        film = search(vfn, session=self.session)

        subtitles = []
        if film and film.subtitles:
            subtitles = self.parse_results(video, film)

        # re-search for episodes without explicit release name
        if isinstance(video, Episode):
            term = u"%s S%02iE%02i" % (video.series, video.season, video.episode)
            time.sleep(self.search_throttle)
            logger.debug('Searching for alternative results: %s', term)
            film = search(term, session=self.session)
            if film and film.subtitles:
                subtitles += self.parse_results(video, film)

            # packs
            if video.season_fully_aired:
                term = u"%s S%02i" % (video.series, video.season)
                logger.debug('Searching for packs: %s', term)
                time.sleep(self.search_throttle)
                film = search(term, session=self.session)
                if film and film.subtitles:
                    subtitles += self.parse_results(video, film)
            else:
                logger.debug("Not searching for packs, because the season hasn't fully aired")

        logger.info("%s subtitles found" % len(subtitles))
        return subtitles
