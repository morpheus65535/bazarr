# coding=utf-8

from flask import request
from flask_restx import Resource, Namespace

from app.database import TableMovies
from subtitles.mass_download import movies_download_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from utilities.path_mappings import path_mappings

from ..utils import authenticate


api_ns_webhooks_radarr = Namespace('webhooksRadarr', description='Webhooks Radarr API endpoint')


@api_ns_webhooks_radarr.route('webhooks/radarr')
class WebHooksRadarr(Resource):
    @authenticate
    def post(self):
        movie_file_id = request.form.get('radarr_moviefile_id')

        radarrMovieId = TableMovies.select(TableMovies.radarrId,
                                           TableMovies.path) \
            .where(TableMovies.movie_file_id == movie_file_id) \
            .dicts() \
            .get_or_none()

        if radarrMovieId:
            store_subtitles_movie(radarrMovieId['path'], path_mappings.path_replace_movie(radarrMovieId['path']))
            movies_download_subtitles(no=radarrMovieId['radarrId'])

        return '', 200
