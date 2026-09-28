import logging
from typing import ClassVar
from urllib.parse import urlsplit

from babelfish import language_converters
from requests import Session
from requests.exceptions import ConnectionError, JSONDecodeError, SSLError, Timeout
from subliminal import Movie
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


class Unit3dSubtitle(Subtitle):
    provider_name = "unit3d"
    hash_verifiable = False
    hearing_impaired_verifiable = False

    def __init__(self, language, record, matched_by, download_path):
        hearing_impaired = record.get("hearing_impaired") is True
        if record.get("forced") is True:
            language = Language.rebuild(language, forced=True)

        super().__init__(language, hearing_impaired=hearing_impaired)
        self.subtitle_id = record["id"]
        self.download_path = download_path
        self.extension = record["extension"]
        self.filename = record.get("filename") or ""
        self.release_info = record["release"]
        self.tmdb_id = record.get("tmdb_id")
        self.imdb_id = record.get("imdb_id")
        self.matched_by = matched_by
        if self.extension in _TEXT_FORMATS:
            self.format = self.extension

    @property
    def id(self):
        return f"{self.provider_name}_{self.subtitle_id}"

    def get_matches(self, video):
        matches = set()

        if self.tmdb_id and video.tmdb_id and str(self.tmdb_id) == str(video.tmdb_id):
            matches |= {"title", "year"}
        if self.imdb_id and video.imdb_id and self.imdb_id == video.imdb_id:
            matches |= {"imdb_id", "title", "year"}
        if self.matched_by == "title":
            # UNIT3D only returns exact title and year matches
            matches |= {"title", "year"}

        utils.update_matches(matches, video, self.release_info)
        self.matches = matches
        return matches


class Unit3dProvider(Provider):
    """Subtitles uploaded to a UNIT3D private tracker, through its subtitle API."""

    provider_name = "unit3d"
    subtitle_class = Unit3dSubtitle
    video_types = (Movie,)
    # UNIT3D languages are ISO 639-1 codes, without regional variants
    languages: ClassVar[set] = {
        Language.fromalpha2(code) for code in language_converters["alpha2"].codes
    }

    def __init__(self, url=None, api_key=None):
        self.base_url = self.normalize_url(url)
        if not api_key:
            raise ConfigurationError("UNIT3D API key is required")

        self._api_key = api_key
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
    def _valid_record(record, language_codes):
        if not isinstance(record, dict):
            return False

        record_id = record.get("id")
        if not isinstance(record_id, int) or isinstance(record_id, bool) or record_id < 1:
            return False
        if record.get("language") not in language_codes:
            return False
        if not isinstance(record.get("extension"), str):
            return False
        if not isinstance(record.get("release"), str):
            return False
        tmdb_id = record.get("tmdb_id")
        if tmdb_id is not None and (not isinstance(tmdb_id, int) or isinstance(tmdb_id, bool)):
            return False
        imdb_id = record.get("imdb_id")
        return imdb_id is None or isinstance(imdb_id, str)

    @staticmethod
    def _search_params(video):
        tmdb_id = str(video.tmdb_id or "").strip()
        imdb_id = str(video.imdb_id or "").strip()

        params = {}
        if tmdb_id.isdigit() and int(tmdb_id) > 0:
            params["tmdb_id"] = int(tmdb_id)
        if imdb_id.startswith("tt") and imdb_id[2:].isdigit() and int(imdb_id[2:]) > 0:
            params["imdb_id"] = imdb_id
        if not params and video.title and video.year:
            params.update({"title": video.title[:255], "year": video.year})
        return params

    @staticmethod
    def _same_movie(record, params):
        """Guard against records of another movie when searching by id."""
        if "tmdb_id" in params and record.get("tmdb_id") == params["tmdb_id"]:
            return True
        if "imdb_id" in params and record.get("imdb_id") == params["imdb_id"]:
            return True
        return "title" in params

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
            logger.debug("UNIT3D search skipped: no TMDB id, IMDb id or title and year")
            return []

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
            if not self._same_movie(record, params):
                logger.debug("Skipping UNIT3D subtitle %s of another movie", record["id"])
                continue

            extension = record["extension"].lower()
            if extension not in _TEXT_FORMATS | _ARCHIVE_FORMATS:
                logger.debug("Skipping UNIT3D subtitle %s in unsupported format %s", record["id"], extension)
                continue

            subtitle = Unit3dSubtitle(
                language_codes[record["language"]],
                {**record, "extension": extension},
                matched_by,
                f"{API_PATH}/{record['id']}/download",
            )
            subtitle.get_matches(video)
            subtitles.append(subtitle)

        logger.debug("UNIT3D result count: %s", len(subtitles))
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

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
            content = utils.get_subtitle_from_archive(archive, forced=subtitle.language.forced)
            if content is None:
                raise ProviderError("UNIT3D subtitle archive contains no subtitle")
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
