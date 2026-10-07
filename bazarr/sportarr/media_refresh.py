"""Refresh the media-server path after a sports subtitle changes."""

import logging
import os

from app.config import settings
from jellyfin.operations import get_jellyfin_client
from plex.operations import get_plex_server
from utilities.path_mappings import path_mappings


def _within(path, root):
    path = path.replace('\\', '/').rstrip('/')
    root = root.replace('\\', '/').rstrip('/')
    if len(root) >= 2 and root[1] == ':':
        path, root = path.casefold(), root.casefold()
    return path == root or path.startswith(root + '/')


def _matching_path(candidates, roots):
    return next(
        (path for path in candidates for root in roots
         if isinstance(root, str) and _within(path, root)),
        None,
    )


def refresh_sports_media_servers(video_path):
    """Ask configured servers to refresh only the matching sports path."""
    sportarr_path = path_mappings.path_replace_reverse_sports(video_path)
    candidates = list(dict.fromkeys(path for path in (video_path, sportarr_path) if path))

    if settings.general.use_plex and settings.plex.update_series_library:
        try:
            server = get_plex_server()
            matched = False
            for section in server.library.sections():
                path = _matching_path(candidates, section.locations)
                if path:
                    section.update(path=os.path.dirname(path.replace('\\', '/')))
                    matched = True
                    break
            if not matched:
                logging.warning('No Plex library path matches this sports file; check media-server mounts')
        except Exception:
            logging.exception('Could not refresh the matching Plex sports path')

    if settings.general.use_jellyfin and settings.jellyfin.update_series_library:
        try:
            client = get_jellyfin_client()
            libraries = client.get_libraries()
            roots = [root for library in libraries for root in library.get('Locations', [])]
            path = _matching_path(candidates, roots)
            if path:
                client.report_media_updated(path)
            elif roots:
                logging.warning('No Jellyfin library path matches this sports file; check media-server mounts')
            else:
                logging.warning('Jellyfin did not return library paths; trying the Sportarr video path')
                client.report_media_updated(sportarr_path or video_path)
        except Exception:
            logging.exception('Could not refresh the Jellyfin sports path')
