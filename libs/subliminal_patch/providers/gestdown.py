# -*- coding: utf-8 -*-

import logging

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

    def __init__(self, language, data: dict):
        super().__init__(language, hearing_impaired=data["hearingImpaired"])
        self.page_link = _BASE_URL + data["downloadUri"]
        self._id = data["subtitleId"]
        self.release_info = data["version"]
        self._matches = {"title", "series", "season", "episode"}

    def get_matches(self, video):
        update_matches(self._matches, video, self.release_info)

        return self._matches

    @property
    def id(self):
        return self._id


class GestdownProvider(Provider):
    provider_name = "gestdown"

    video_types = (Episode,)
    subtitle_class = GestdownSubtitle

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

    def _subtitles_search(self, video, language: Language):

        logger.debug("Post data: %s", json_data)
        lang = self._converter.convert(language.alpha3)
        response = self._session.get(f"{_BASE_URL}/subtitles/find/{lang}/{video.series}/{video.season}/{video.episode}")

        # TODO: implement rate limiting
        response.raise_for_status()

        matching_subtitles = response.json()["matchingSubtitles"]

        if not matching_subtitles:
            logger.debug("No episodes found for '%s' language", language)
            return None

        for subtitle_dict in matching_subtitles:
            sub = GestdownSubtitle(language, subtitle_dict)
            logger.debug("Found subtitle: %s", sub)
            yield sub

    def list_subtitles(self, video, languages):
        subtitles = []
        for language in languages:
            try:
                subtitles += self._subtitles_search(video, language)
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
