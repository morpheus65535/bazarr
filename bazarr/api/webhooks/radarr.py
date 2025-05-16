# coding=utf-8
import logging

from flask_restx import Resource, Namespace, reqparse

from app.database import TableMovies, database, select
from radarr.sync.movies import update_one_movie
from subtitles.mass_download import movies_download_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from utilities.path_mappings import path_mappings

from ..utils import authenticate


api_ns_webhooks_radarr = Namespace('Webhooks Radarr', description='Webhooks to trigger subtitles search based on '
                                                                  'Radarr webhooks or Radarr file IDs.')


@api_ns_webhooks_radarr.route('webhooks/radarr')
class WebHooksRadarr(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarr_movie_file_id', type=int, required=False, help='Movie file ID')
    post_request_parser.add_argument('eventType', type=str, required=False, help='Event type', location='json')
    post_request_parser.add_argument('movieFile', type=dict, required=False, help='Episode file details payload', location='json')
    post_request_parser.add_argument('movie', type=dict, required=False, help='Episode file details payload', location='json')

    @authenticate
    @api_ns_webhooks_radarr.doc(parser=post_request_parser)
    @api_ns_webhooks_radarr.response(200, 'Success')
    @api_ns_webhooks_radarr.response(401, 'Not Authenticated')
    @api_ns_webhooks_radarr.response(422, 'Invalid request: need at least one of event type or movie file ID.')
    def post(self):
        """Search for missing subtitles for a specific movie file id"""
        args = self.post_request_parser.parse_args()

        event_type = args.get('eventType')
        radarr_movie_file_id = args.get('radarr_movie_file_id')

        if not event_type and not radarr_movie_file_id:
            logging.debug('Invalid request: need at least one of event type or movie file ID.')
            return 'Invalid request: need at least one of event type or movie file ID.', 422

        logging.debug('Received Radarr webhook event: %s', event_type)

        if event_type == 'Test':
            logging.debug('Received test hook, skipping database search.')
            return 'Received test hook, skipping database search.', 200

        if not radarr_movie_file_id:
            try:
                radarr_movie_file_id = args.get('movieFile', {}).get('id')
            except AttributeError:
                logging.debug('No movie file ID found in the webhook request. Nothing to do.')
                # Radarr reports the webhook as 'unhealthy' and requires
                # user interaction if we return anything except 200s.
                return 'No movie file ID found in the webhook request. Nothing to do.', 200

        # This webhook is often faster than the database update,
        # so we update the movie first if we can.
        try:
            radarr_id = args.get('movie', {}).get('id')
        except AttributeError:
            radarr_id = None

        if radarr_id:
            update_one_movie(radarr_id, 'updated')

        radarr_movie = database.execute(
            select(TableMovies.radarrId, TableMovies.path)
            .where(TableMovies.movie_file_id == radarr_movie_file_id)) \
            .first()
        if not radarr_movie:
            logging.debug('No movie file ID found in the database. Nothing to do.')
            return 'No movie file ID found in the database. Nothing to do.', 200
        
        store_subtitles_movie(radarr_movie.path, path_mappings.path_replace_movie(radarr_movie.path))
        movies_download_subtitles(no=radarr_movie.radarrId)

        return 'Finished processing subtitles.', 200