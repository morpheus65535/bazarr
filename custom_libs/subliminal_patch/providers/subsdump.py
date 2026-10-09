import logging
from typing import ClassVar
from urllib.parse import urlsplit

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
from subliminal_patch.providers import Provider, utils
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

_LANGUAGE_CODES = {
    "ara",
    "aze",
    "bel",
    "ben",
    "bos",
    "bul",
    "cat",
    "ces",
    "dan",
    "deu",
    "ell",
    "eng",
    "epo",
    "est",
    "eus",
    "fas",
    "fin",
    "fra",
    "heb",
    "hin",
    "hrv",
    "hun",
    "hye",
    "ind",
    "isl",
    "ita",
    "jpn",
    "kal",
    "kan",
    "kat",
    "khm",
    "kin",
    "kor",
    "kur",
    "lav",
    "lit",
    "mal",
    "mkd",
    "mni",
    "mon",
    "msa",
    "mya",
    "nep",
    "nld",
    "nor",
    "pan",
    "pol",
    "por",
    "pus",
    "ron",
    "rus",
    "sin",
    "slk",
    "slv",
    "som",
    "spa",
    "sqi",
    "srp",
    "sun",
    "swa",
    "swe",
    "tam",
    "tel",
    "tgl",
    "tha",
    "tur",
    "ukr",
    "urd",
    "vie",
    "yor",
    "zho",
}


class SubsDumpSubtitle(Subtitle):
    provider_name = "subsdump"
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, record, content_path, page_link):
        super().__init__(
            language,
            hearing_impaired=bool(record.get("hearing_impaired")),
            page_link=page_link,
        )
        self.record_id = record["id"]
        self.content_path = content_path
        self.title = record["media"]["title"]
        self.imdb_id = record["media"].get("imdb_id")
        self.year = record["media"].get("year")
        self.season = record["media"].get("season")
        self.episode = record["media"].get("episode")
        self.releases = record.get("releases") or []
        self.release_info = ", ".join(self.releases)
        self.uploader = record.get("uploader")
        self.matches = set()

    @property
    def id(self):
        return self.record_id

    def get_matches(self, video):
        matches = set()
        if isinstance(video, Episode):
            if self.title and video.series and self.title.casefold() == video.series.casefold():
                matches.add("series")
            if self.season == video.season:
                matches.add("season")
            if self.episode == video.episode:
                matches.add("episode")
        else:
            if self.title and video.title and self.title.casefold() == video.title.casefold():
                matches.add("title")
            if self.year and self.year == video.year:
                matches.add("year")

        utils.update_matches(matches, video, self.releases)
        self.matches = matches
        return matches


