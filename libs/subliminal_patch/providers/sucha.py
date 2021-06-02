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

SERVER_URL = "http://sapidb.caretas.club"
PAGE_URL = "https://sucha.caretas.club"
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
        type_ = "episode" if isinstance(video, Episode) else "movie"
        self.found_matches |= guess_matches(
            video,
            guessit(self.filename, {"type": type_}),
        )
        self.found_matches |= guess_matches(
            video,
            guessit(self.guessed_release_info, {"type": type_}),
        )
        return self.found_matches


class SuchaProvider(Provider):
    """Sucha Provider"""

    # This is temporary. Castilian spanish subtitles may exist, but are rare
    # and currently impossible to guess from the API.
    languages = {Language("spa", "MX")}
    language_list = list(languages)
    video_types = (Episode, Movie)

    def initialize(self):
        self.session = Session()
        self.session.headers.update(
            {"User-Agent": os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        )

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        movie_year = video.year or "0"
        is_episode = isinstance(video, Episode)
        type_str = "episode" if is_episode else "movie"
        language = self.language_list[0]

        if is_episode:
            q = {"query": f"{video.series} S{video.season:02}E{video.episode:02}"}
        else:
            q = {"query": video.title, "year": movie_year}

        logger.debug(f"Searching subtitles: {q}")
        result = self.session.get(f"{SERVER_URL}/{type_str}", params=q, timeout=10)
        result.raise_for_status()

        results = result.json()
        subtitles = []
        for item in results:
            matches = set()
            title = item.get("title", "").lower()
            alt_title = item.get("alt_title", title).lower()
            if not title:
                logger.debug("No subtitles found")
                return []

            if any(video.title.lower() in item for item in (title, alt_title)):
                matches.add("title")

            if str(item["year"]) == video.year:
                matches.add("year")

            if is_episode and any(
                q["query"].lower() in item for item in (title, alt_title)
            ):
                matches.update("title", "series", "season", "episode", "year")

            subtitles.append(
                SuchaSubtitle(
                    language,
                    item["release"],
                    item["filename"],
                    str(item["id"]),
                    type_str,
                    matches,
                )
            )
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

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
            f"{SERVER_URL}/download",
            params={"id": subtitle.download_id, "type": subtitle.download_type},
            timeout=10,
        )
        response.raise_for_status()
        archive = self._get_archive(response.content)
        subtitle_file = self.get_file(archive)
        subtitle.content = fix_line_ending(subtitle_file)
