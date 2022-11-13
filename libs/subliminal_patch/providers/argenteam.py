# coding=utf-8
from __future__ import absolute_import

from json import JSONDecodeError
import logging
import os
import urllib.parse

from requests import Session
from subliminal import Episode
from subliminal import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

BASE_URL = "https://argenteam.net"
API_URL = f"{BASE_URL}/api/v1"

logger = logging.getLogger(__name__)


class ArgenteamSubtitle(Subtitle):
    provider_name = "argenteam"
    hearing_impaired_verifiable = False

    def __init__(self, language, page_link, download_link, release_info, matches):
        super(ArgenteamSubtitle, self).__init__(language, page_link=page_link)

        self._found_matches = matches

        self.page_link = page_link
        self.download_link = download_link
        self.release_info = release_info

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        update_matches(self._found_matches, video, self.release_info)

        return self._found_matches


class ArgenteamProvider(Provider, ProviderSubtitleArchiveMixin):
    provider_name = "argenteam"

    languages = {Language("spa", "MX")}
    video_types = (Episode, Movie)
    subtitle_class = ArgenteamSubtitle

    _default_lang = Language("spa", "MX")

    def __init__(self):
        self.session = Session()

    def initialize(self):
        self.session.headers.update(
            {"User-Agent": os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        )

    def terminate(self):
        self.session.close()

    def query(self, video):
        is_episode = isinstance(video, Episode)
        imdb_id = video.series_imdb_id if is_episode else video.imdb_id

        if not imdb_id:
            logger.debug("%s doesn't have IMDB ID. Can't search")
            return []

        if is_episode:
            argenteam_ids = self._search_ids(
                imdb_id, season=video.season, episode=video.episode
            )
        else:
            argenteam_ids = self._search_ids(imdb_id)

        if not argenteam_ids:
            logger.debug("No IDs found")
            return []

        return self._parse_subtitles(argenteam_ids, is_episode)

    def _parse_subtitles(self, ids, is_episode=True):
        movie_kind = "episode" if is_episode else "movie"

        subtitles = []

        for aid in ids:
            response = self.session.get(
                f"{API_URL}/{movie_kind}", params={"id": aid}, timeout=10
            )
            response.raise_for_status()

            try:
                content = response.json()
            except JSONDecodeError:
                continue

            if not content or not content.get("releases"):
                continue

            for r in content["releases"]:
                for s in r["subtitles"]:
                    page_link = f"{BASE_URL}/{movie_kind}/{aid}"

                    release_info = self._combine_release_info(r, s)

                    logger.debug("Got release info: %s", release_info)

                    download_link = s["uri"].replace("http://", "https://")

                    # Already matched within query
                    if is_episode:
                        matches = {"series", "title", "season", "episode", "imdb_id"}
                    else:
                        matches = {"title", "year", "imdb_id"}

                    subtitles.append(
                        ArgenteamSubtitle(
                            self._default_lang,
                            page_link,
                            download_link,
                            release_info,
                            matches,
                        )
                    )

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video)

    def download_subtitle(self, subtitle):
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        archive = get_archive_from_bytes(r.content)
        subtitle.content = get_subtitle_from_archive(archive)

    def _search_ids(self, identifier, **kwargs):
        """
        :param identifier: imdb_id or title (without year)
        """
        identifier = identifier.lstrip("tt")

        query = identifier
        if kwargs.get("season") and kwargs.get("episode"):
            query = f"{identifier} S{kwargs['season']:02}E{kwargs['episode']:02}"

        logger.debug("Searching ID for %s", query)

        r = self.session.get(f"{API_URL}/search", params={"q": query}, timeout=10)
        r.raise_for_status()

        try:
            results = r.json()
        except JSONDecodeError:
            return []

        if not results.get("results"):
            return []

        match_ids = [result["id"] for result in results["results"]]
        logger.debug("Found matching IDs: %s", match_ids)

        return match_ids

    def _combine_release_info(self, release_dict, subtitle_dict):
        releases = [
            urllib.parse.unquote(subtitle_dict.get("uri", "Unknown").split("/")[-1])
        ]

        combine = [
            release_dict.get(key)
            for key in ("source", "codec", "tags")
            if release_dict.get(key)
        ]

        if combine:
            r_info = ".".join(combine)
            if release_dict.get("team"):
                r_info += f"-{release_dict['team']}"

            releases.append(r_info)

        return "\n".join(releases)
