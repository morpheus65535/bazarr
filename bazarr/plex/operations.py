# coding=utf-8
import logging
from datetime import datetime
import requests
from app.config import settings, write_config
from plexapi.server import PlexServer

logger = logging.getLogger(__name__)
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

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
    Searches across all configured movie libraries.

    :param movie_metadata: Metadata object containing the movie's IMDb ID.
    """
    try:
        plex = get_plex_server()
        movie_libraries = settings.plex.movie_library
        
        # Ensure we have a list
        if not isinstance(movie_libraries, list):
            movie_libraries = [movie_libraries] if movie_libraries else []
        
        if not movie_libraries:
            logger.debug("No movie libraries configured in Plex settings")
            return
        
        # Search through all configured movie libraries
        for library_name in movie_libraries:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                video = library.getGuid(guid=movie_metadata.imdbId)
                update_added_date(video, datetime.now().strftime(DATETIME_FORMAT))
                logger.debug(f"Updated added date for movie in library '{library_name}'")
                return  # Success - no need to check other libraries
            except Exception as lib_error:
                # Movie not found in this library, try next one
                logger.debug(f"Movie not found in library '{library_name}': {lib_error}")
                continue
        
        # If we get here, movie wasn't found in any library
        logger.warning(f"Movie with IMDB ID {movie_metadata.imdbId} not found in any configured Plex movie library")
        
    except Exception as e:
        logger.error(f"Error in plex_set_movie_added_date_now: {e}")


def plex_set_episode_added_date_now(episode_metadata) -> None:
    """
    Update the added date of a TV episode in Plex to the current datetime.
    Searches across all configured series libraries.

    :param episode_metadata: Metadata object containing the episode's IMDb ID, season, and episode number.
    """
    try:
        plex = get_plex_server()
        series_libraries = settings.plex.series_library
        
        # Ensure we have a list
        if not isinstance(series_libraries, list):
            series_libraries = [series_libraries] if series_libraries else []
        
        if not series_libraries:
            logger.debug("No series libraries configured in Plex settings")
            return
        
        # Search through all configured series libraries
        for library_name in series_libraries:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                show = library.getGuid(episode_metadata.imdbId)
                episode = show.episode(season=episode_metadata.season, episode=episode_metadata.episode)
                update_added_date(episode, datetime.now().strftime(DATETIME_FORMAT))
                logger.debug(f"Updated added date for episode in library '{library_name}'")
                return  # Success - no need to check other libraries
            except Exception as lib_error:
                # Show not found in this library, try next one
                logger.debug(f"Show not found in library '{library_name}': {lib_error}")
                continue
        
        # If we get here, show wasn't found in any library
        logger.warning(f"Show with IMDB ID {episode_metadata.imdbId} not found in any configured Plex series library")
        
    except Exception as e:
        logger.error(f"Error in plex_set_episode_added_date_now: {e}")


def plex_update_library(is_movie_library: bool) -> None:
    """
    Trigger a library update for the specified library type.
    Updates all configured libraries of the given type.

    :param is_movie_library: True for movie library, False for series library.
    """
    try:
        plex = get_plex_server()
        library_names = settings.plex.movie_library if is_movie_library else settings.plex.series_library
        
        # Ensure we have a list
        if not isinstance(library_names, list):
            library_names = [library_names] if library_names else []
        
        if not library_names:
            library_type = "movie" if is_movie_library else "series"
            logger.debug(f"No {library_type} libraries configured in Plex settings")
            return
        
        # Update all configured libraries
        updated_count = 0
        for library_name in library_names:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                library.update()
                logger.info(f"Triggered update for library: {library_name}")
                updated_count += 1
            except Exception as lib_error:
                logger.error(f"Failed to update library '{library_name}': {lib_error}")
                continue
        
        if updated_count > 0:
            logger.debug(f"Successfully triggered update for {updated_count} libraries")
        else:
            logger.warning("Failed to update any Plex libraries")
            
    except Exception as e:
        logger.error(f"Error in plex_update_library: {e}")


def plex_refresh_item(imdb_id: str, is_movie: bool, season: int = None, episode: int = None) -> None:
    """
    Refresh a specific item in Plex instead of scanning the entire library.
    This is much more efficient than a full library scan when subtitles are added.
    Searches across all configured libraries of the appropriate type.

    :param imdb_id: IMDB ID of the content
    :param is_movie: True for movie, False for TV episode
    :param season: Season number for TV episodes
    :param episode: Episode number for TV episodes
    """
    try:
        plex = get_plex_server()
        library_names = settings.plex.movie_library if is_movie else settings.plex.series_library
        
        # Ensure we have a list
        if not isinstance(library_names, list):
            library_names = [library_names] if library_names else []
        
        if not library_names:
            library_type = "movie" if is_movie else "series"
            logger.debug(f"No {library_type} libraries configured in Plex settings")
            return
        
        # Search through all configured libraries
        for library_name in library_names:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                
                if is_movie:
                    # Refresh specific movie
                    item = library.getGuid(f"imdb://{imdb_id}")
                    item.refresh()
                    logger.info(f"Refreshed movie in '{library_name}': {item.title} (IMDB: {imdb_id})")
                    return  # Success - no need to check other libraries
                else:
                    # Refresh specific episode
                    show = library.getGuid(f"imdb://{imdb_id}")
                    episode_item = show.episode(season=season, episode=episode)
                    episode_item.refresh()
                    logger.info(f"Refreshed episode in '{library_name}': {show.title} S{season:02d}E{episode:02d} (IMDB: {imdb_id})")
                    return  # Success - no need to check other libraries
                    
            except Exception as lib_error:
                # Item not found in this library, try next one
                logger.debug(f"Item not found in library '{library_name}': {lib_error}")
                continue
        
        # If we get here, item wasn't found in any library - fall back to full update
        logger.warning(f"Item (IMDB: {imdb_id}) not found in any configured library, falling back to library update")
        plex_update_library(is_movie)
            
    except Exception as e:
        logger.warning(f"Failed to refresh specific item (IMDB: {imdb_id}), falling back to library update: {e}")
        # Fallback to full library update if specific refresh fails
        plex_update_library(is_movie)