class SubsDumpProvider(Provider):
    provider_name = "subsdump"
    subtitle_class = SubsDumpSubtitle
    video_types = (Episode, Movie)
    languages: ClassVar[set] = {Language(code) for code in _LANGUAGE_CODES}
    languages.add(Language("por", "BR"))
    languages.update(Language.rebuild(language, hi=True) for language in list(languages))

    def __init__(self, base_url=None, api_key=None):
        if not base_url:
            raise ConfigurationError("SubsDump Base URL is required")

        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigurationError("SubsDump Base URL must begin with http:// or https://")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ConfigurationError(
                "SubsDump Base URL cannot contain credentials, a query, or a fragment"
            )

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers.update(
            {"Accept": "application/json", "User-Agent": "Bazarr SubsDump"}
        )
        if self.api_key:
            self.session.headers["X-API-Key"] = self.api_key

        try:
            info = self._json("/api/v1/info", timeout=10)
            if info.get("name") != "SubsDump" or info.get("api_version") != "v1":
                raise ConfigurationError("The server does not provide the SubsDump v1 API")
        except Exception:
            self.terminate()
            raise

    def terminate(self):
        if self.session is not None:
            self.session.close()
            self.session = None

    def ping(self):
        try:
            info = self._json("/api/v1/info", timeout=10)
            return info.get("name") == "SubsDump" and info.get("api_version") == "v1"
        except ProviderError:
            return False

    def _json(self, path, params=None, timeout=30):
        if self.session is None:
            raise ProviderError("SubsDump provider is not initialized")

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=timeout,
                allow_redirects=False,
            )
        except SSLError as error:
            raise ConfigurationError("SubsDump TLS verification failed") from error
        except Timeout as error:
            raise ProviderError("SubsDump request timed out") from error
        except ConnectionError as error:
            raise ProviderError("SubsDump is unreachable") from error

        if response.status_code in {401, 403}:
            raise AuthenticationError("SubsDump rejected the API key")
        if response.status_code == 503:
            raise ServiceUnavailable("SubsDump is not ready")
        if response.status_code != 200:
            raise ProviderError(f"SubsDump returned HTTP {response.status_code}")
        if len(response.content) > 2 * 1024 * 1024:
            raise ProviderError("SubsDump response exceeded the size limit")

        try:
            payload = response.json()
        except (JSONDecodeError, ValueError) as error:
            raise ProviderError("SubsDump returned malformed JSON") from error
        if not isinstance(payload, dict):
            raise ProviderError("SubsDump returned an unexpected response")
        return payload

    @staticmethod
    def _language_code(language):
        if language.alpha3 == "por" and language.country == "BR":
            return "por-BR"
        return language.alpha3

    @staticmethod
    def _valid_record(record, requested_language):
        if not isinstance(record, dict):
            return False

        record_id = record.get("id")
        media = record.get("media")
        language = record.get("language")
        links = record.get("links")
        releases = record.get("releases")
        if not isinstance(record_id, int) or isinstance(record_id, bool) or record_id < 1:
            return False
        if not isinstance(media, dict) or not isinstance(media.get("title"), str):
            return False
        if not isinstance(language, dict) or language.get("code") != requested_language:
            return False
        if not isinstance(releases, list) or not all(isinstance(item, str) for item in releases):
            return False
        if not isinstance(links, dict):
            return False
        return (
            links.get("page") == f"/subtitles/{record_id}"
            and links.get("content") == f"/api/v1/subtitles/{record_id}/content"
        )

    def _query_language(self, video, language):
        language_code = self._language_code(language)
        params = {"language": language_code, "per_page": 100}
        original_name = getattr(video, "original_name", None)
        if original_name:
            params["release"] = original_name[:512]

        if isinstance(video, Episode):
            imdb_id = getattr(video, "series_imdb_id", None)
            if imdb_id:
                path = (
                    f"/api/v1/series/{imdb_id}/seasons/{video.season}"
                    f"/episodes/{video.episode}/subtitles"
                )
            else:
                path = "/api/v1/subtitles"
                params.update(
                    {
                        "title": video.series,
                        "media_type": "episode",
                        "season": video.season,
                        "episode": video.episode,
                    }
                )
        else:
            imdb_id = getattr(video, "imdb_id", None)
            if imdb_id:
                path = f"/api/v1/movies/{imdb_id}/subtitles"
                if video.year:
                    params["year"] = video.year
            else:
                path = "/api/v1/subtitles"
                params.update({"title": video.title, "media_type": "movie"})
                if video.year:
                    params["year"] = video.year

        payload = self._json(path, params=params)
        records = payload.get("subtitles")
        if not isinstance(records, list):
            raise ProviderError("SubsDump response is missing subtitles")

        subtitles = []
        for record in records:
            if not self._valid_record(record, language_code):
                logger.debug("Skipping malformed SubsDump subtitle record")
                continue
            page_path = record["links"]["page"]
            subtitle = SubsDumpSubtitle(
                language,
                record,
                record["links"]["content"],
                f"{self.base_url}{page_path}",
            )
            subtitle.get_matches(video)
            subtitles.append(subtitle)
        return subtitles

    def list_subtitles(self, video, languages):
        subtitles = []
        for language in languages:
            base_language = Language.rebuild(language, hi=False, forced=False)
            if base_language not in self.languages:
                continue
            subtitles.extend(self._query_language(video, language))
        return subtitles

    def download_subtitle(self, subtitle):
        if self.session is None:
            raise ProviderError("SubsDump provider is not initialized")

        try:
            response = self.session.get(
                f"{self.base_url}{subtitle.content_path}",
                timeout=30,
                allow_redirects=False,
            )
        except SSLError as error:
            raise ConfigurationError("SubsDump TLS verification failed") from error
        except Timeout as error:
            raise ProviderError("SubsDump download timed out") from error
        except ConnectionError as error:
            raise ProviderError("SubsDump is unreachable") from error

        if response.status_code in {401, 403}:
            raise AuthenticationError("SubsDump rejected the API key")
        if response.status_code != 200:
            raise ProviderError(f"SubsDump download returned HTTP {response.status_code}")
        if not response.content or len(response.content) > 10 * 1024 * 1024:
            raise ProviderError("SubsDump returned an invalid subtitle file")
        subtitle.content = fix_line_ending(response.content)
