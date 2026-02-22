# -*- coding: utf-8 -*-
"""KickAssSubtitles provider for subliminal."""

from __future__ import absolute_import

import base64
import logging
import os
import time

from requests import Session
from requests.exceptions import HTTPError, RequestException, Timeout
from subliminal.video import Episode, Movie
from subliminal.exceptions import ConfigurationError, ProviderError
from subliminal.utils import hash_opensubtitles
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

API_BASE_URL = "https://kickasssubtitles.com/api"
USER_AGENT = "Bazarr/KickAssSubtitles/{}".format(__version__)
REQUEST_TIMEOUT_SECONDS = 10
DOWNLOAD_TIMEOUT_SECONDS = 30
TASK_POLL_INTERVAL_SECONDS = 2
TASK_MAX_WAIT_SECONDS = 30


class KickAssSubtitlesSubtitle(Subtitle):
    """KickAssSubtitles Subtitle."""

    provider_name = "kickasssubtitles"
    hash_verifiable = True

    def __init__(self, language, page_link, task_id, file_hash=None, imdb_id=None,
                 title=None, year=None, season=None, episode=None):
        super(KickAssSubtitlesSubtitle, self).__init__(language, page_link=page_link)
        self.task_id = task_id
        self.file_hash = file_hash
        self.imdb_id = imdb_id
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.subtitle_extension = None
        self.subtitle_content_b64 = None

    @property
    def id(self):
        return self.task_id

    def get_matches(self, video):
        """Get matches for the subtitle."""
        matches = set()

        # Hash match is the most reliable
        if self.file_hash and hasattr(video, 'hashes') and video.hashes.get('opensubtitles') == self.file_hash:
            matches.add('hash')

        # Handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')
            # imdb
            if self.imdb_id and video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add('series_imdb_id')
        else:
            # title
            matches.add('title')
            # year
            if video.year and self.year == video.year:
                matches.add('year')
            # imdb
            if self.imdb_id and video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')

        return matches


