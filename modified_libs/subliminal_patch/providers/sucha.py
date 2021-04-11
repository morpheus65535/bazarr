# -*- coding: utf-8 -*-
import io
import logging
import os
import zipfile

import rarfile
from requests import Session
from guessit import guessit
from subliminal import Episode, Movie
from subliminal.exceptions import ServiceUnavailable
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language

logger = logging.getLogger(__name__)

SERVER_URL = "http://sapidb.caretas.club/"
PAGE_URL = "https://sucha.caretas.club/"
UNDESIRED_FILES = ("[eng]", ".en.", ".eng.", ".fr.", ".pt.")


class SuchaSubtitle(Subtitle):
    provider_name = "sucha"
    hash_verifiable = False

    def __init__(
        self,
        language,
        release_info,
        filename,
        download_id,
        download_type,
        matches,
    ):
        super(SuchaSubtitle, self).__init__(
            language, hearing_impaired=False, page_link=PAGE_URL
        )
        self.download_id = download_id
        self.download_type = download_type
        self.language = language
        self.guessed_release_info = release_info
        self.filename = filename
        self.release_info = (
            release_info if len(release_info) > len(filename) else filename
        )
        self.found_matches = matches

    @property
    def id(self):
        return self.download_id

    def get_matches(self, video):
        self.found_matches |= guess_matches(
            video,
            guessit(
                self.filename,
                {"type": "episode" if isinstance(video, Episode) else "movie"},
            ),
        )
        self.found_matches |= guess_matches(
            video,
            guessit(
                self.guessed_release_info,
                {"type": "episode" if isinstance(video, Episode) else "movie"},
            ),
        )
        return self.found_matches


class SuchaProvider(Provider):
    """Sucha Provider"""
    languages = {Language.fromalpha2(l) for l in ["es"]}
    language_list = list(languages)
    video_types = (Episode, Movie)

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            "User-Agent": os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")
        }

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        movie_year = video.year if video.year else "0"
        is_episode = isinstance(video, Episode)
        language = self.language_list[0]

        if is_episode:
            q = {"query": f"{video.series} S{video.season:02}E{video.episode:02}"}
        else:
            q = {"query": video.title, "year": movie_year}

        logger.debug(f"Searching subtitles: {q}")
        result = self.session.get(
            SERVER_URL + ("episode" if is_episode else "movie"), params=q, timeout=10
        )
        result.raise_for_status()

        result_ = result.json()
        subtitles = []
        for i in result_:
            matches = set()
            try:
                if (
                    video.title.lower() in i["title"].lower()
                    or video.title.lower() in i["alt_title"].lower()
                ):
                    matches.add("title")
            except TypeError:
                logger.debug("No subtitles found")
                return []

            if is_episode:
                if (
                    q["query"].lower() in i["title"].lower()
                    or q["query"].lower() in i["alt_title"].lower()
                ):
                    matches_ = ("title", "series", "season", "episode", "year")
                    [matches.add(match) for match in matches_]

            if str(i["year"]) == video.year:
                matches.add("year")

            subtitles.append(
                SuchaSubtitle(
                    language,
                    i["release"],
                    i["filename"],
                    str(i["id"]),
                    "episode" if is_episode else "movie",
                    matches,
                )
            )
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def _check_response(self, response):
        if response.status_code != 200:
            raise ServiceUnavailable(f"Bad status code: {response.status_code}")

    def _get_archive(self, content):
        archive_stream = io.BytesIO(content)

        if rarfile.is_rarfile(archive_stream):
            logger.debug("Identified rar archive")
            return rarfile.RarFile(archive_stream)

        if zipfile.is_zipfile(archive_stream):
            logger.debug("Identified zip archive")
            return zipfile.ZipFile(archive_stream)

        raise APIThrottled("Unsupported compressed format")

    def get_file(self, archive):
        for name in archive.namelist():
            if os.path.split(name)[-1].startswith("."):
                continue

            if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                continue

            if any(undesired in name.lower() for undesired in UNDESIRED_FILES):
                continue

            logger.debug(f"Returning from archive: {name}")
            return archive.read(name)

        raise APIThrottled("Can not find the subtitle in the compressed file")

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle %r", subtitle)
        response = self.session.get(
            SERVER_URL + "download",
            params={"id": subtitle.download_id, "type": subtitle.download_type},
            timeout=10,
        )
        response.raise_for_status()
        self._check_response(response)
        archive = self._get_archive(response.content)
        subtitle_file = self.get_file(archive)
        subtitle.content = fix_line_ending(subtitle_file)
