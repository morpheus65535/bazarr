# -*- coding: utf-8 -*-

import logging
import time

from requests import HTTPError
from requests import Session
from subliminal_patch.core import Episode
from subliminal_patch.language import PatchedAddic7edConverter
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.gestdown.info"


class GestdownSubtitle(Subtitle):
    provider_name = "gestdown"
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, data: dict):
        super().__init__(language, hearing_impaired=data["hearingImpaired"])
        self.page_link = _BASE_URL + data["downloadUri"]
        self._id = data["subtitleId"]
        self.release_info = data["version"]
        self.matches = set()

    def get_matches(self, video):
        self.matches = {"title", "series", "season", "episode", "tvdb_id"}

        update_matches(self.matches, video, self.release_info)

        return self.matches

    @property
    def id(self):
        return self._id


def _retry_on_423(method):
    def retry(self, *args, **kwargs):
        retries = 0
        while 3 > retries:
            try:
                return method(self, *args, **kwargs)
            except HTTPError as error:
                if error.response.status_code != 423:
                    raise

                retries += 1

                logger.debug("423 returned. Retrying in 30 seconds")
                time.sleep(30)

        logger.debug("Retries limit exceeded. Ignoring query")
        return []

    return retry


class GestdownProvider(Provider):
    provider_name = "gestdown"

    video_types = (Episode,)

    # fmt: off
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'aze', 'ben', 'bos', 'bul', 'cat', 'ces', 'dan', 'deu', 'ell', 'eng', 'eus', 'fas', 'fin', 'fra', 'glg',
        'heb', 'hrv', 'hun', 'hye', 'ind', 'ita', 'jpn', 'kor', 'mkd', 'msa', 'nld', 'nor', 'pol', 'por', 'ron', 'rus',
        'slk', 'slv', 'spa', 'sqi', 'srp', 'swe', 'tha', 'tur', 'ukr', 'vie', 'zho'
    ]} | {Language.fromietf(l) for l in ["sr-Latn", "sr-Cyrl"]}
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))
    # fmt: on

    _converter = PatchedAddic7edConverter()

    def initialize(self):
        self._session = Session()
        self._session.headers.update({"User-Agent": "Bazarr"})

    def terminate(self):
        self._session.close()

    def _subtitles_search(self, video, language: Language, show_id):
        lang = self._converter.convert(language.alpha3)
        response = self._session.get(f"{_BASE_URL}/subtitles/get/{show_id}/{video.season}/{video.episode}/{lang}")

        # TODO: implement rate limiting
        response.raise_for_status()

        matching_subtitles = response.json()["matchingSubtitles"]

        if not matching_subtitles:
            logger.debug("No episodes found for '%s' language", language)
            return None

        for subtitle_dict in matching_subtitles:
            if not subtitle_dict["completed"]:
                continue

            sub = GestdownSubtitle(language, subtitle_dict)
            logger.debug("Found subtitle: %s", sub)
            yield sub

    def _search_show(self, video):
        try:
            response = self._session.get(f"{_BASE_URL}/shows/external/tvdb/{video.series_tvdb_id}")
            response.raise_for_status()
            return response.json()["shows"]
        except HTTPError as error:
            if error.response.status_code == 404:
                return None
            raise


    @_retry_on_423
    def list_subtitles(self, video, languages):
        subtitles = []
        shows = self._search_show(video)
        if shows is None:
            logger.debug("Couldn't find the show")
            return subtitles

        for language in languages:
            try:
                for show in shows:
                    subs = list(self._subtitles_search(video, language, show["id"]))
                    if len(subs) > 0:
                        subtitles += subs
                        continue
            except HTTPError as error:
                if error.response.status_code == 404:
                    logger.debug("Couldn't find the show or its season/episode")
                    return []
                raise

        return subtitles

    def download_subtitle(self, subtitle: GestdownSubtitle):
        response = self._session.get(subtitle.page_link, allow_redirects=True)
        response.raise_for_status()
        subtitle.content = response.content
