# -*- coding: utf-8 -*-
import functools
import logging
import time

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import get_archive_from_bytes
from subliminal_patch.providers.utils import get_subtitle_from_archive
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)


class HDBitsSubtitle(Subtitle):
    provider_name = "hdbits"
    hash_verifiable = False

    def __init__(self, language, id, name, filename, matches=None, episode=None):
        super().__init__(language, hearing_impaired=language.hi)
        self.item_id = id
        self.release_info = name
        self.filename = filename
        self.episode = episode
        self._matches = matches or set()

    def get_matches(self, video):
        update_matches(self._matches, video, self.release_info)
        return self._matches

    @property
    def id(self):
        return f"{self.provider_name}_{self.item_id}"


_SPECIAL_LANG_MAP = {"uk": ("eng",), "br": ("por", "BR"), "gr": ("ell",)}
_ALLOWED_EXTENSIONS = (".ass", ".srt", ".zip", ".rar")


def _get_language(code):
    special_args = _SPECIAL_LANG_MAP.get(code)
    if special_args is None:
        try:
            return Language.fromietf(code)
        except Exception as error:
            logger.debug("Error [%s] loading language with '%s' code", error, code)
            return None

    return Language(*special_args)


class HDBitsProvider(Provider):
    provider_name = "hdbits"

    video_types = (Movie, Episode)
    subtitle_class = HDBitsSubtitle

    languages = {Language("por", "BR")} | {
        Language.fromalpha2(l) for l in language_converters["alpha2"].codes
    }

    def __init__(self, username, passkey) -> None:
        self._session = Session()
        self._def_params = {"username": username, "passkey": passkey}
        self._session.headers.update({"User-Agent": "Bazarr"})

    def initialize(self):
        pass

    def terminate(self):
        self._session.close()

    def list_subtitles(self, video, languages):
        episode = None
        if isinstance(video, Movie):
            lookup = {"imdb": {"id": (video.imdb_id or "").lstrip("tt")}}
            matches = {"imdb_id", "title", "year"}
        else:
            lookup = {"tvdb": {"id": video.series_tvdb_id, "season": video.season}}
            matches = {"tvdb_id", "imdb_id", "series", "title", "episode", "season"}
            episode = video.episode

        logger.debug("ID lookup: %s", lookup)

        response = self._session.post(
            "https://hdbits.org/api/torrents", json={**self._def_params, **lookup}
        )
        response.raise_for_status()
        ids = [item["id"] for item in response.json()["data"]]

        subtitles = []
        for torrent_id in ids:
            subtitles.extend(
                self._parse_subtitles(torrent_id, languages, episode, matches)
            )
            time.sleep(0.5)

        return subtitles

    def _parse_subtitles(self, torrent_id, languages, episode=None, matches=None):
        response = self._session.post(
            "https://hdbits.org/api/subtitles",
            json={**self._def_params, **{"torrent_id": torrent_id}},
        )
        subtitles = response.json()["data"]
        parsed_subs = []
        for subtitle in subtitles:
            if not subtitle["filename"].endswith(_ALLOWED_EXTENSIONS):
                logger.debug("Extension not supported: %s", subtitle["filename"])
                continue

            language = _get_language(subtitle["language"])
            if language is None:
                continue

            if language not in languages:
                logger.debug("Ignoring language: %r !~ %r", language, languages)
                continue

            if episode is not None:
                guessed = _memoized_episode_guess(subtitle["title"])
                if guessed.get("episode") is not None and episode != guessed["episode"]:
                    logger.debug(
                        "Episode not matched: %s != %s", subtitle["title"], episode
                    )
                    continue

            parsed = HDBitsSubtitle(
                language,
                subtitle["id"],
                subtitle["title"],
                subtitle["filename"],
                matches,
                episode,
            )
            parsed_subs.append(parsed)

        return parsed_subs

    def download_subtitle(self, subtitle):
        response = self._session.get(
            f"https://hdbits.org/getdox.php?id={subtitle.item_id}&passkey={self._def_params['passkey']}"
        )
        response.raise_for_status()
        if subtitle.filename.endswith((".zip", ".rar")):
            archive = get_archive_from_bytes(response.content)
            subtitle.content = get_subtitle_from_archive(
                archive, episode=subtitle.episode
            )
        else:
            subtitle.content = response.content


@functools.lru_cache(2048)
def _memoized_episode_guess(content):
    # Use include to save time from unnecessary checks
    return guessit(
        content,
        {
            "type": "episode",
            # Add codec keys to avoid matching x264, 5.1, etc as episode info
            "includes": ["season", "episode", "video_codec", "audio_codec"],
            "enforce_list": True,
        },
    )
