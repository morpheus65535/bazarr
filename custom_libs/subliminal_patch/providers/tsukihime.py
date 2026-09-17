from __future__ import absolute_import

import logging
import lzma
import os
import re

from guessit import guessit
from requests import Session
from requests.exceptions import RequestException
from subzero.language import Language

from subliminal.exceptions import ProviderError
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches

logger = logging.getLogger(__name__)

API_URL = "https://api.tsukihime.org/v1"
STORAGE_URL = "https://storage.tsukihime.org"
MAX_TORRENTS = 20

# TsukiHime stores each subtitle track as an XZ archive named after the attachment id under a
# path keyed on the hexadecimal rendering of that same id. AnimeTosho-mirrored torrents are
# served from a dedicated path, the rest from the native one.
NATIVE_STORAGE_PATH = "attach"
ANIMETOSHO_STORAGE_PATH = "tosho/attach"

# TsukiHime reports regional language variants with codes that neither resolve to a valid IETF
# language nor carry a country babelfish understands. Map them explicitly so a track is never
# demoted to a generic language (e.g. Simplified Chinese) and dropped by the pool.
_REGIONAL_LANGUAGE_ALIASES = {
    "es-419": Language("spa", "MX"),
    "es-es": Language("spa"),
    "pt-br": Language("por", "BR"),
    "pt-pt": Language("por"),
    "zh-cn": Language("zho", "CN"),
    "zh-hans": Language("zho", "CN"),
    "zh-hk": Language("zho", "TW"),
    "zh-hant": Language("zho", "TW"),
    "zh-tw": Language("zho", "TW"),
}

_SUPPORTED_ALPHA2_CODES = [
    "af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "cs",
    "da", "de", "el", "en", "eo", "es", "et", "eu", "fa", "fi",
    "fr", "gl", "he", "hi", "hr", "hu", "hy", "id", "is", "it",
    "ja", "ka", "kk", "ko", "lt", "lv", "mk", "ms", "nl", "no",
    "pl", "pt", "ro", "ru", "sk", "sl", "sq", "sr", "sv", "th",
    "tr", "uk", "ur", "uz", "vi", "zh",
]

# The provider pool intersects the requested languages with these before calling list_subtitles,
# so every regional variant a profile may ask for has to be declared or it never reaches this
# provider. The same applies to the forced and hearing-impaired variants.
languages = {Language.fromalpha2(code) for code in _SUPPORTED_ALPHA2_CODES}
languages.update(_REGIONAL_LANGUAGE_ALIASES.values())
languages.update(Language.rebuild(language, forced=True) for language in list(languages))
languages.update(Language.rebuild(language, hi=True) for language in list(languages))

_SUBTITLE_CODECS = ("ass", "srt", "ssa", "sub", "vtt")

# Matches the hearing-impaired markers fansub groups append to a track name, e.g.
# "English (CC)", "[SDH]" or "english.hearing impaired".
_HI_MARKER_RE = re.compile(
    r"(?:^|[\s_.\-\[(])(?:cc|sdh|hearing[\s_.\-]*impaired)(?:$|[\s_.\-)\]])",
    re.IGNORECASE,
)

# Tracks holding only signs and songs are frequently muxed without the forced disposition flag, so
# the track name is the only hint. Treat them like forced ones instead of offering them as full
# subtitles, e.g. "English [Signs]" or "Signs & Songs".
_SIGNS_MARKER_RE = re.compile(r"\bsigns?\b", re.IGNORECASE)


def _language_from_code(code):
    if not code:
        return None

    normalized = code.strip().lower().replace("_", "-")
    if normalized in _REGIONAL_LANGUAGE_ALIASES:
        return _REGIONAL_LANGUAGE_ALIASES[normalized]

    for candidate in (code.strip(), normalized):
        try:
            return Language.fromietf(candidate)
        except Exception:
            continue

    try:
        return Language.fromalpha3b(normalized)
    except Exception:
        logger.debug("Unsupported TsukiHime language code: %s", code)
        return None


