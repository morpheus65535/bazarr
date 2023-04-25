# coding=utf-8

from flask_restx import Resource, Namespace, reqparse

from app.database import TableEpisodes, TableShows, database, select
from subtitles.mass_download import episode_download_subtitles
from subtitles.indexer.series import store_subtitles
from utilities.path_mappings import path_mappings

from ..utils import authenticate


api_ns_webhooks_sonarr = Namespace('Webhooks Sonarr', description='Webhooks to trigger subtitles search based on '
                                                                  'Sonarr episode file ID')


@api_ns_webhooks_sonarr.route('webhooks/sonarr')
class WebHooksSonarr(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('sonarr_episodefile_id', type=int, required=True, help='Episode file ID')

    @authenticate
    @api_ns_webhooks_sonarr.doc(parser=post_request_parser)
    @api_ns_webhooks_sonarr.response(200, 'Success')
    @api_ns_webhooks_sonarr.response(401, 'Not Authenticated')
    def post(self):
        """Search for missing subtitles for a specific episode file id"""
        args = self.post_request_parser.parse_args()
        episode_file_id = args.get('sonarr_episodefile_id')

        sonarrEpisodeId = database.execute(
            select(TableEpisodes.sonarrEpisodeId, TableEpisodes.path)
            .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)
            .where(TableEpisodes.episode_file_id == episode_file_id)) \
            .first()

        if sonarrEpisodeId:
            store_subtitles(sonarrEpisodeId.path, path_mappings.path_replace(sonarrEpisodeId.path))
            episode_download_subtitles(no=sonarrEpisodeId.sonarrEpisodeId, send_progress=True)

        return '', 200
