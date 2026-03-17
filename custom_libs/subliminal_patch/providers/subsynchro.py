# -*- coding: utf-8 -*-
import io
import logging
import os

from zipfile import ZipFile, is_zipfile
from requests import Session
from guessit import guessit
from requests.exceptions import JSONDecodeError

from subliminal import Movie
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language

logger = logging.getLogger(__name__)

SERVER_URL = "https://www.subsynchro.com/include/ajax/subMarin.php"
PAGE_URL = "https://www.subsynchro.com"


class SubsynchroSubtitle(Subtitle):
    provider_name = "subsynchro"
    hash_verifiable = False

    def __init__(
        self,
        language,
        release_info,
        filename,
        download_url,
        file_type,
        matches,
    ):
        super(SubsynchroSubtitle, self).__init__(
            language, hearing_impaired=False, page_link=download_url
        )
        self.download_url = download_url
        self.file_type = file_type
        self.release_info = release_info
        self.filename = filename
        self.release_info = (
            release_info if len(release_info) > len(filename) else filename
        )
        self.matches = matches or set()

    @property
    def id(self):
        return self.download_url

    def get_matches(self, video):
        self.matches |= guess_matches(
            video,
            guessit(
                self.filename,
            ),
        )
        self.matches |= guess_matches(
            video,
            guessit(
                self.release_info,
            ),
        )
        return self.matches


class SubsynchroProvider(Provider):
    """Subsynchro Provider"""

    languages = {Language.fromalpha2(l) for l in ["fr"]}
    language_list = list(languages)
    video_types = (Movie,)

    def initialize(self):
        self.session = Session()
        self.session.headers = {"User-Agent": "Bazarr", "Referer": PAGE_URL}

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        language = self.language_list[0]

        params = {"title": video.title, "year": video.year}

        logger.debug("Searching subtitles from params: %s", params)

        result = self.session.get(SERVER_URL, params=params, timeout=10)
        result.raise_for_status()

        subtitles = []

        try:
            results = result.json()
        except JSONDecodeError:
            results = {}

        status_ = results.get("status")

        if status_ != 200:
            logger.debug(f"No subtitles found (status {status_})")
            return subtitles

        for i in results.get("data", []):
            matches = set()
            if any(
                video.title.lower() in title.lower()
                for title in (i.get("titre", "n/a"), i.get("titre_original", "n/a"))
            ):
                # Year is already set on query
                matches.update(["title", "year"])

            subtitles.append(
                SubsynchroSubtitle(
                    language,
                    i.get("release", "n/a"),
                    i.get("filename", "n/a"),
                    i.get("telechargement"),
                    i.get("fichier"),
                    matches,
                )
            )
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def get_file(self, archive):
        for name in archive.namelist():
            if os.path.split(name)[-1].startswith("."):
                continue

            if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                continue

            logger.debug(f"Returning from archive: {name}")
            return archive.read(name)

        raise APIThrottled("Can not find the subtitle in the zip file")

    def download_subtitle(self, subtitle):
        logger.debug(f"Downloading subtitle {subtitle.download_url}")

        response = self.session.get(
            subtitle.download_url, allow_redirects=True, timeout=10
        )
        response.raise_for_status()

        stream = io.BytesIO(response.content)
        if is_zipfile(stream):
            logger.debug("Zip file found")
            subtitle_ = self.get_file(ZipFile(stream))
            subtitle.content = fix_line_ending(subtitle_)
        else:
            raise APIThrottled(f"Unknown file type: {subtitle.download_url}")