class TsukiHimeSubtitle(Subtitle):
    """Subtitle track extracted from a release indexed by TsukiHime."""
    provider_name = "tsukihime"
    hash_verifiable = False

    def __init__(self, language, download_url, release_info, release_id, codec, verified_matches,
                 uploader=None):
        super(TsukiHimeSubtitle, self).__init__(
            language,
            page_link=download_url,
            original_format=True,
        )
        self.download_url = download_url
        self.release_info = release_info
        self.release_id = release_id
        self.format = codec.lower()
        self.verified_matches = verified_matches
        # TsukiHime has no uploader concept, so Bazarr's free-text Uploader column carries the
        # streaming source of the release (e.g. "Crunchy Roll", "Netflix") to tell apart variants.
        self.uploader = uploader
        self.matches = set()

    @property
    def id(self):
        # TsukiHime reuses the same attachment (and therefore the same storage URL) across release
        # associations, so the release has to stay part of the id. Otherwise the pool drops every
        # association but the first and scoring cannot use their release-specific metadata.
        return f"{self.release_id}:{self.download_url}"

    def get_matches(self, video):
        video_type = "episode" if isinstance(video, Episode) else "movie"
        self.matches |= guess_matches(video, guessit(self.release_info, {"type": video_type}))
        self.matches.update(self.verified_matches)
        return self.matches


