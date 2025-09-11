# coding=utf-8

import logging
import requests
from urllib.parse import urlencode

from app.config import settings


def call_subtitle_webhook(subtitle_path, media_path, language, media_type):
    """
    Call Autopulse after subtitle download to trigger Plex metadata refresh.
    Uses Autopulse's automatic /triggers/manual endpoint.
    """
    # Check if Autopulse is enabled
    if not settings.plex.use_autopulse or not settings.plex.autopulse_host:
        return

    try:
        host = settings.plex.autopulse_host.strip()
        port = settings.plex.autopulse_port
        username = settings.plex.autopulse_username.strip()
        password = settings.plex.autopulse_password.strip()
        
        if not host:
            return

        # Build Autopulse manual trigger URL
        autopulse_url = f"http://{host}:{port}/triggers/manual"
        
        # Prepare query parameters for Autopulse
        params = {'path': media_path}
        
        # Build full URL with query parameters
        webhook_url = f"{autopulse_url}?{urlencode(params)}"
        
        # Setup authentication if provided
        auth = None
        if username and password:
            auth = (username, password)
        
        headers = {
            'User-Agent': 'Bazarr',
        }
        
        logging.debug(f"BAZARR calling Autopulse: {autopulse_url} for path: {media_path}")
        
        # Make the webhook call to Autopulse
        response = requests.get(
            webhook_url,
            auth=auth,
            headers=headers,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            logging.info(f"BAZARR Autopulse call successful for {media_path}")
        else:
            logging.warning(f"BAZARR Autopulse call failed with status {response.status_code} for {media_path}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"BAZARR Autopulse call failed for {media_path}: {str(e)}")
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling Autopulse for {media_path}: {str(e)}")


def test_autopulse_connection():
    """
    Test connection to Autopulse server.
    Returns (success: bool, message: str)
    """
    try:
        host = settings.plex.autopulse_host.strip()
        port = settings.plex.autopulse_port
        username = settings.plex.autopulse_username.strip()
        password = settings.plex.autopulse_password.strip()
        
        if not host:
            return False, "Autopulse host not configured"

        # Build Autopulse stats URL
        status_url = f"http://{host}:{port}/stats"
        
        # Setup authentication if provided
        auth = None
        if username and password:
            auth = (username, password)
        
        headers = {
            'User-Agent': 'Bazarr',
        }
        
        logging.debug(f"BAZARR testing Autopulse connection: {status_url}")
        
        # Test connection to Autopulse
        response = requests.get(
            status_url,
            auth=auth,
            headers=headers,
            timeout=10,
            verify=True
        )
        
        if response.status_code == 200:
            return True, "Autopulse connection successful"
        else:
            return False, f"Autopulse connection failed with status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Autopulse connection failed: {str(e)}"
    except Exception as e:
        return False, f"Autopulse connection error: {str(e)}"


def get_autopulse_config():
    """
    Get essential Plex configuration for Autopulse setup.
    Returns dict with config data or None if failed.
    """
    try:
        # Get the current Plex configuration from Bazarr's settings
        server_url = settings.plex.get('server_url', '')
        server_name = settings.plex.get('server_name', '')
        username = settings.plex.get('username', '')
        auth_method = settings.plex.get('auth_method', 'apikey')
        
        # Get configured library names from Bazarr settings
        movie_library = settings.plex.get('movie_library', '')
        series_library = settings.plex.get('series_library', '')
        
        # Get the decrypted token for Autopulse configuration
        key_existed = bool(getattr(settings.plex, 'encryption_key', None))
        if not key_existed:
            logging.warning("BAZARR no encryption key available for Autopulse config")
            return None
            
        # Get the encrypted token from settings
        encrypted_token = settings.plex.get('token') if auth_method == 'oauth' else settings.plex.get('apikey')
        if not encrypted_token:
            logging.warning("BAZARR no encrypted token available for Autopulse config")
            return None
        
        # Decrypt the token
        try:
            from api.plex.security import get_or_create_encryption_key, TokenManager
            key = get_or_create_encryption_key(settings.plex, 'encryption_key')
            token_manager = TokenManager(key)
            decrypted_token = token_manager.decrypt(encrypted_token)
        except Exception as e:
            logging.error(f"BAZARR token decryption failed for Autopulse config: {e}")
            return None
        
        if not decrypted_token or not server_url:
            logging.warning("BAZARR missing required Plex configuration for Autopulse")
            return None
        
        # Get basic libraries information
        libraries = []
        try:
            headers = {
                'X-Plex-Token': decrypted_token,
                'Accept': 'application/json'
            }
            
            response = requests.get(
                f"{server_url}/library/sections",
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'MediaContainer' in data and 'Directory' in data['MediaContainer']:
                    sections = data['MediaContainer']['Directory']
                    for section in sections:
                        if section.get('type') in ['movie', 'show']:
                            libraries.append({
                                'key': section.get('key', ''),
                                'title': section.get('title', ''),
                                'type': section.get('type', ''),
                                'locations': [loc.get('path', '') for loc in section.get('Location', [])]
                            })
        except Exception as e:
            logging.warning(f"BAZARR could not fetch libraries for Autopulse config: {e}")
        
        # Return simplified configuration data
        config_data = {
            'plex_url': server_url,
            'plex_token': decrypted_token,
            'server_name': server_name,
            'username': username,
            'auth_method': auth_method,
            'libraries': libraries,
            'configured_libraries': {
                'movie': movie_library,
                'series': series_library
            }
        }
        
        logging.info(f"BAZARR generated Autopulse config for server: {server_name}")
        return config_data
            
    except Exception as e:
        logging.error(f"BAZARR error generating Autopulse config: {str(e)}")
        return None
