# -*- coding: utf-8 -*-
import logging

from requests import Session
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)


class ArgenteamSubtitle(Subtitle):
    provider_name = "argenteam_dump"
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, rel_path, release_info, matches=None):
        super().__init__(language, hearing_impaired=language.hi)
        self.release_info = release_info
        self.rel_path = rel_path
        self._matches = matches or set()

    def get_matches(self, video):
        update_matches(self._matches, video, self.release_info)
        return self._matches

    @property
    def id(self):
        return f"{self.provider_name}_{self.rel_path}"


_BASE_URL = "https://argt.caretas.club"


class ArgenteamDumpProvider(Provider):
    provider_name = "argenteam_dump"

    video_types = (Movie, Episode)
    subtitle_class = ArgenteamSubtitle

    languages = {Language("spa", "MX")}
    _language = Language("spa", "MX")

    def __init__(self) -> None:
        self._session = Session()
        self._session.headers.update({"User-Agent": "Bazarr"})

    def initialize(self):
        pass

    def terminate(self):
        self._session.close()

    def list_subtitles(self, video, languages):
        episode = None
        if isinstance(video, Movie):
            params = {"query": video.title}
            matches = {"title"}
            endpoint = f"{_BASE_URL}/search/movies/"
        else:
            params = {
                "query": video.series,
                "season": video.season,
                "episode": video.episode,
            }
            matches = {"tvdb_id", "imdb_id", "series", "title", "episode", "season"}
            endpoint = f"{_BASE_URL}/search/episodes/"

        response = self._session.get(endpoint, params=params)
        response.raise_for_status()
        items = response.json()
        if not items:
            return []

        subs = []
        for item in items:
            subs.append(
                ArgenteamSubtitle(
                    self._language, item["rel_path"], item["release_info"], matches
                )
            )

        return subs

    def download_subtitle(self, subtitle):
        response = self._session.get(
            f"{_BASE_URL}/download/", params={"rel_path": subtitle.rel_path}
        )
        response.raise_for_status()
        archive = get_archive_from_bytes(response.content)
        subtitle.content = get_subtitle_from_archive(archive)
