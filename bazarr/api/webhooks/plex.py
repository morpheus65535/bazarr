# coding=utf-8

import json
import requests
import os
import logging

from flask_restx import Resource, Namespace, reqparse
from bs4 import BeautifulSoup as bso

from app.database import TableEpisodes, TableShows, TableMovies, database, select
from app.config import settings
from subtitles.mass_download import episode_download_subtitles, movies_download_subtitles
from app.logger import logger
from ..plex.security import sanitize_log_data

from ..utils import authenticate


api_ns_webhooks_plex = Namespace('Webhooks Plex', description='Webhooks endpoint that can be configured in Plex to '
                                                              'trigger a subtitles search when playback start.')


def _is_relevant_server(payload):
    """Check if webhook is from our configured Plex server."""
    instance_name = settings.general.get('instance_name', 'Bazarr')
    
    server_uuid = payload.get('Server', {}).get('uuid', '')
    configured_server = settings.plex.get('server_machine_id', '')
    
    if not configured_server:
        # No server configured, process all (backward compatible)
        logger.debug(f'PLEX WEBHOOK [{instance_name}]: No server configured, processing all')
        return True
    
    if not server_uuid:
        # Can't determine server from payload, process anyway
        logger.debug(f'PLEX WEBHOOK [{instance_name}]: No server UUID in payload, processing')
        return True
    
    if server_uuid == configured_server:
        logger.debug(f'PLEX WEBHOOK [{instance_name}]: Server UUID matches ({server_uuid[:8]}...)')
        return True
    
    logger.debug(f'PLEX WEBHOOK [{instance_name}]: Server UUID mismatch '
                f'(got {server_uuid[:8]}..., expected {configured_server[:8]}...), skipping')
    return False


def _is_relevant_library(payload):
    """Check if webhook is for a library this instance manages."""
    instance_name = settings.general.get('instance_name', 'Bazarr')
    
    metadata = payload.get('Metadata', {})
    library_section_id = metadata.get('librarySectionID')
    library_section_title = metadata.get('librarySectionTitle', '')
    media_type = metadata.get('type', '')
    
    # Determine which library config to check
    if media_type == 'episode':
        configured_lib_ids = settings.plex.get('series_library_ids', [])
        configured_lib_names = settings.plex.get('series_library', [])
    else:
        configured_lib_ids = settings.plex.get('movie_library_ids', [])
        configured_lib_names = settings.plex.get('movie_library', [])
    
    # Normalize to lists
    if isinstance(configured_lib_ids, str):
        configured_lib_ids = [configured_lib_ids] if configured_lib_ids else []
    if isinstance(configured_lib_names, str):
        configured_lib_names = [configured_lib_names] if configured_lib_names else []
    
    # If no libraries configured, process all (backward compatible)
    if not configured_lib_ids and not configured_lib_names:
        logger.debug(f'PLEX WEBHOOK [{instance_name}]: No libraries configured, processing all')
        return True
    
    # Check by ID first (100% reliable)
    if configured_lib_ids and library_section_id:
        if str(library_section_id) in [str(lid) for lid in configured_lib_ids]:
            logger.debug(f'PLEX WEBHOOK [{instance_name}]: Library ID {library_section_id} matches')
            return True
    
    # Fallback to name matching
    if configured_lib_names and library_section_title:
        if library_section_title in configured_lib_names:
            logger.debug(f'PLEX WEBHOOK [{instance_name}]: Library name "{library_section_title}" matches')
            return True
    
    logger.debug(f'PLEX WEBHOOK [{instance_name}]: Library "{library_section_title}" '
                f'(ID: {library_section_id}) not configured, skipping')
    return False


