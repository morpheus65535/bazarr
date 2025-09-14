# coding=utf-8

import logging
import requests
from app.config import settings


def get_plex_libraries_with_paths():
    """
    Get Plex library sections with their location paths.
    Returns a dictionary with movie_paths and series_paths arrays.
    
    This utility requires OAuth authentication and is used for Autopulse integration.
    """
    try:
        # Only works with OAuth authentication
        if settings.plex.get('auth_method') != 'oauth':
            return {'movie_paths': [], 'series_paths': []}
            
        # Get decrypted token and server URL directly from OAuth system
        from api.plex.oauth import get_decrypted_token
        decrypted_token = get_decrypted_token()
        server_url = settings.plex.get('server_url')
        
        if not decrypted_token or not server_url:
            return {'movie_paths': [], 'series_paths': []}
        
        # Get library sections
        response = requests.get(
            f"{server_url}/library/sections",
            headers={'X-Plex-Token': decrypted_token, 'Accept': 'application/json'},
            timeout=5,
            verify=False
        )
        
        if response.status_code != 200:
            return {'movie_paths': [], 'series_paths': []}
        
        data = response.json()
        if 'MediaContainer' not in data or 'Directory' not in data['MediaContainer']:
            return {'movie_paths': [], 'series_paths': []}
        
        movie_paths = []
        series_paths = []
        
        # Process library sections to extract paths
        sections = data['MediaContainer']['Directory']
        for section in sections:
            section_type = section.get('type')
            section_key = section.get('key')
            
            if section_type in ['movie', 'show']:
                locations = _get_library_locations(server_url, section_key, decrypted_token)
                if section_type == 'movie':
                    movie_paths.extend(locations)
                elif section_type == 'show':
                    series_paths.extend(locations)
        
        return {
            'movie_paths': movie_paths,
            'series_paths': series_paths
        }
        
    except Exception as e:
        logging.debug(f"BAZARR could not fetch Plex library paths: {e}")
        return {'movie_paths': [], 'series_paths': []}


def _get_library_locations(server_url, section_key, token):
    """Get the locations for a specific Plex library section."""
    try:
        response = requests.get(
            f"{server_url}/library/sections/{section_key}",
            headers={'X-Plex-Token': token, 'Accept': 'application/json'},
            timeout=5,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'MediaContainer' in data and 'Directory' in data['MediaContainer']:
                directories = data['MediaContainer']['Directory']
                if directories and len(directories) > 0:
                    directory = directories[0]
                    locations = directory.get('Location', [])
                    if isinstance(locations, list):
                        return [loc.get('path', '') for loc in locations if loc.get('path')]
                    elif isinstance(locations, dict):
                        path = locations.get('path', '')
                        return [path] if path else []
        return []
    except Exception as e:
        logging.debug(f"Failed to get locations for library section {section_key}: {e}")
        return []
