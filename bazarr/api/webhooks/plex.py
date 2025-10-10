# coding=utf-8

import json
import requests
import os
import logging

from flask_restx import Resource, Namespace, reqparse
from bs4 import BeautifulSoup as bso

from app.database import TableEpisodes, TableShows, TableMovies, database, select
from subtitles.mass_download import episode_download_subtitles, movies_download_subtitles
from app.logger import logger
from ..plex.security import sanitize_log_data

from ..utils import authenticate


api_ns_webhooks_plex = Namespace('Webhooks Plex', description='Webhooks endpoint that can be configured in Plex to '
                                                              'trigger a subtitles search when playback start.')


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
            
            if event not in ['media.play']:
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
                    episode_download_subtitles(no=sonarrEpisodeId.sonarrEpisodeId, send_progress=True)
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
