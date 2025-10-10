# coding=utf-8
import logging
from datetime import datetime
import requests
from app.config import settings, write_config
from plexapi.server import PlexServer

logger = logging.getLogger(__name__)


def get_plex_server() -> PlexServer:
    """Connect to the Plex server and return the server instance."""
    from api.plex.security import TokenManager, get_or_create_encryption_key, encrypt_api_key
    
    session = requests.Session()
    session.verify = False
    
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
            
            plex_server = PlexServer(server_url, decrypted_token, session=session)
            
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
            
            plex_server = PlexServer(baseurl, decrypted_apikey, session=session)
        
        return plex_server
            
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
        update_added_date(video, datetime.now().isoformat())
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
        update_added_date(episode, datetime.now().isoformat())
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


def plex_refresh_item(imdb_id: str, is_movie: bool, season: int = None, episode: int = None) -> None:
    """
    Refresh a specific item in Plex instead of scanning the entire library.
    This is much more efficient than a full library scan when subtitles are added.

    :param imdb_id: IMDB ID of the content
    :param is_movie: True for movie, False for TV episode
    :param season: Season number for TV episodes
    :param episode: Episode number for TV episodes
    """
    try:
        plex = get_plex_server()
        library_name = settings.plex.movie_library if is_movie else settings.plex.series_library
        library = plex.library.section(library_name)
        
        if is_movie:
            # Refresh specific movie
            item = library.getGuid(f"imdb://{imdb_id}")
            item.refresh()
            logger.info(f"Refreshed movie: {item.title} (IMDB: {imdb_id})")
        else:
            # Refresh specific episode
            show = library.getGuid(f"imdb://{imdb_id}")
            episode_item = show.episode(season=season, episode=episode)
            episode_item.refresh()
            logger.info(f"Refreshed episode: {show.title} S{season:02d}E{episode:02d} (IMDB: {imdb_id})")
            
    except Exception as e:
        logger.warning(f"Failed to refresh specific item (IMDB: {imdb_id}), falling back to library update: {e}")
        # Fallback to full library update if specific refresh fails
        plex_update_library(is_movie)
