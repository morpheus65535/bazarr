# coding=utf-8
import logging
from datetime import datetime
from app.config import settings, write_config
from plexapi.server import PlexServer

logger = logging.getLogger(__name__)

# Constants
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_plex_server() -> PlexServer:
    """Connect to the Plex server and return the server instance."""
    from api.plex.security import TokenManager, get_or_create_encryption_key, encrypt_api_key
    
    try:
        auth_method = settings.plex.get('auth_method', 'apikey')
        
        if auth_method == 'oauth':
            # OAuth authentication - use encrypted token and configured server URL
            
            encrypted_token = settings.plex.get('token')
            if not encrypted_token:
                raise ValueError("OAuth token not found. Please re-authenticate with Plex.")
            
            # Get or create encryption key
            encryption_key = get_or_create_encryption_key(settings.plex, 'encryption_key')
            token_manager = TokenManager(encryption_key)
            
            try:
                decrypted_token = token_manager.decrypt(encrypted_token)
            except Exception as e:
                logger.error(f"Failed to decrypt OAuth token: {type(e).__name__}")
                raise ValueError("Invalid OAuth token. Please re-authenticate with Plex.")
            
            # Use configured OAuth server URL
            server_url = settings.plex.get('server_url')
            if not server_url:
                raise ValueError("Server URL not configured. Please select a Plex server.")
            
            return PlexServer(server_url, decrypted_token)
            
        else:
            # Manual/API key authentication - always use encryption now
            protocol = "https://" if settings.plex.ssl else "http://"
            baseurl = f"{protocol}{settings.plex.ip}:{settings.plex.port}"
            
            apikey = settings.plex.get('apikey')
            if not apikey:
                raise ValueError("API key not configured. Please configure Plex authentication.")
            
            # Auto-encrypt plain text API keys
            if not settings.plex.get('apikey_encrypted', False):
                logger.info("Auto-encrypting plain text API key")
                encrypt_api_key()
                apikey = settings.plex.get('apikey')  # Get the encrypted version
            
            # Decrypt the API key
            encryption_key = get_or_create_encryption_key(settings.plex, 'encryption_key')
            token_manager = TokenManager(encryption_key)
            
            try:
                decrypted_apikey = token_manager.decrypt(apikey)
            except Exception as e:
                logger.error(f"Failed to decrypt API key: {type(e).__name__}")
                raise ValueError("Invalid encrypted API key. Please reconfigure Plex authentication.")
            
            return PlexServer(baseurl, decrypted_apikey)
            
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
