# coding=utf-8
import logging

from flask_restx import Resource, Namespace, reqparse

from app.database import TableEpisodes, TableShows, database, select
from sonarr.sync.series import update_one_series
from subtitles.mass_download import episode_download_subtitles
from subtitles.indexer.series import store_subtitles
from utilities.path_mappings import path_mappings


from ..utils import authenticate


api_ns_webhooks_sonarr = Namespace('Webhooks Sonarr', description='Webhooks to trigger subtitles search based on '
                                                                  'Sonarr webhooks or Sonarr file IDs.')


@api_ns_webhooks_sonarr.route('webhooks/sonarr')
class WebHooksSonarr(Resource):

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('sonarr_episodefile_id', type=int, required=False, help='Movie file ID')
    post_request_parser.add_argument('eventType', type=str, required=False, help='Event type', location='json')
    post_request_parser.add_argument('episodeFiles', type=list, required=False, help='Episode file details payload', location='json')
    post_request_parser.add_argument('series', type=dict, required=False, help='Series details payload', location='json')

    @authenticate
    @api_ns_webhooks_sonarr.doc(parser=post_request_parser)
    @api_ns_webhooks_sonarr.response(200, 'Success')
    @api_ns_webhooks_sonarr.response(401, 'Not Authenticated')
    @api_ns_webhooks_sonarr.response(422, 'Invalid request: need at least one of event type or episode file ID.')
    def post(self):
        """Search for missing subtitles for a specific episode file id"""
        args = self.post_request_parser.parse_args()
        event_type = args.get('eventType')
        sonarr_episodefile_id = args.get('sonarr_episodefile_id')

        if not event_type and not sonarr_episodefile_id:
            logging.debug('Invalid request: need at least one of event type or episode file ID.')
            return 'Invalid request: need at least one of event type or episode file ID.', 422

        logging.debug('Received Sonarr webhook event: %s', event_type)

        if event_type == 'Test':
            logging.debug('Received test hook, skipping database search.')
            return 'Received test hook, skipping database search.', 200

        episode_file_ids = []
        if sonarr_episodefile_id:
            episode_file_ids = [sonarr_episodefile_id]
        elif isinstance(args.get('episodeFiles'), list):
            episode_file_ids = [e.get('id') for e in args.get('episodeFiles', [])]
        if not episode_file_ids:
            logging.debug('No episode file IDs found in the webhook request. Nothing to do.')
            # Sonarr reports the webhook as 'unhealthy' and requires
            # user interaction if we return anything except 200s.
            return 'No episode file IDs found in the webhook request. Nothing to do.', 200

        # This webhook is often faster than the database update,
        # so we update the series first if we can.
        try:
            series_id = args.get('series', {}).get('id')
        except AttributeError:
            series_id = None

        if series_id:
            update_one_series(series_id, 'updated')

        for efid in episode_file_ids:
            episode = database.execute(
                select(TableEpisodes.sonarrEpisodeId, TableEpisodes.path)
                .select_from(TableEpisodes)
                .join(TableShows)
                .where(TableEpisodes.episode_file_id == efid)) \
                .first()

            if episode:
                store_subtitles(episode.path, path_mappings.path_replace(episode.path))
                episode_download_subtitles(no=episode.sonarrEpisodeId, send_progress=True)
            else:
                logging.debug('No episode found for episode file ID %s, skipping.', efid)
        return 'Finished processing subtitles.', 200