class TsukiHimeProvider(Provider):
    """TsukiHime anime subtitle provider."""
    provider_name = "tsukihime"
    subtitle_class = TsukiHimeSubtitle
    languages = languages
    video_types = (Episode, Movie)

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers.update({"User-Agent": os.environ.get("SZ_USER_AGENT", "Bazarr")})

    def terminate(self):
        if self.session is not None:
            self.session.close()
            self.session = None

    def list_subtitles(self, video, languages):
        anime = self._get_anime(video)
        if not anime:
            return []

        requested_languages = set(languages)
        entries = [
            entry for entry in self._get_entries(video, anime["id"])
            if entry.get("state") == "completed"
            and self._entry_has_requested_language(entry.get("sublangs", []), requested_languages)
        ]

        # Prefer the releases that best resemble the original media name so, when the candidate cap
        # is reached, the associations we keep come from the most relevant torrents first.
        entries.sort(key=lambda entry: self._entry_score(video, entry), reverse=True)

        subtitles = []
        seen_ids = set()
        for entry in entries[:MAX_TORRENTS]:
            entry_id = entry.get("id")
            if not entry_id:
                continue

            detail = self._get_json(f"/torrents/{entry_id}")
            if not detail:
                continue

            for file_data in self._matching_files(video, detail.get("files", [])):
                for attachment in file_data.get("attachments", []):
                    subtitle = self._subtitle_from_attachment(
                        video, anime, entry, file_data, attachment, requested_languages,
                    )
                    if subtitle and subtitle.id not in seen_ids:
                        seen_ids.add(subtitle.id)
                        subtitles.append(subtitle)

        return subtitles

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle %r", subtitle)
        response = self._download(subtitle.download_url)
        if not response.content.startswith(b"\xFD\x37\x7A\x58\x5A\x00"):
            raise ProviderError("TsukiHime returned an unidentified archive type")
        try:
            subtitle.content = lzma.decompress(response.content)
        except lzma.LZMAError as error:
            raise ProviderError("TsukiHime subtitle decompression failed") from error
        return subtitle

    def _get_anime(self, video):
        if isinstance(video, Episode):
            anidb_id = self._scalar(getattr(video, "series_anidb_id", None))
            if not anidb_id:
                logger.debug("Skipping %r because no AniDB series ID was identified", video)
                return None
            return self._get_json(f"/animes/anidb/{anidb_id}")

        anilist_id = self._scalar(getattr(video, "anilist_id", None))
        if not anilist_id:
            logger.debug("Skipping %r because no AniList ID was identified", video)
            return None
        return self._get_json(f"/animes/anilist/{anilist_id}")

    def _get_entries(self, video, anime_id):
        if isinstance(video, Episode):
            episode_no = self._scalar(getattr(video, "series_anidb_episode_no", None)) or video.episode
            data = self._get_json(f"/animes/{anime_id}/episodes/{episode_no}")
        else:
            data = self._get_json(f"/animes/{anime_id}")
        return data.get("results", []) if data else []

    def _subtitle_from_attachment(self, video, anime, entry, file_data, attachment, requested_languages):
        if attachment.get("type") != 1:
            return None

        info = attachment.get("info") or {}
        # Native torrents only expose the subtitle once it has been extracted and cached; a 0 here
        # means the track is not downloadable yet. AnimeTosho-mirrored ones omit the key entirely.
        if info.get("cached") == 0:
            return None

        language = _language_from_code(info.get("lang"))
        if not language:
            return None

        name = info.get("name", "")
        if bool(info.get("forced")) or _SIGNS_MARKER_RE.search(name):
            language = Language.rebuild(language, forced=True)
        elif _HI_MARKER_RE.search(name):
            language = Language.rebuild(language, hi=True)
        if language not in requested_languages:
            return None

        codec = info.get("codec", "").lower()
        attachment_id = attachment.get("id")
        if codec not in _SUBTITLE_CODECS or not attachment_id:
            return None

        storage_path = ANIMETOSHO_STORAGE_PATH if entry.get("animetosho") else NATIVE_STORAGE_PATH
        download_url = (
            f"{STORAGE_URL}/{storage_path}/{int(attachment_id):08X}/{int(attachment_id)}.xz"
        )

        verified_matches = {"title"} if isinstance(video, Movie) else {"series", "season", "episode"}
        if video.year and anime.get("release_year") == video.year:
            verified_matches.add("year")

        release_info = entry.get("name") or file_data.get("filename", "")
        return self.subtitle_class(
            language,
            download_url,
            release_info=release_info,
            release_id=entry.get("id"),
            codec=codec,
            verified_matches=verified_matches,
            uploader=self._streaming_service(video, release_info) or self._track_label(info.get("name")),
        )

    def _get_json(self, path):
        try:
            response = self.session.get(f"{API_URL}{path}", timeout=10)
        except RequestException as error:
            logger.exception("TsukiHime request failed for %s", path)
            raise ProviderError("TsukiHime request failed; check the Bazarr log") from error

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ProviderError(f"TsukiHime returned HTTP {response.status_code} for {path}")
        try:
            return response.json()
        except ValueError as error:
            raise ProviderError(f"TsukiHime returned invalid JSON for {path}") from error

    def _download(self, url):
        try:
            response = self.session.get(url, timeout=10)
        except RequestException as error:
            logger.exception("TsukiHime subtitle download failed for %s", url)
            raise ProviderError("TsukiHime subtitle download failed; check the Bazarr log") from error

        if response.status_code != 200:
            raise ProviderError(f"TsukiHime returned HTTP {response.status_code} for {url}")
        return response

    @staticmethod
    def _scalar(value):
        if isinstance(value, (list, tuple)):
            return value[-1] if value else None
        return value

    @staticmethod
    def _streaming_service(video, release_info):
        video_type = "episode" if isinstance(video, Episode) else "movie"
        service = guessit(release_info, {"type": video_type}).get("streaming_service")
        if isinstance(service, (list, tuple)):
            return service[0] if service else None
        return service

    @staticmethod
    def _track_label(name):
        # A release can carry several full tracks for the same language (its own translation plus a
        # streaming one, for instance). The track name is the only thing telling them apart, so it
        # goes on the Uploader column too, unless it is just the language name.
        label = (name or "").strip()
        if not label:
            return None
        try:
            if Language.fromname(label) is not None:
                return None
        except Exception:
            pass
        return label

    @classmethod
    def _entry_has_requested_language(cls, sublangs, requested_languages):
        requested_alpha3 = {language.alpha3 for language in requested_languages}
        return any(
            language and language.alpha3 in requested_alpha3
            for language in (_language_from_code(code) for code in sublangs)
        )

    @classmethod
    def _entry_score(cls, video, entry):
        original_name = os.path.splitext((getattr(video, "original_name", None) or video.name))[0]
        name_overlap = cls._name_overlap(entry.get("name", ""), original_name)
        # Among equally similar releases prefer the most recently indexed one.
        return name_overlap, int(entry.get("source_date") or 0)

    @classmethod
    def _name_overlap(cls, candidate, reference):
        candidate_tokens = set(re.split(r"\W+", candidate))
        reference_tokens = set(re.split(r"\W+", reference))
        if not candidate_tokens or not reference_tokens:
            return 0.0
        return len(candidate_tokens & reference_tokens) / len(candidate_tokens)

    @classmethod
    def _matching_files(cls, video, files):
        if not files:
            return []

        if len(files) <= 1:
            return files

        if isinstance(video, Movie):
            original_name = os.path.splitext((getattr(video, "original_name", None) or video.name).lower())[0]
            best = max(
                files,
                key=lambda file_data: cls._name_overlap(
                    file_data.get("filename", "").lower(),
                    original_name,
                ),
            )
            return [best]

        expected = {
            cls._scalar(getattr(video, "series_anidb_episode_no", None)),
            video.episode,
        }
        expected.discard(None)

        matching = []
        for file_data in files:
            guessed_episode = guessit(file_data.get("filename", ""), {"type": "episode"}).get("episode")
            guessed_episodes = guessed_episode if isinstance(guessed_episode, (list, tuple)) else [guessed_episode]
            if expected.intersection(guessed_episodes):
                matching.append(file_data)
        return matching or files
