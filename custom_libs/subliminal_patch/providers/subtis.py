# -*- coding: utf-8 -*-
"""Subtis provider for subliminal."""

from __future__ import annotations

import logging
import os
import struct
from json import JSONDecodeError
from typing import TYPE_CHECKING
from urllib.parse import quote

from guessit import guessit
from requests import Session
from requests.exceptions import HTTPError, RequestException, Timeout
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language

if TYPE_CHECKING:
    from subliminal.video import Video as SubtitleVideo

__version__ = "0.9.2"

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.subt.is/v1"
USER_AGENT = f"Bazarr/Subtis/{__version__}"
REQUEST_TIMEOUT_SECONDS = 10
DOWNLOAD_TIMEOUT_SECONDS = 30


class SubtisSubtitle(Subtitle):
    """Subtitle representation for the Subtis provider.

    Represents a Spanish subtitle from the subt.is API with metadata
    for matching against video files.
    """

    provider_name: str = "subtis"
    hash_verifiable: bool = True

    def __init__(
        self,
        language: Language,
        video: Movie,
        page_link: str,
        title: str,
        download_url: str,
        is_synced: bool = True,
        search_method: str | None = None,
    ) -> None:
        super().__init__(language, hearing_impaired=False, page_link=page_link)
        self.video = video
        self.download_url = download_url
        self.is_synced = is_synced
        self._title = str(title).strip()
        self.search_method = search_method
        sync_indicator = "" if is_synced else " [fuzzy match]"
        self.release_info = f"{self._title}{sync_indicator}"

    @property
    def id(self) -> str:
        return self.page_link

    def get_matches(self, video: SubtitleVideo) -> set[str]:
        self.matches: set[str] = set()

        if isinstance(video, Movie):
            if self.search_method == "hash":
                self.matches.add("hash")
            else:
                self.matches |= guess_matches(video, guessit(self._title, {"type": "movie"}))

        return self.matches


