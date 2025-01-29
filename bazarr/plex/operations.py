# coding=utf-8
from datetime import datetime
from app.config import settings
from plexapi.server import PlexServer
import logging

logger = logging.getLogger(__name__)

# Constants
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_plex_server() -> PlexServer:
    """Connect to the Plex server and return the server instance."""
    try:
        protocol = "https://" if settings.plex.ssl else "http://"
        baseurl = f"{protocol}{settings.plex.ip}:{settings.plex.port}"
        return PlexServer(baseurl, settings.plex.apikey)
    except Exception as e:
        logger.error(f"Failed to connect to Plex server: {e}")
        raise


def update_added_date(video, added_date: str) -> None:
    """Update the added date of a video in Plex."""
    try:
        updates = {"addedAt.value": added_date}
        video.edit(**updates)
        logger.info(f"Updated added date for {video.title} to {added_date}")
    except Exception as e:
        logger.error(f"Failed to update added date for {video.title}: {e}")
        raise


def plex_set_movie_added_date_now(movie_metadata) -> None:
    """
    Update the added date of a movie in Plex to the current datetime.

    :param movie_metadata: Metadata object containing the movie's IMDb ID.
    """
    try:
        plex = get_plex_server()
        library = plex.library.section(settings.plex.movie_library)
        video = library.getGuid(guid=movie_metadata.imdbId)
        current_date = datetime.now().strftime(DATETIME_FORMAT)
        update_added_date(video, current_date)
    except Exception as e:
        logger.error(f"Error in plex_set_movie_added_date_now: {e}")


def plex_set_episode_added_date_now(episode_metadata) -> None:
    """
    Update the added date of a TV episode in Plex to the current datetime.

    :param episode_metadata: Metadata object containing the episode's IMDb ID, season, and episode number.
    """
    try:
        plex = get_plex_server()
        library = plex.library.section(settings.plex.series_library)
        show = library.getGuid(episode_metadata.imdbId)
        episode = show.episode(season=episode_metadata.season, episode=episode_metadata.episode)
        current_date = datetime.now().strftime(DATETIME_FORMAT)
        update_added_date(episode, current_date)
    except Exception as e:
        logger.error(f"Error in plex_set_episode_added_date_now: {e}")


def plex_update_library(is_movie_library: bool) -> None:
    """
    Trigger a library update for the specified library type.

    :param is_movie_library: True for movie library, False for series library.
    """
    try:
        plex = get_plex_server()
        library_name = settings.plex.movie_library if is_movie_library else settings.plex.series_library
        library = plex.library.section(library_name)
        library.update()
        logger.info(f"Triggered update for library: {library_name}")
    except Exception as e:
        logger.error(f"Error in plex_update_library: {e}")