@api_ns_webhooks_plex.route('webhooks/plex')
class WebHooksPlex(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('payload', type=str, required=True, help='Webhook payload')

    @authenticate
    @api_ns_webhooks_plex.doc(parser=post_request_parser)
    @api_ns_webhooks_plex.response(200, 'Success')
    @api_ns_webhooks_plex.response(204, 'Unhandled event or no processable data')
    @api_ns_webhooks_plex.response(400, 'Bad request - missing required data')
    @api_ns_webhooks_plex.response(401, 'Not Authenticated')
    @api_ns_webhooks_plex.response(404, 'IMDB series/movie ID not found')
    @api_ns_webhooks_plex.response(500, 'Internal server error')
    def post(self):
        """Trigger subtitles search on play media event in Plex"""
        try:
            args = self.post_request_parser.parse_args()
            json_webhook = args.get('payload')
            
            if not json_webhook:
                logger.debug('PLEX WEBHOOK: No payload received')
                return "No payload found in request", 400
            
            parsed_json_webhook = json.loads(json_webhook)
            
            # Check if this is a valid Plex webhook (should have 'event' field)
            if 'event' not in parsed_json_webhook:
                logger.debug('PLEX WEBHOOK: Invalid payload - missing "event" field')
                return "Invalid webhook payload - missing event field", 400
            
            event = parsed_json_webhook['event']
            
            if event not in ['media.play', 'playback.started']:
                logger.debug('PLEX WEBHOOK: Ignoring unhandled event "%s"', event)
                return 'Unhandled event', 204
            
            # Check if Metadata key exists in the payload
            if 'Metadata' not in parsed_json_webhook:
                logger.debug('PLEX WEBHOOK: No Metadata in payload for event "%s"', event)
                return "No Metadata found in JSON request body", 400
                
            if 'Guid' not in parsed_json_webhook['Metadata']:
                logger.debug('PLEX WEBHOOK: No GUID in Metadata for event "%s". Probably a pre-roll video.', event)
                return "No GUID found in JSON request body", 204
                
        except json.JSONDecodeError as e:
            logger.debug('PLEX WEBHOOK: Failed to parse JSON. Error: %s. Payload: %s', 
                        str(e), sanitize_log_data(json_webhook) if json_webhook else 'None')
            return "Invalid JSON payload", 400
        except Exception as e:
            logger.error('PLEX WEBHOOK: Unexpected error: %s', str(e))
            return "Unexpected error processing webhook", 500

        # Filter by server UUID - skip if from different Plex server
        if not _is_relevant_server(parsed_json_webhook):
            return 'Event from different Plex server, skipping', 204
        
        # Filter by library ID/name - skip if for different library
        if not _is_relevant_library(parsed_json_webhook):
            return 'Event for different library, skipping', 204

        media_type = parsed_json_webhook['Metadata']['type']

        if media_type == 'episode':
            season = parsed_json_webhook['Metadata']['parentIndex']
            episode = parsed_json_webhook['Metadata']['index']
        else:
            season = episode = None

        ids = []
        for item in parsed_json_webhook['Metadata']['Guid']:
            splitted_id = item['id'].split('://')
            if len(splitted_id) == 2:
                ids.append({splitted_id[0]: splitted_id[1]})
        if not ids:
            return 'No GUID found', 204

        if media_type == 'episode':
            try:
                episode_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
                r = requests.get(f'https://imdb.com/title/{episode_imdb_id}',
                                 headers={"User-Agent": os.environ["SZ_USER_AGENT"]})
                soup = bso(r.content, "html.parser")
                script_tag = soup.find(id='__NEXT_DATA__')
                script_tag_json = script_tag.string
                show_metadata_dict = json.loads(script_tag_json)
                series_imdb_id = show_metadata_dict['props']['pageProps']['aboveTheFoldData']['series']['series']['id']
            except Exception:
                logger.debug('BAZARR is unable to get series IMDB id.')
                return 'IMDB series ID not found', 404
            else:
                sonarrEpisodeId = database.execute(
                    select(TableEpisodes.sonarrEpisodeId)
                    .select_from(TableEpisodes)
                    .join(TableShows)
                    .where(TableShows.imdbId == series_imdb_id,
                           TableEpisodes.season == season,
                           TableEpisodes.episode == episode)) \
                    .first()

                if sonarrEpisodeId:
                    episode_download_subtitles(no=sonarrEpisodeId.sonarrEpisodeId)
        else:
            try:
                movie_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
            except Exception:
                logger.debug('BAZARR is unable to get movie IMDB id.')
                return 'IMDB movie ID not found', 404
            else:
                radarrId = database.execute(
                    select(TableMovies.radarrId)
                    .where(TableMovies.imdbId == movie_imdb_id)) \
                    .first()

                if radarrId:
                    movies_download_subtitles(no=radarrId.radarrId)

        return '', 200