class SubtisProvider(Provider):
    """Subtis subtitle provider for Spanish language subtitles.

    Searches the subt.is API for subtitles using a cascade of increasingly
    broad matching strategies (hash -> bytes -> filename -> alternative).
    Currently supports movies only.
    """

    languages: set[Language] = {Language.fromalpha2("es")}
    video_types: tuple[type[Movie], ...] = (Movie,)
    provider_name: str = "subtis"
    version: str = __version__

    def __init__(self) -> None:
        self.session: Session | None = None

    def initialize(self) -> None:
        self.session = Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
        )

    def terminate(self) -> None:
        if self.session is not None:
            self.session.close()
            self.session = None

    def _encode_filename(self, filename: str) -> str:
        return quote(filename, safe="")

    def _build_hash_url(self, video_hash: str) -> str:
        return f"{API_BASE_URL}/subtitle/find/file/hash/{video_hash}"

    def _build_bytes_url(self, file_size: int) -> str:
        return f"{API_BASE_URL}/subtitle/find/file/bytes/{file_size}"

    def _build_filename_url(self, filename: str) -> str:
        encoded = self._encode_filename(filename)
        return f"{API_BASE_URL}/subtitle/find/file/name/{encoded}"

    def _build_alternative_url(self, filename: str) -> str:
        encoded = self._encode_filename(filename)
        return f"{API_BASE_URL}/subtitle/file/alternative/{encoded}"

    def _compute_video_hash(self, file_path: str) -> str | None:
        """Compute OpenSubtitles hash for a video file.

        Hash is: size + checksum(first 64KB) + checksum(last 64KB)
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size <= 0:
                return None

            def _checksum_at(offset: int, length: int) -> int:
                checksum = 0
                with open(file_path, "rb") as handle:
                    handle.seek(offset)
                    data = handle.read(length)
                if not data:
                    return 0
                padding = (8 - (len(data) % 8)) % 8
                if padding:
                    data += b"\0" * padding
                for chunk in struct.iter_unpack("<Q", data):
                    checksum += chunk[0]
                return checksum

            chunk_size = min(65536, file_size)
            head_sum = _checksum_at(0, chunk_size)
            tail_offset = max(file_size - chunk_size, 0)
            tail_sum = _checksum_at(tail_offset, chunk_size)

            file_hash = (file_size + head_sum + tail_sum) & 0xFFFFFFFFFFFFFFFF
            return f"{file_hash:016x}"
        except OSError as error:
            logger.warning("Unable to compute hash for %s: %s", file_path, error)
            return None

    def _parse_api_response(
        self,
        response_data: dict[str, object],
    ) -> tuple[str, str] | None:
        """Extract subtitle link and title from API response.

        Expects response in format:
            {"subtitle": {"subtitle_link": "..."}, "title": {"title_name": "..."}}

        Returns:
            Tuple of (subtitle_link, title_name), or None if required fields
            are missing. Uses "Unknown" as fallback for missing title_name.
        """
        if not isinstance(response_data, dict):
            return None

        subtitle_data = response_data.get("subtitle")
        if not isinstance(subtitle_data, dict):
            return None

        subtitle_link = subtitle_data.get("subtitle_link")
        if not isinstance(subtitle_link, str) or not subtitle_link:
            return None

        title_data = response_data.get("title", {})
        title_name = (
            title_data.get("title_name", "Unknown")
            if isinstance(title_data, dict)
            else "Unknown"
        )

        return subtitle_link, str(title_name)

    def _fetch_subtitle(
        self,
        url: str,
        filename: str,
    ) -> tuple[str, str] | None:
        """Fetch and parse subtitle from URL.

        Returns tuple of (subtitle_link, title_name) or None if not found.
        """
        if self.session is None:
            logger.warning("Session not initialized")
            return None

        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            return self._parse_api_response(data)
        except Timeout:
            logger.warning("Request timed out for %s", filename)
        except HTTPError as error:
            if error.response.status_code != 404:
                logger.warning("HTTP %s for %s", error.response.status_code, filename)
        except RequestException as error:
            logger.warning("Network error for %s: %s", filename, error)
        except JSONDecodeError as error:
            logger.warning("Invalid JSON response for %s: %s", filename, error)
        return None

    def query(self, language: Language, video: Movie | Episode) -> list[SubtisSubtitle]:
        if not video.name:
            logger.warning("Missing video name")
            return []

        filename = os.path.basename(video.name)

        video_hash: str | None = None
        if os.path.exists(video.name):
            video_hash = self._compute_video_hash(video.name)

        cascade_steps: list[tuple[str, bool, str]] = []
        if video_hash:
            cascade_steps.append((self._build_hash_url(video_hash), True, "hash"))
        if video.size:
            cascade_steps.append((self._build_bytes_url(video.size), True, "bytes"))
        cascade_steps.append((self._build_filename_url(filename), True, "name"))
        cascade_steps.append(
            (self._build_alternative_url(filename), False, "alternative")
        )

        for url, is_synced, method in cascade_steps:
            parsed = self._fetch_subtitle(url, filename)
            if parsed:
                subtitle_link, title_name = parsed
                logger.debug(
                    "Found subtitle via cascade search (%s) for %s",
                    method,
                    filename,
                )
                return [
                    SubtisSubtitle(
                        language=language,
                        video=video,
                        page_link=url,
                        title=title_name,
                        download_url=subtitle_link,
                        is_synced=is_synced,
                        search_method=method,
                    )
                ]

        logger.info("No subtitle found for %s", filename)
        return []

    def list_subtitles(
        self,
        video: Movie | Episode,
        languages: set[Language],
    ) -> list[SubtisSubtitle]:
        if isinstance(video, Episode):
            logger.debug("TV show support not yet implemented")
            return []

        subtitles: list[SubtisSubtitle] = []
        for language in languages:
            subtitles.extend(self.query(language, video))
        return subtitles

    def download_subtitle(self, subtitle: SubtisSubtitle) -> None:
        """Download subtitle content from the API.

        Fetches the subtitle file from subtitle.download_url and stores
        the content in subtitle.content. Handles network errors gracefully.
        """
        if self.session is None:
            logger.warning("Session not initialized")
            return

        if not subtitle.download_url:
            logger.warning("No download URL available")
            return

        try:
            response = self.session.get(
                subtitle.download_url,
                timeout=DOWNLOAD_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            if not response.content:
                logger.warning("Empty subtitle content")
                return

            subtitle.content = response.content

        except Timeout:
            logger.warning(
                "Download timed out from %s",
                subtitle.download_url,
            )
        except HTTPError as error:
            logger.warning(
                "HTTP error %s downloading from %s",
                error.response.status_code,
                subtitle.download_url,
            )
        except RequestException as error:
            logger.warning(
                "Network error downloading from %s: %s",
                subtitle.download_url,
                error,
            )
