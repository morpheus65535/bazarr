# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import re
import time

from requests import Session
from requests.exceptions import JSONDecodeError

from subliminal.exceptions import ConfigurationError, ProviderError
from subliminal.video import Episode, Movie

from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import (
    get_archive_from_bytes,
    get_subtitle_from_archive,
    update_matches,
)
from subliminal_patch.subtitle import Subtitle

from subzero.language import Language

logger = logging.getLogger(__name__)

_SUBX_BASE_URL = "https://subx-api.duckdns.org"


# ---------------------------
# Helpers
# ---------------------------

def _series_sanitizer(title):
    """Cleans series title for search."""
    title = title or ""
    title = re.sub(r"[._]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _unique_nonempty(seq):
    """Returns unique non-empty elements maintaining order."""
    seen = set()
    out = []
    for x in seq:
        if not x:
            continue
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _collect_titles(video, episode, max_alts=5):
    """Collects main and alternative titles."""
    titles = [video.series] if episode else [video.title]
    try:
        alts = getattr(
            video,
            "alternative_series" if episode else "alternative_titles",
            None,
        )
        if alts:
            titles.extend(alts)
    except Exception:
        pass
    return _unique_nonempty(titles)[:max_alts]


# ---------------------------
# Subtitle Class
# ---------------------------

class SubxSubtitle(Subtitle):
    """SubX Subtitle."""
    provider_name = "subx"
    hash_verifiable = False

    def __init__(
        self,
        language,
        video,
        page_link,
        title,
        description,
        uploader,
        download_url,
    ):
        super(SubxSubtitle, self).__init__(
            language,
            hearing_impaired=False,
            page_link=page_link,
        )

        self.video = video
        self.download_url = download_url
        self.uploader = uploader

        self.release_info = str(title).strip()
        if description:
            self.release_info += f" | {description}"

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        """Determines which features match the video."""
        matches = set()

        if isinstance(video, Episode):
            matches.update({"title", "series", "season", "episode", "year"})
        elif isinstance(video, Movie):
            matches.update({"title", "year"})

        update_matches(matches, video, self.release_info)
        return matches


# ---------------------------
# Provider Class
# ---------------------------

class SubxSubtitlesProvider(Provider):
    """SubX subtitle provider for Spanish."""
    provider_name = "subx"
    hash_verifiable = False

    languages = {
        Language.fromalpha2("es"),
        Language("spa", "MX"),
    }

    video_types = (Episode, Movie)
    subtitle_class = SubxSubtitle

    def __init__(self, api_key=None):
        """
        Initialize SubX provider.
        
        Args:
            api_key: SubX API key (required)
        """
        if not api_key:
            raise ConfigurationError("SubX API key is required")

        self.session = Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Bazarr",
        })

    def initialize(self):
        """Initialize session."""
        pass

    def terminate(self):
        """Close session."""
        self.session.close()

    def run_query(self, query, video, video_type):
        """
        Execute a search on SubX API.
        
        Args:
            query: Search term
            video: Video object
            video_type: Video type ('episode' or 'movie')
            
        Returns:
            List of found subtitles
        """
        params = {
            "query": query,
            "limit": 100,
            "video_type": video_type,
        }

        if video.year:
            params["year"] = video.year

        logger.debug("SubX search params: %s", params)

        try:
            response = self.session.get(
                f"{_SUBX_BASE_URL}/api/subtitles/search",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error("SubX API error: %s", e)
            return []

        logger.debug(
            "SubX API response: total=%s | items=%d",
            data.get("total"),
            len(data.get("items", [])),
        )

        subtitles = []
        for item in data.get("items", []):
            # Build page URL
            page_url = item.get("page_url")
            if not page_url and item.get("id"):
                page_url = f"{_SUBX_BASE_URL}/api/subtitles/{item['id']}"

            subtitles.append(self.subtitle_class(
                language=Language.fromalpha2("es"),
                video=video,
                page_link=page_url,
                title=item.get("title"),
                description=item.get("description", ""),
                uploader=item.get("uploader", "unknown"),
                download_url=f"{_SUBX_BASE_URL}/api/subtitles/{item['id']}/download",
            ))

        return subtitles

    def list_subtitles(self, video, languages):
        """
        List available subtitles for video.
        
        Args:
            video: Video object
            languages: Requested languages
            
        Returns:
            List of found subtitles
        """
        subtitles = []
        seen_queries = set()

        def query_once(q, vtype):
            """Execute a unique query without repetition."""
            if not q or q in seen_queries:
                return []
            seen_queries.add(q)
            res = self.run_query(q, video, vtype)
            time.sleep(5)  # Rate limiting
            return res or []

        # ---------------------------
        # EPISODES
        # ---------------------------
        if isinstance(video, Episode):
            titles = _collect_titles(video, episode=True, max_alts=5)
            logger.debug("Titles to search: %s", titles)

            for raw_title in titles:
                title = _series_sanitizer(raw_title)

                # S00E00 search
                subtitles += query_once(
                    f"{title} S{video.season:02}E{video.episode:02}",
                    "episode",
                )
                
                # Season search
                subtitles += query_once(
                    f"{title} S{video.season:02}",
                    "episode",
                )

                # Series title only if few results
                if len(subtitles) <= 5:
                    subtitles += query_once(title, "episode")
                else:
                    break

                # Episode title as last resort
                if not subtitles and getattr(video, "title", None) and video.title != title:
                    subtitles += query_once(video.title, "episode")

                if subtitles:
                    break

        # ---------------------------
        # MOVIES
        # ---------------------------
        else:
            titles = _collect_titles(video, episode=False, max_alts=5)
            logger.debug("Titles to search: %s", titles)

            for t in titles:
                # Title search
                res = query_once(t, "movie")
                if res:
                    subtitles += res
                    break
                    
                # Search with year
                if getattr(video, "year", None):
                    res2 = query_once(f"{t} ({video.year})", "movie")
                    if res2:
                        subtitles += res2
                        break

        return subtitles

    def download_subtitle(self, subtitle):
        """
        Download subtitle content.
        
        Args:
            subtitle: Subtitle object to download
        """
        try:
            response = self.session.get(
                subtitle.download_url,
                timeout=30,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to download subtitle: %s", e)
            raise APIThrottled("Failed to download subtitle")

        # Process compressed file
        archive = get_archive_from_bytes(response.content)
        if archive is None:
            raise APIThrottled("Unknown or unsupported archive format")

        episode = (
            subtitle.video.episode
            if isinstance(subtitle.video, Episode)
            else None
        )

        subtitle.content = get_subtitle_from_archive(
            archive,
            episode=episode,
        )
