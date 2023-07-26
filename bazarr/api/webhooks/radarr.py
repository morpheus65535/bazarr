# coding=utf-8

from flask_restx import Resource, Namespace, reqparse

from app.database import TableMovies, database, select
from subtitles.mass_download import movies_download_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from utilities.path_mappings import path_mappings

from ..utils import authenticate


api_ns_webhooks_radarr = Namespace('Webhooks Radarr', description='Webhooks to trigger subtitles search based on '
                                                                  'Radarr movie file ID')


@api_ns_webhooks_radarr.route('webhooks/radarr')
class WebHooksRadarr(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('radarr_moviefile_id', type=int, required=True, help='Movie file ID')

    @authenticate
    @api_ns_webhooks_radarr.doc(parser=post_request_parser)
    @api_ns_webhooks_radarr.response(200, 'Success')
    @api_ns_webhooks_radarr.response(401, 'Not Authenticated')
    def post(self):
        """Search for missing subtitles for a specific movie file id"""
        args = self.post_request_parser.parse_args()
        movie_file_id = args.get('radarr_moviefile_id')

        radarrMovieId = database.execute(
            select(TableMovies.radarrId, TableMovies.path)
            .where(TableMovies.movie_file_id == movie_file_id)) \
            .first()

        if radarrMovieId:
            store_subtitles_movie(radarrMovieId.path, path_mappings.path_replace_movie(radarrMovieId.path))
            movies_download_subtitles(no=radarrMovieId.radarrId)

        return '', 200