class KickAssSubtitlesProvider(Provider):
    """KickAssSubtitles subtitle provider.

    Searches the KickAssSubtitles API for subtitles using OpenSubtitles hash,
    file size, and filename. Uses an async task-based API.
    """

    languages = {Language.fromalpha2(lang) for lang in [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'ru', 'ar', 'cs', 'da', 'nl',
        'fi', 'el', 'he', 'hu', 'id', 'ja', 'ko', 'no', 'ro', 'sv', 'th', 'tr',
        'vi', 'zh', 'bg', 'hr', 'sk', 'sl', 'sr', 'uk', 'hi', 'bn', 'fa', 'ms',
    ]}
    video_types = (Movie, Episode)
    provider_name = "kickasssubtitles"
    hash_verifiable = True

    def __init__(self, api_key=None):
        if not api_key:
            raise ConfigurationError('API key must be specified')

        self.api_key = api_key
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(self.api_key),
        })

    def terminate(self):
        if self.session is not None:
            self.session.close()
            self.session = None

    def _get_imdb_id(self, video):
        """Extract IMDB ID from video."""
        if isinstance(video, Episode):
            imdb_id = video.series_imdb_id if hasattr(video, 'series_imdb_id') else None
        else:
            imdb_id = video.imdb_id if hasattr(video, 'imdb_id') else None
        
        if imdb_id:
            # Ensure it's in the format ttXXXXXXX
            imdb_id = str(imdb_id)
            if not imdb_id.startswith('tt'):
                imdb_id = "tt{}".format(imdb_id)
            return imdb_id
        return None

    def _create_search_task(self, video, language):
        """Create a search task and return the task ID."""
        if self.session is None:
            logger.warning("Session not initialized")
            return None

        # Per API docs, these fields are REQUIRED for /search:
        # - filename
        # - filesize 
        # - hashes[opensubtitles]
        
        payload = {}

        # Add filename (required)
        if hasattr(video, 'name') and video.name:
            filename = os.path.basename(video.name)
            payload['filename'] = filename
        else:
            logger.warning("No filename available for video")
            return None

        # Add file size (required)
        if hasattr(video, 'size') and video.size:
            payload['filesize'] = str(video.size)
        else:
            logger.warning("No file size available for video")
            return None

        # Add OpenSubtitles hash (required)
        if hasattr(video, 'name') and video.name and os.path.exists(video.name):
            try:
                video_hash = hash_opensubtitles(video.name)
                if video_hash:
                    payload['hashes[opensubtitles]'] = video_hash
                else:
                    logger.warning("Could not compute hash for %s", video.name)
                    return None
            except (IOError, OSError) as e:
                logger.warning("Error computing hash for %s: %s", video.name, e)
                return None
        else:
            logger.warning("File does not exist, cannot compute hash: %s", video.name if hasattr(video, 'name') else 'unknown')
            return None

        # Optional: Add language (convert to 2-letter code)
        if language and hasattr(language, 'alpha2') and language.alpha2:
            payload['language'] = language.alpha2

        # Optional: encoding and format preferences
        payload['encoding'] = 'UTF-8'
        payload['format'] = 'subrip'

        try:
            logger.debug("Creating search task with payload: %s", payload)
            response = self.session.post(
                "{}/search".format(API_BASE_URL),
                data=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data.get('id')
            
            if not task_id:
                logger.warning("No task ID in response")
                return None
                
            logger.debug("Created task: %s", task_id)
            return task_id

        except Timeout:
            logger.warning("Request timed out while creating search task")
            return None
        except HTTPError as error:
            error_msg = "HTTP error {} while creating search task".format(error.response.status_code)
            try:
                error_data = error.response.json()
                logger.warning("%s: %s", error_msg, error_data)
            except Exception:
                logger.warning("%s: %s", error_msg, error.response.text)
            return None
        except RequestException as error:
            logger.warning("Request error while creating search task: %s", error)
            return None
        except Exception as error:
            logger.error("Unexpected error creating search task: %s", error)
            return None

    def _wait_for_task(self, task_id):
        """Poll the task endpoint until completion or timeout."""
        if self.session is None:
            logger.warning("Session not initialized")
            return None

        start_time = time.time()
        while time.time() - start_time < TASK_MAX_WAIT_SECONDS:
            try:
                response = self.session.get(
                    "{}/tasks/{}".format(API_BASE_URL, task_id),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                
                task_data = response.json()
                status = task_data.get('status')
                
                if status == 'completed':
                    return task_data
                elif status in ['failed', 'error']:
                    logger.warning(
                        "Task %s failed with status: %s, data: %s", 
                        task_id, 
                        status, 
                        task_data
                    )
                    return None
                
                # Wait before polling again
                time.sleep(TASK_POLL_INTERVAL_SECONDS)
                
            except Exception as error:
                logger.warning("Error polling task %s: %s", task_id, error)
                return None
        
        logger.warning("Task %s timed out", task_id)
        return None

    def query(self, language, video):
        """Search for subtitles."""
        if self.session is None:
            logger.warning("Session not initialized")
            return []

        # Create search task
        task_id = self._create_search_task(video, language)
        if not task_id:
            return []

        # Wait for task completion
        task_result = self._wait_for_task(task_id)
        if not task_result:
            return []

        # Extract subtitle information from result
        result_data = task_result.get('result', {})
        subtitles_list = result_data.get('subtitles', [])
        
        if not subtitles_list:
            logger.debug("No subtitles found in task result")
            return []

        subtitles = []
        for sub_data in subtitles_list:
            try:
                # Get hash if available
                file_hash = None
                if hasattr(video, 'hashes'):
                    file_hash = video.hashes.get('opensubtitles')

                # Get IMDB ID
                imdb_id = self._get_imdb_id(video)

                # Extract video attributes
                title = None
                year = None
                season = None
                episode = None
                
                if isinstance(video, Episode):
                    title = video.series
                    year = video.year
                    season = video.season
                    episode = video.episode
                else:
                    title = video.title
                    year = video.year

                # Create subtitle object
                subtitle = KickAssSubtitlesSubtitle(
                    language=language,
                    page_link="https://kickasssubtitles.com",
                    task_id=task_id,
                    file_hash=file_hash,
                    imdb_id=imdb_id,
                    title=title,
                    year=year,
                    season=season,
                    episode=episode,
                )
                
                # Store subtitle content for later download
                subtitle.subtitle_extension = sub_data.get('extension', 'srt')
                subtitle.subtitle_content_b64 = sub_data.get('contents_base64')
                
                if subtitle.subtitle_content_b64:
                    subtitles.append(subtitle)
                
            except Exception as e:
                logger.warning("Error creating subtitle object: %s", e)
                continue

        logger.debug("Found %d subtitles", len(subtitles))
        return subtitles

    def list_subtitles(self, video, languages):
        """List all available subtitles."""
        subtitles = []
        for language in languages:
            subtitles.extend(self.query(language, video))
        return subtitles

    def download_subtitle(self, subtitle):
        """Download subtitle content.
        
        Since the subtitle content is already available in base64 format
        from the search API response, we just need to decode it.
        """
        if not subtitle.subtitle_content_b64:
            logger.warning("No subtitle content available")
            return

        try:
            # Decode the base64 content
            subtitle.content = base64.b64decode(subtitle.subtitle_content_b64)
            logger.debug("Successfully decoded subtitle content")
            
        except Exception as error:
            logger.warning(
                "Error decoding subtitle content: %s",
                error,
            )
