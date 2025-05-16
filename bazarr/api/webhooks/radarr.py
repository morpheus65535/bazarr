# coding=utf-8
import logging

from flask_restx import Resource, Namespace, fields

from app.database import TableMovies, database, select
from radarr.sync.movies import update_one_movie
from subtitles.mass_download import movies_download_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from utilities.path_mappings import path_mappings

from ..utils import authenticate


api_ns_webhooks_radarr = Namespace('Webhooks Radarr', description='Webhooks to trigger subtitles search based on '
                                                                  'Radarr webhooks or Radarr file IDs. '
                                                                  'Requires at least one of eventType or '
                                                                  'radarr_movie_file_id to be sent in the request body.')


@api_ns_webhooks_radarr.route('webhooks/radarr')
class WebHooksRadarr(Resource):

    movie_model = api_ns_webhooks_radarr.model('RadarrMovie', {
        'id': fields.Integer(required=True, description='Movie ID'),
    }, strict=False)
        

    movie_file_model = api_ns_webhooks_radarr.model('RadarrMovieFile', {
        'id': fields.Integer(required=True, description='Movie file ID'),
    }, strict=False)

    radarr_webhook_model = api_ns_webhooks_radarr.model('RadarrWebhook', {
        'eventType': fields.String(required=True, description='Type of event (e.g. MovieAdded)'),
        'movieFile': fields.Nested(movie_file_model, required=False, description='Full movie file details payload'),
        'movie': fields.Nested(movie_model, required=False, description='Full movie details payload'),
        # Keep this field for backwards compatibility with user-scripts
        'radarr_movie_file_id': fields.Integer(required=False, description='Radarr movie file ID for use with user scripts. Takes precedence over movieFile'),
    }, strict=False)

    @authenticate
    @api_ns_webhooks_radarr.expect(radarr_webhook_model, validate=True)
    @api_ns_webhooks_radarr.response(200, 'Success')
    @api_ns_webhooks_radarr.response(401, 'Not Authenticated')
    @api_ns_webhooks_radarr.response(422, 'Invalid request: need at least one of event type or movie file ID.')
    def post(self):
        """Search for missing subtitles for a specific movie file id"""
        args = api_ns_webhooks_radarr.payload
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
            radarr_movie_file_id = args.get('movieFile', {}).get('id')

        if not radarr_movie_file_id:
            logging.debug('No movie file ID found in the webhook request. Nothing to do.')
            # Radarr reports the webhook as 'unhealthy' and requires
            # user interaction if we return anything except 200s.
            return 'No movie file ID found in the webhook request. Nothing to do.', 200

        # This webhook is often faster than the database update,
        # so we update the movie first if we can.
        radarr_id = args.get('movie', {}).get('id')
        if radarr_id:
            update_one_movie(radarr_id, 'updated')
            

        radarrMovieId = database.execute(
            select(TableMovies.radarrId, TableMovies.path)
            .where(TableMovies.movie_file_id == radarr_movie_file_id)) \
            .first()
        if not radarrMovieId:
            logging.debug('No movie file ID found in the database. Nothing to do.')
            return 'No movie file ID found in the database. Nothing to do.', 200
        
        store_subtitles_movie(radarrMovieId.path, path_mappings.path_replace_movie(radarrMovieId.path))
        movies_download_subtitles(no=radarrMovieId.radarrId)

        return 'Finished processing subtitles.', 200