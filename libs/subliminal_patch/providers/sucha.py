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

server_url = "http://sapidb.caretas.club/"
page_url = "https://sucha.caretas.club/"


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
            language, hearing_impaired=False, page_link=page_url
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
            q = {
                "query": "{} S{:02}E{:02}".format(
                    video.series, video.season, video.episode
                )
            }
        else:
            q = {"query": video.title, "year": movie_year}
        logger.debug("Searching subtitles: {}".format(q["query"]))
        res = self.session.get(
            server_url + ("episode" if is_episode else "movie"), params=q, timeout=10
        )
        res.raise_for_status()
        result = res.json()

        try:
            subtitles = []
            for i in result:
                matches = set()
                if (
                    video.title.lower() in i["title"].lower()
                    or video.title.lower() in i["alt_title"].lower()
                ):
                    matches.add("title")
                if is_episode:
                    if (
                        q["query"].lower() in i["title"].lower()
                        or q["query"].lower() in i["alt_title"].lower()
                    ):
                        matches.add("title")
                        matches.add("series")
                        matches.add("season")
                        matches.add("episode")
                        matches.add("year")
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
        except KeyError:
            logger.debug("No subtitles found")
            return []

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def _check_response(self, response):
        if response.status_code != 200:
            raise ServiceUnavailable("Bad status code: " + str(response.status_code))

    def _get_archive(self, content):
        archive_stream = io.BytesIO(content)
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Identified rar archive")
            archive = rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
        else:
            raise APIThrottled("Unsupported compressed format")
        return archive

    def get_file(self, archive):
        for name in archive.namelist():
            if os.path.split(name)[-1].startswith("."):
                continue
            if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                continue
            if (
                "[eng]" in name.lower()
                or ".en." in name.lower()
                or ".eng." in name.lower()
            ):
                continue
            logger.debug("Returning from archive: {}".format(name))
            return archive.read(name)
        raise APIThrottled("Can not find the subtitle in the compressed file")

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle %r", subtitle)
        response = self.session.get(
            server_url + "download",
            params={"id": subtitle.download_id, "type": subtitle.download_type},
            timeout=10,
        )
        response.raise_for_status()
        self._check_response(response)
        archive = self._get_archive(response.content)
        subtitle_file = self.get_file(archive)
        subtitle.content = fix_line_ending(subtitle_file)
