import io
import re
from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from requests import Session
import logging
from guessit import guessit
from subliminal.exceptions import ConfigurationError
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.video import Episode, Movie
from subzero.language import Language
from subliminal_patch.exceptions import APIThrottled, TooManyRequests

logger = logging.getLogger(__name__)

class SubsRoSubtitle(Subtitle):
    provider_name = "subsro"
    hash_verifiable = False

    def __init__(self, language, title, download_link, imdb_id, is_episode=False, episode_number=None, year=None, release_info=None, season=None, sub_id=None):
        super().__init__(language)
        self.title = title
        self.page_link = download_link
        self.imdb_id = imdb_id
        self.matches = set()
        self.asked_for_episode = is_episode
        self.episode = episode_number
        self.year = year
        self.release_info = self.releases = release_info
        self.season = season
        self.sub_id = sub_id

    @property
    def id(self):
        return self.sub_id or self.page_link

    def get_matches(self, video):
        matches = set()
        if video.year and self.year == video.year:
            matches.add("year")
        if isinstance(video, Movie):
            if video.title:
                matches.add("title")
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add("imdb_id")
            matches |= guess_matches(
                video,
                guessit(f"{self.title} {self.season or ''} {self.year or ''} {self.release_info or ''}", {"type": "movie"}),
            )
        else:
            if video.series:
                matches.add("series")
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add("imdb_id")
            if video.season == self.season:
                matches.add("season")
            if {"imdb_id", "season"}.issubset(matches):
                matches.add("episode")
            matches |= guess_matches(
                video,
                guessit(f"{self.title} {self.year or ''} {self.release_info or ''}", {"type": "episode"}),
            )
        self.matches = matches
        return matches


class SubsRoProvider(Provider, ProviderSubtitleArchiveMixin):
    languages = {Language(lang) for lang in ["ron", "eng"]}
    video_types = (Episode, Movie)
    hash_verifiable = False

    def __init__(self, api_key=None):
        if not api_key:
            raise ConfigurationError("SubsRo requires an API Key.")
        self.api_keys = [k.strip() for k in api_key.split(",") if k.strip()]
        self.current_key_index = 0
        self.session = None

    def initialize(self):
        self.session = Session()
        self.base_url = "https://api.subs.ro/v1.0"
        self.session.headers.update({"Accept": "application/json"})
        self._update_api_key_header()

    def _update_api_key_header(self):
        current_key = self.api_keys[self.current_key_index]
        self.session.headers.update({"X-Subs-Api-Key": current_key})

    def terminate(self):
        self.session.close()

    @classmethod
    def check(cls, video):
        return isinstance(video, (Episode, Movie))

    def query(self, language, imdb_id, video):
        logger.info("Querying SubsRo API for %s subtitles of %s", language, imdb_id)
        if not imdb_id:
            return []

        lang_code = "ro" if language.alpha3 == "ron" else "en"
        url = f"{self.base_url}/search/imdbid/{imdb_id}"
        params = {"language": lang_code}

        response = self._request("get", url, params=params)

        try:
            data = response.json()
        except ValueError:
            logger.error("SubsRo: Invalid JSON response")
            return []

        if data.get("status") != 200:
            logger.warning("SubsRo API returned status %s", data.get("status"))
            return []

        results = []
        items = data.get("items", [])

        for item in items:
            sub_id = item.get("id")
            title = item.get("title")
            year = item.get("year")
            release_info = item.get("description", "")
            download_link = item.get("downloadLink")

            season = None
            if title:
                t_match = re.search(r"[Ss]ezon(?:ul)?\s*(\d{1,2})", title)
                if t_match:
                    season = int(t_match.group(1))
            if season is None and release_info:
                s_match = re.search(r"[Ss]ezon(?:ul)?\s*(\d{1,2})|[Ss](\d{1,2})[Ee]\d+", release_info)
                if s_match:
                    season = int(next(g for g in s_match.groups() if g is not None))

            episode_number = video.episode if isinstance(video, Episode) else None

            if download_link and title:
                results.append(
                    SubsRoSubtitle(
                        language, title, download_link, f"tt{imdb_id}",
                        isinstance(video, Episode), episode_number, year, release_info, season, sub_id
                    )
                )
        return results

    def list_subtitles(self, video, languages):
        imdb_id = None
        try:
            if isinstance(video, Episode):
                imdb_id = video.series_imdb_id[2:]
            else:
                imdb_id = video.imdb_id[2:]
        except Exception:
            logger.error(f"Error parsing imdb_id from video object {video}")

        subtitles = [s for lang in languages for s in self.query(lang, imdb_id, video)]
        return subtitles

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle archive from SubsRo API: %s", subtitle.page_link)
        response = self._request("get", subtitle.page_link)
        archive_stream = io.BytesIO(response.content)

        if is_rarfile(archive_stream):
            archive = RarFile(archive_stream)
        elif is_zipfile(archive_stream):
            archive = ZipFile(archive_stream)
        else:
            if subtitle.is_valid():
                subtitle.content = response.content
                return True
            else:
                subtitle.content = None
                return False

        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)
        return True

    def _request(self, method, url, **kwargs):
        attempts = 0
        max_attempts = len(self.api_keys)

        while attempts < max_attempts:
            try:
                response = self.session.request(method, url, **kwargs)
            except Exception as e:
                logger.error("SubsRo request error: %s", e)
                raise APIThrottled(f"SubsRo request failed: {e}")

            if response.status_code == 429:
                logger.warning("SubsRo: API Key #%d hit the rate limit (HTTP 429).", self.current_key_index + 1)
                attempts += 1
                if attempts < max_attempts:
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    logger.info("SubsRo: Switching to API Key #%d and retrying...", self.current_key_index + 1)
                    self._update_api_key_header()
                    continue
                else:
                    logger.error("SubsRo: All provided API keys have reached their rate limit.")
                    raise TooManyRequests("SubsRo: Too many requests (All keys exhausted)")

            if response.status_code == 401:
                logger.error("SubsRo: Unauthorized (401). API Key #%d is invalid.", self.current_key_index + 1)
                raise ValueError(f"SubsRo: Invalid API Key (Key #{self.current_key_index + 1})")

            if response.status_code >= 500:
                logger.warning("SubsRo: Server error %s for %s", response.status_code, url)
                raise APIThrottled(f"SubsRo: Server error {response.status_code}")

            return response
