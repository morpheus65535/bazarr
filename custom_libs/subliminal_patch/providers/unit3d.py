import logging
import os
from typing import ClassVar
from urllib.parse import urlsplit

from babelfish import language_converters
from guessit import guessit
from requests import Session
from requests.exceptions import ConnectionError, JSONDecodeError, SSLError, Timeout
from subliminal import Episode, Movie
from subliminal.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ProviderError,
    ServiceUnavailable,
)
from subliminal.subtitle import fix_line_ending
from subliminal_patch.exceptions import ForbiddenError, TooManyRequests
from subliminal_patch.providers import Provider, utils
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

API_PATH = "/api/subtitles"
PER_PAGE = 50
MAX_JSON_SIZE = 2 * 1024 * 1024
MAX_FILE_SIZE = 20 * 1024 * 1024

# Formats Bazarr can convert; UNIT3D also stores bitmap (.sup) subtitles which are skipped
_TEXT_FORMATS = {"srt", "ass", "ssa", "vtt"}
_ARCHIVE_FORMATS = {"zip"}
_PACKS = {"season", "series"}


class Unit3dSubtitle(Subtitle):
    provider_name = "unit3d"
    # A file of the same size or name in the subtitle's torrent is reported as a
    # hash match, which Bazarr validates against the other matches
    hash_verifiable = True
    hearing_impaired_verifiable = False

    def __init__(self, language, record, matched_by, download_path, page_link=None, wanted_season=None,
                 wanted_episode=None):
        hearing_impaired = record.get("hearing_impaired") is True
        if record.get("forced") is True:
            language = Language.rebuild(language, forced=True)

        super().__init__(language, hearing_impaired=hearing_impaired, page_link=page_link)
        self.subtitle_id = record["id"]
        self.download_path = download_path
        self.extension = record["extension"]
        self.filename = record.get("filename") or ""
        self.release_info = record["release"]
        uploader = record.get("uploader")
        self.uploader = uploader.strip()[:64] if isinstance(uploader, str) else None
        self.tmdb_id = record.get("tmdb_id")
        self.tvdb_id = record.get("tvdb_id")
        self.imdb_id = record.get("imdb_id")
        self.season = record.get("season")
        self.episode = record.get("episode")
        self.pack = record.get("pack")
        release_match = record.get("release_match") or {}
        self.release_match = release_match.get("file_size") is True or release_match.get("file_name") is True
        self.matched_by = matched_by
        # The episode to extract from a season or series pack archive
        self.wanted_season = wanted_season
        self.wanted_episode = wanted_episode
        if self.extension in _TEXT_FORMATS:
            self.format = self.extension

    @property
    def id(self):
        return f"{self.provider_name}_{self.subtitle_id}"

    def get_matches(self, video):
        matches = set()

        if isinstance(video, Episode):
            if self.tvdb_id and video.series_tvdb_id and str(self.tvdb_id) == str(video.series_tvdb_id):
                matches |= {"series", "year", "series_tvdb_id"}
            if self.imdb_id and video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches |= {"series", "year", "series_imdb_id"}
            if self.matched_by == "title":
                # UNIT3D only returns exact show name and first air year matches
                matches |= {"series", "year"}
            if self.pack == "series" or self.season == video.season:
                matches.add("season")
            # Pack archives are only used when they contain the wanted episode
            if self.pack in _PACKS or self.episode == video.episode:
                matches.add("episode")
        else:
            if self.tmdb_id and video.tmdb_id and str(self.tmdb_id) == str(video.tmdb_id):
                matches |= {"title", "year"}
            if self.imdb_id and video.imdb_id and self.imdb_id == video.imdb_id:
                matches |= {"imdb_id", "title", "year"}
            if self.matched_by == "title":
                # UNIT3D only returns exact title and year matches
                matches |= {"title", "year"}

        if self.release_match:
            matches.add("hash")

        utils.update_matches(matches, video, self.release_info)
        self.matches = matches
        return matches


