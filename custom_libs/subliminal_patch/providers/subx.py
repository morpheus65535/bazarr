# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import os
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
        season=None,
        episode=None,
    ):
        super(SubxSubtitle, self).__init__(
            language,
            hearing_impaired=False,
            page_link=page_link,
        )

        self.video = video
        self.download_url = download_url
        self.uploader = uploader
        self.season = season
        self.episode = episode

        self.release_info = str(title).strip()
        if description:
            self.release_info += f" | {description}"

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        """Determines which features match the video."""
        self.matches = set()  # ← Cambiar de 'matches' a 'self.matches'
    
        if isinstance(video, Episode):
            self.matches.update({"title", "series", "year"})
            
            # Match season if it aligns
            if self.season == video.season:
                self.matches.add("season")
                
            # For episode matching:
            # - If subtitle has specific episode, it must match
            # - If subtitle is a season pack (episode=None), consider it a match
            if self.episode is not None:
                if self.episode == video.episode:
                    self.matches.add("episode")
            else:
                # Season pack - add episode match to allow Bazarr to accept it
                self.matches.add("episode")
        
        elif isinstance(video, Movie):
            self.matches.update({"title", "year"})
    
        # Update matches from release info, but preserve episode match for season packs
        is_season_pack = isinstance(video, Episode) and self.episode is None
        if is_season_pack:
            # Temporarily store that this is a season pack
            had_episode_match = "episode" in self.matches  # ← self.matches
        
        update_matches(self.matches, video, self.release_info)  # ← self.matches
        
        # Restore episode match for season packs (it might be removed by update_matches)
        if is_season_pack and had_episode_match:
            self.matches.add("episode")  # ← self.matches
        
        return self.matches  # ← self.matches

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
            "User-Agent": os.environ.get("SZ_USER_AGENT", "Sub-Zero/2"),
        })

    def initialize(self):
        """Initialize session."""
        pass

    def terminate(self):
        """Close session."""
        self.session.close()

    def run_query(self, query, video, video_type, season=None, episode=None):
        """
        Execute a search on SubX API.
        
        Args:
            query: Search term (or None if using imdb_id)
            video: Video object
            video_type: Video type ('episode' or 'movie')
            season: Season number to filter (optional)
            episode: Episode number to filter (optional)
            
        Returns:
            List of found subtitles
        """
        # Build search parameters
        params = {
            "limit": 200,
            "video_type": video_type,
        }

        # Prefer IMDb ID for more accurate results (per API docs)
        if hasattr(video, 'imdb_id') and video.imdb_id:
            params["imdb_id"] = video.imdb_id
            logger.debug("Using IMDb ID for search: %s", video.imdb_id)
        elif query:
            # Fallback to title search
            params["title"] = query
        else:
            logger.error("No search criteria provided (no imdb_id or query)")
            return []
        
        # Add year if available (helps narrow results)
        if hasattr(video, 'year') and video.year:
            params["year"] = video.year

        logger.debug("SubX search params: %s", params)

        # Execute request with retry logic
        max_retries = 3
        data = None
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{_SUBX_BASE_URL}/api/subtitles/search",
                    params=params,
                    timeout=10,  # 10s timeout for search (per API docs)
                )
                
                # Handle specific HTTP status codes per API documentation
                if response.status_code == 400:
                    logger.error("Bad request to SubX API: %s", response.text)
                    return []  # Don't retry on bad requests
                
                elif response.status_code == 401:
                    logger.error("Invalid SubX API key")
                    raise ConfigurationError("Invalid SubX API key")
                
                elif response.status_code == 404:
                    logger.debug("No results found (404)")
                    return []
                
                elif response.status_code == 429:
                    # Rate limited - exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning("Rate limit hit, waiting %ds before retry %d/%d", 
                                     wait_time, attempt + 1, max_retries)
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limit exceeded after %d retries", max_retries)
                        raise APIThrottled("SubX rate limit exceeded")
                
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning("Server error %d, retrying in %ds (attempt %d/%d)", 
                                     response.status_code, wait_time, attempt + 1, max_retries)
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Server error persists after %d retries", max_retries)
                        return []
                
                # Success
                response.raise_for_status()
                data = response.json()
                break  # Exit retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("SubX API error (attempt %d/%d): %s", 
                                 attempt + 1, max_retries, e)
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error("SubX API error after %d retries: %s", max_retries, e)
                    return []
        
        if data is None:
            logger.error("No data received from SubX API")
            return []

        logger.debug(
            "SubX API response: total=%s | items=%d",
            data.get("total"),
            len(data.get("items", [])),
        )

        subtitles = []
        filtered_count = 0
        season_packs = []  # Store season packs as fallback
        
        for item in data.get("items", []):
            # Filter by season/episode if searching for TV shows
            item_season = item.get("season")
            item_episode = item.get("episode")
            
            logger.debug("Item: season=%s, episode=%s, title=%s", 
                        item_season, item_episode, item.get("title"))
            
            # Skip if season doesn't match
            if season is not None and item_season != season:
                logger.debug("Skipping - season mismatch (want %s, got %s)", season, item_season)
                filtered_count += 1
                continue
            
            # If looking for specific episode
            if episode is not None:
                # Exact episode match - highest priority
                if item_episode == episode:
                    logger.debug("Found exact episode match")
                # Season pack (episode=None) - save as fallback
                elif item_episode is None and item_season == season:
                    logger.debug("Found season pack - saving as fallback")
                    season_packs.append(item)
                    continue
                # Different episode - skip
                else:
                    logger.debug("Skipping - episode mismatch (want %s, got %s)", episode, item_episode)
                    filtered_count += 1
                    continue

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
                uploader=item.get("uploader_name", "unknown"),
                download_url=f"{_SUBX_BASE_URL}/api/subtitles/{item['id']}/download",
                season=item_season,
                episode=item_episode,
            ))
        
        # If no exact episode matches found, use season packs as fallback
        if episode is not None and not subtitles and season_packs:
            logger.info("No exact episode matches, using %d season pack(s) as fallback", len(season_packs))
            for item in season_packs:
                page_url = item.get("page_url")
                if not page_url and item.get("id"):
                    page_url = f"{_SUBX_BASE_URL}/api/subtitles/{item['id']}"

                subtitles.append(self.subtitle_class(
                    language=Language.fromalpha2("es"),
                    video=video,
                    page_link=page_url,
                    title=item.get("title"),
                    description=item.get("description", ""),
                    uploader=item.get("uploader_name", "unknown"),
                    download_url=f"{_SUBX_BASE_URL}/api/subtitles/{item['id']}/download",
                    season=item.get("season"),
                    episode=item.get("episode"),
                ))
        
        logger.debug("After filtering: %d subtitles (filtered out %d)", len(subtitles), filtered_count)

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

        # ---------------------------
        # EPISODES
        # ---------------------------
        if isinstance(video, Episode):
            titles = _collect_titles(video, episode=True, max_alts=3)
            logger.debug("Titles to search: %s", titles)

            for raw_title in titles:
                title = _series_sanitizer(raw_title)

                # 1. First try: Exact episode (e.g., "Breaking Bad S03E13")
                logger.debug("Searching for %s S%02dE%02d", title, video.season, video.episode)
                query = f"{title} S{video.season:02d}E{video.episode:02d}"
                subtitles = self.run_query(
                    query,
                    video,
                    "episode",
                    season=video.season,
                    episode=video.episode,
                )
                
                if subtitles:
                    logger.debug("Found %d subtitles for exact episode", len(subtitles))
                    break
                
                # 2. Second try: Season only (e.g., "Breaking Bad S03")
                logger.debug("No exact match, trying season: %s S%02d", title, video.season)
                query = f"{title} S{video.season:02d}"
                subtitles = self.run_query(
                    query,
                    video,
                    "episode",
                    season=video.season,
                    episode=None,  # Accept any episode from this season
                )
                
                if subtitles:
                    logger.debug("Found %d subtitles for season", len(subtitles))
                    break
                
                # 3. Last try: Series title only (fallback for poorly tagged content)
                logger.debug("No season match, trying series title only: %s", title)
                subtitles = self.run_query(
                    title,
                    video,
                    "episode",
                    season=video.season,
                    episode=None,
                )
                
                if subtitles:
                    logger.debug("Found %d subtitles from series title search", len(subtitles))
                    break
                
                time.sleep(1)  # Small delay between different title attempts

        # ---------------------------
        # MOVIES
        # ---------------------------
        else:
            titles = _collect_titles(video, episode=False, max_alts=3)
            logger.debug("Titles to search: %s", titles)

            for title in titles:
                logger.debug("Searching for movie: %s", title)
                subtitles = self.run_query(title, video, "movie")
                
                if subtitles:
                    logger.debug("Found %d subtitles for movie", len(subtitles))
                    break
                
                time.sleep(1)  # Small delay between searches

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
