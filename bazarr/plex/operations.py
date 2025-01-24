# coding=utf-8
from datetime import datetime
from app.config import settings
from plexapi.server import PlexServer
import logging

logger = logging.getLogger(__name__)


def plex_set_added_date_now(movie_metadata):
    try:
        if settings.plex.ssl:
            protocol_plex = "https://"
        else:
            protocol_plex = "http://"

        baseurl = f'{protocol_plex}{settings.plex.ip}:{settings.plex.port}'
        token = settings.plex.apikey
        plex = PlexServer(baseurl, token)
        library = plex.library.section(settings.plex.movie_library)
        video = library.getGuid(guid=movie_metadata.imdbId)
        # Get the current date and time in the desired format
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updates = {"addedAt.value": current_date}
        video.edit(**updates)
    except Exception as e:
        logger.error(f"A Plex error occurred: {e}")


def plex_update_library(is_movie):
    try:
        # Determine protocol based on SSL settings
        protocol_plex = "https://" if settings.plex.ssl else "http://"
        baseurl = f"{protocol_plex}{settings.plex.ip}:{settings.plex.port}"
        token = settings.plex.apikey

        # Connect to the Plex server
        plex = PlexServer(baseurl, token)

        # Select the library to update
        library_name = settings.plex.movie_library if is_movie else settings.plex.series_library
        library = plex.library.section(library_name)

        # Trigger update
        library.update()

    except Exception as e:
        logger.error(f"A Plex error occurred: {e}")