class Unit3dProvider(Provider):
    """Subtitles uploaded to a UNIT3D private tracker, through its subtitle API."""

    provider_name = "unit3d"
    subtitle_class = Unit3dSubtitle
    video_types = (Episode, Movie)
    # UNIT3D languages are ISO 639-1 codes, without regional variants
    languages: ClassVar[set] = {
        Language.fromalpha2(code) for code in language_converters["alpha2"].codes
    }

    def __init__(self, url=None, api_key=None, match_files=True):
        self.base_url = self.normalize_url(url)
        if not api_key:
            raise ConfigurationError("UNIT3D API key is required")

        self._api_key = api_key
        # Send the video file size and name so UNIT3D can find its exact release
        self.match_files = match_files is not False
        self.session = None

    @staticmethod
    def normalize_url(url):
        if not url:
            raise ConfigurationError("UNIT3D URL is required")

        url = url.strip()
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigurationError("UNIT3D URL must begin with http:// or https://")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ConfigurationError(
                "UNIT3D URL cannot contain credentials, a query, or a fragment"
            )

        return url.rstrip("/")

    def initialize(self):
        self.session = Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "User-Agent": "Bazarr UNIT3D",
            }
        )

    def terminate(self):
        if self.session is not None:
            self.session.close()
            self.session = None

    def ping(self):
        try:
            self.status()
        except ProviderError:
            return False
        return True

    def status(self):
        payload = self._json(f"{API_PATH}/status", timeout=10)
        if payload.get("status") != "ok" or payload.get("provider") != "unit3d":
            raise ProviderError("The server does not provide the UNIT3D subtitle API")
        return payload

    def _get(self, path, params=None, timeout=30):
        if self.session is None:
            raise ProviderError("UNIT3D provider is not initialized")

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=timeout,
                allow_redirects=False,
            )
        except SSLError as error:
            raise ConfigurationError("UNIT3D TLS verification failed") from error
        except Timeout as error:
            logger.debug("UNIT3D connection failure: request timed out")
            raise ProviderError("UNIT3D request timed out") from error
        except ConnectionError as error:
            logger.debug("UNIT3D connection failure: server unreachable")
            raise ProviderError("UNIT3D is unreachable") from error

        status_code = response.status_code
        if status_code == 401:
            logger.debug("UNIT3D authentication failure")
            raise AuthenticationError("UNIT3D rejected the API key")
        if status_code == 403:
            raise ForbiddenError("UNIT3D denied access to this account")
        if status_code == 429:
            raise TooManyRequests("UNIT3D rate limit reached")
        if 300 <= status_code < 400:
            raise ConfigurationError(
                "UNIT3D redirected the request, check the URL (e.g. https:// and no trailing path)"
            )
        if status_code >= 500:
            raise ServiceUnavailable(f"UNIT3D returned HTTP {status_code}")
        return response

    def _json(self, path, params=None, timeout=30):
        response = self._get(path, params=params, timeout=timeout)

        if response.status_code == 404:
            raise ConfigurationError(
                "UNIT3D does not provide the subtitle API, it may need to be updated"
            )
        if response.status_code != 200:
            raise ProviderError(f"UNIT3D returned HTTP {response.status_code}")
        if len(response.content) > MAX_JSON_SIZE:
            raise ProviderError("UNIT3D response exceeded the size limit")

        try:
            payload = response.json()
        except (JSONDecodeError, ValueError) as error:
            raise ProviderError("UNIT3D returned malformed JSON") from error
        if not isinstance(payload, dict):
            raise ProviderError("UNIT3D returned an unexpected response")
        if set(payload) == {"message"}:
            # UNIT3D answers banned accounts with a bare message
            raise ForbiddenError("UNIT3D refused the request for this account")
        return payload

    @staticmethod
    def _is_int(value):
        return isinstance(value, int) and not isinstance(value, bool)

    @classmethod
    def _valid_record(cls, record, language_codes):
        if not isinstance(record, dict):
            return False

        record_id = record.get("id")
        if not cls._is_int(record_id) or record_id < 1:
            return False
        if record.get("language") not in language_codes:
            return False
        if not isinstance(record.get("extension"), str):
            return False
        if not isinstance(record.get("release"), str):
            return False
        if record.get("uploader") is not None and not isinstance(record["uploader"], str):
            return False
        for key in ("torrent_id", "tmdb_id", "tvdb_id", "season", "episode"):
            if record.get(key) is not None and not cls._is_int(record[key]):
                return False
        if record.get("pack") is not None and record["pack"] not in _PACKS:
            return False
        release_match = record.get("release_match")
        if release_match is not None and (
            not isinstance(release_match, dict)
            or any(value not in (True, False, None) for value in release_match.values())
        ):
            return False
        imdb_id = record.get("imdb_id")
        return imdb_id is None or isinstance(imdb_id, str)

    @staticmethod
    def _positive_id(value):
        value = str(value or "").strip()
        return int(value) if value.isdigit() and int(value) > 0 else None

    @staticmethod
    def _imdb_id(value):
        value = str(value or "").strip()
        return value if value.startswith("tt") and value[2:].isdigit() and int(value[2:]) > 0 else None

    @classmethod
    def _search_params(cls, video):
        if isinstance(video, Episode):
            episode = video.episode[0] if isinstance(video.episode, list) and video.episode else video.episode
            if not cls._is_int(video.season) or not cls._is_int(episode):
                return {}

            params = {"type": "episode", "season": video.season, "episode": episode}
            ids = {
                "tvdb_id": cls._positive_id(video.series_tvdb_id),
                "imdb_id": cls._imdb_id(video.series_imdb_id),
            }
            title = video.series
        else:
            params = {}
            ids = {
                "tmdb_id": cls._positive_id(video.tmdb_id),
                "imdb_id": cls._imdb_id(video.imdb_id),
            }
            title = video.title

        ids = {key: value for key, value in ids.items() if value is not None}
        if ids:
            params.update(ids)
        elif title and video.year:
            params.update({"title": title[:255], "year": video.year})
        else:
            return {}
        return params

    @classmethod
    def _file_params(cls, video):
        params = {}
        if cls._is_int(video.size) and video.size > 0:
            params["file_size"] = video.size
        file_name = os.path.basename(str(video.original_name or video.name or ""))
        if file_name and len(file_name) <= 255:
            params["file_name"] = file_name
        return params

    @staticmethod
    def _same_media(record, params):
        """Guard against records of another movie, show or episode."""
        if "type" in params:
            if record.get("type", "episode") != "episode":
                return False
            pack = record.get("pack")
            if pack is None and (record.get("season"), record.get("episode")) != (params["season"], params["episode"]):
                return False
            if pack == "season" and record.get("season") != params["season"]:
                return False
        elif record.get("type", "movie") != "movie":
            return False

        if "title" in params:
            return True
        return any(key in params and record.get(key) == params[key] for key in ("tmdb_id", "tvdb_id", "imdb_id"))

    def query(self, languages, video):
        language_codes = {}
        for language in languages:
            base_language = Language.rebuild(language, hi=False, forced=False)
            if base_language in self.languages:
                language_codes[base_language.alpha2] = base_language

        if not language_codes:
            return []

        params = self._search_params(video)
        if not params:
            logger.debug("UNIT3D search skipped: no id, or title and year")
            return []

        if self.match_files:
            params.update(self._file_params(video))
        params.update({"language": ",".join(sorted(language_codes)), "perPage": PER_PAGE})
        logger.debug("UNIT3D search: %s", params)

        payload = self._json(API_PATH, params=params)
        records = payload.get("data")
        if not isinstance(records, list):
            raise ProviderError("UNIT3D response is missing subtitles")

        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        matched_by = meta.get("matched_by")
        total = meta.get("total")
        if isinstance(total, int) and total > len(records):
            logger.debug("UNIT3D has %s subtitles, only the first %s are used", total, len(records))

        subtitles = []
        for record in records:
            if not self._valid_record(record, language_codes):
                logger.debug("Skipping malformed UNIT3D subtitle record")
                continue
            if not self._same_media(record, params):
                logger.debug("Skipping UNIT3D subtitle %s of another movie or episode", record["id"])
                continue

            extension = record["extension"].lower()
            if extension not in _TEXT_FORMATS | _ARCHIVE_FORMATS:
                logger.debug("Skipping UNIT3D subtitle %s in unsupported format %s", record["id"], extension)
                continue
            if record.get("pack") in _PACKS and extension not in _ARCHIVE_FORMATS:
                # The episode of a single file uploaded to a pack is unknown
                logger.debug("Skipping UNIT3D pack subtitle %s that is not an archive", record["id"])
                continue

            subtitle = Unit3dSubtitle(
                language_codes[record["language"]],
                {**record, "extension": extension},
                matched_by,
                f"{API_PATH}/{record['id']}/download",
                page_link=self._torrent_page(record.get("torrent_id")),
                wanted_season=params.get("season"),
                wanted_episode=params.get("episode"),
            )
            subtitle.get_matches(video)
            subtitles.append(subtitle)

        logger.debug("UNIT3D result count: %s", len(subtitles))
        return subtitles

    def _torrent_page(self, torrent_id):
        # Built from the configured URL, never taken from the response
        return f"{self.base_url}/torrents/{torrent_id}" if self._is_int(torrent_id) and torrent_id > 0 else None

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    @staticmethod
    def _episode_from_archive(archive, season, episode, forced=False):
        """Read the subtitle of an episode from a season or series pack archive."""
        for name in archive.namelist():
            base_name = os.path.basename(name)
            stem, extension = os.path.splitext(base_name.lower())
            if extension.lstrip(".") not in _TEXT_FORMATS:
                continue
            if not forced and stem.endswith("forced"):
                continue

            guess = guessit(base_name, {"type": "episode"})
            guessed_episodes = guess.get("episode")
            if not isinstance(guessed_episodes, list):
                guessed_episodes = [guessed_episodes]
            guessed_season = guess.get("season")
            if episode in guessed_episodes and guessed_season in (None, season):
                logger.debug("Using %s from UNIT3D pack archive", name)
                return archive.read(name)
        return None

    def download_subtitle(self, subtitle):
        logger.debug("UNIT3D download: subtitle %s", subtitle.subtitle_id)
        response = self._get(subtitle.download_path)

        if response.status_code == 404:
            raise ProviderError("UNIT3D subtitle is no longer available")
        if response.status_code != 200:
            raise ProviderError(f"UNIT3D download returned HTTP {response.status_code}")
        if "application/json" in response.headers.get("Content-Type", ""):
            raise ForbiddenError("UNIT3D refused the download for this account")
        if not response.content or len(response.content) > MAX_FILE_SIZE:
            raise ProviderError("UNIT3D returned an invalid subtitle file")

        if subtitle.extension in _ARCHIVE_FORMATS:
            archive = utils.get_archive_from_bytes(response.content)
            if archive is None:
                raise ProviderError("UNIT3D returned an invalid subtitle archive")
            if subtitle.pack in _PACKS:
                content = self._episode_from_archive(
                    archive, subtitle.wanted_season, subtitle.wanted_episode, forced=subtitle.language.forced
                )
            else:
                content = utils.get_subtitle_from_archive(archive, forced=subtitle.language.forced)
            if content is None:
                raise ProviderError("UNIT3D subtitle archive does not contain the wanted subtitle")
        else:
            content = response.content

        subtitle.content = fix_line_ending(content)


def check_connection(url, api_key):
    """Check the UNIT3D connection for the provider settings "Test" button.

    Returns a dict with ``status`` and either ``version`` or a user-friendly ``error``.
    """
    try:
        provider = Unit3dProvider(url, api_key)
        provider.initialize()
        try:
            info = provider.status()
        finally:
            provider.terminate()
    except (ConfigurationError, ProviderError) as error:
        logger.debug("UNIT3D connection test failed: %s", error)
        return {"status": False, "error": str(error)}

    permissions = info.get("permissions")
    if isinstance(permissions, dict):
        missing = [name for name in ("search", "download") if permissions.get(name) is not True]
        if missing:
            return {"status": False, "error": f"UNIT3D API key is missing the {' and '.join(missing)} permission"}

    version = info.get("version")
    return {"status": True, "version": f"UNIT3D {version}" if isinstance(version, str) else "UNIT3D"}
