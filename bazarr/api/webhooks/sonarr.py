# coding=utf-8
import logging

from flask_restx import Resource, Namespace, fields

from app.database import TableEpisodes, TableShows, database, select
from sonarr.sync.series import update_one_series
from subtitles.mass_download import episode_download_subtitles
from subtitles.indexer.series import store_subtitles
from utilities.path_mappings import path_mappings


from ..utils import authenticate


api_ns_webhooks_sonarr = Namespace('Webhooks Sonarr', description='Webhooks to trigger subtitles search based on '
                                                                  'Sonarr webhooks')


@api_ns_webhooks_sonarr.route('webhooks/sonarr')
class WebHooksSonarr(Resource):

    episode_file_model = api_ns_webhooks_sonarr.model('SonarrEpisodeFile', {
        'id': fields.Integer(required=True, description='Episode file ID'),
    }, strict=False)
    
    series_model = api_ns_webhooks_sonarr.model('SonarrSeries', {
        'id': fields.Integer(required=True, description='Series ID'),
    }, strict=False)
    
    sonarr_webhook_model = api_ns_webhooks_sonarr.model('SonarrWebhook', {
        'episodeFiles': fields.List(fields.Nested(episode_file_model), required=False, description='List of episode files'),
        'series': fields.Nested(series_model, required=False, description='Full series details payload'),
        'eventType': fields.String(required=True, description='Type of event (e.g. Test)'),
    }, strict=False)

    @authenticate
    @api_ns_webhooks_sonarr.expect(sonarr_webhook_model, validate=True)
    @api_ns_webhooks_sonarr.response(200, 'Success')
    @api_ns_webhooks_sonarr.response(401, 'Not Authenticated')
    def post(self):
        """Search for missing subtitles based on Sonarr webhooks"""
        args = api_ns_webhooks_sonarr.payload
        event_type = args.get('eventType')

        logging.debug('Received Sonarr webhook event: %s', event_type)

        if event_type == 'Test':
            logging.debug('Received test hook, skipping database search.')
            return 'Received test hook, skipping database search.', 200


        # Sonarr hooks only differentiate a download starting vs. ending by
        # the inclusion of episodeFiles in the payload.
        episode_file_ids = [e.get('id') for e in args.get('episodeFiles', [])]

        if not episode_file_ids:
            logging.debug('No episode file IDs found in the webhook request. Nothing to do.')
            # Sonarr reports the webhook as 'unhealthy' and requires
            # user interaction if we return anything except 200s.
            return 'No episode file IDs found in the webhook request. Nothing to do.', 200

        # This webhook is often faster than the database update,
        # so we update the series first if we can.
        series_id = args.get('series', {}).get('id')
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
