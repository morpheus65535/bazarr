# coding=utf-8

import logging
import requests
from app.config import settings


def get_plex_libraries_with_paths() -> dict[str, list[str]]:
    """
    Retrieve the filesystem paths of all Plex movie and TV show libraries.

    This function queries the configured Plex server for its library
    sections and collects the root folder locations of every section whose
    type is either ``movie`` or ``show``. It only operates when Plex is
    configured to use OAuth authentication, since it relies on the
    decrypted OAuth token and the stored server URL to perform the request.
    If authentication is not OAuth-based, credentials are missing, the
    server responds with a non-successful status, the response payload is
    malformed, or any other error occurs, empty path lists are returned
    instead of raising. Failures are logged at debug level.

    :return: A dictionary with two keys, ``movie_paths`` and
        ``series_paths``, each mapping to a list of library root folder
        paths discovered on the Plex server. Both lists are empty when the
        paths cannot be retrieved.
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


def _get_library_locations(server_url: str, section_key: str, token: str) -> list[str]:
    """
    Retrieve the filesystem locations configured for a Plex library section.

    Queries the Plex server API endpoint for the given library section and
    extracts the paths of all configured locations from the returned
    ``MediaContainer`` payload. The request is performed without TLS
    certificate verification and with a short timeout. If the request fails,
    the server responds with a non-200 status code, the response structure
    is unexpected, or any other error occurs, an empty list is returned and
    the failure is logged at debug level rather than propagated.

    :param server_url: Base URL of the Plex server, including scheme and
        port, without a trailing slash.
    :param section_key: Identifier of the library section whose locations
        should be retrieved.
    :param token: Plex authentication token sent via the ``X-Plex-Token``
        header.
    :return: List of filesystem paths configured for the library section.
        Empty paths are omitted; an empty list is returned on any failure.
    """
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
