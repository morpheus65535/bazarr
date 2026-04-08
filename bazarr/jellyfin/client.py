# coding=utf-8

import logging
import os

import requests

logger = logging.getLogger(__name__)


class JellyfinClient:
    """Thin HTTP client for the Jellyfin REST API."""

    def __init__(self, url: str, api_key: str):
        self.base_url = url.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False

        bazarr_version = os.environ.get('BAZARR_VERSION', 'unknown')
        self.session.headers.update({
            'Authorization': (
                f'MediaBrowser Client="Bazarr", Device="Bazarr", '
                f'DeviceId="bazarr", Version="{bazarr_version}", '
                f'Token="{api_key}"'
            ),
            'Content-Type': 'application/json',
        })

    def _url(self, path: str) -> str:
        return f'{self.base_url}{path}'

    def get(self, path: str, params: dict = None) -> requests.Response:
        response = self.session.get(self._url(path), params=params, timeout=30)
        response.raise_for_status()
        return response

    def post(self, path: str, json: dict = None, params: dict = None) -> requests.Response:
        response = self.session.post(self._url(path), json=json, params=params, timeout=30)
        response.raise_for_status()
        return response

    def get_system_info(self) -> dict:
        """GET /System/Info — returns server name, version, id."""
        return self.get('/System/Info').json()

    def get_libraries(self) -> list:
        """GET /Library/VirtualFolders — returns all library folders."""
        return self.get('/Library/VirtualFolders').json()

    def get_items(self, params: dict) -> list:
        """GET /Items — search/browse items with query parameters."""
        data = self.get('/Items', params=params).json()
        return data.get('Items', [])

    def get_episodes(self, series_id: str, season: int) -> list:
        """GET /Shows/{seriesId}/Episodes — list episodes for a season."""
        data = self.get(f'/Shows/{series_id}/Episodes', params={
            'season': season,
            'fields': 'ProviderIds',
        }).json()
        return data.get('Items', [])

    def refresh_item(self, item_id: str) -> None:
        """POST /Items/{itemId}/Refresh — trigger metadata refresh for a specific item."""
        self.post(f'/Items/{item_id}/Refresh', params={
            'metadataRefreshMode': 'ValidationOnly',
            'imageRefreshMode': 'None',
            'replaceAllMetadata': 'false',
            'replaceAllImages': 'false',
        })

    def report_media_updated(self, path: str) -> None:
        """POST /Library/Media/Updated — notify Jellyfin of filesystem changes.

        Triggers filesystem change detection for the given path.
        """
        self.post('/Library/Media/Updated', json={
            'Updates': [{'Path': path, 'UpdateType': 'Modified'}],
        })

