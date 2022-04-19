# coding=utf-8

from flask import request
from flask_restful import Resource

from app.database import TableMovies
from get_subtitle.mass_download import movies_download_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from utilities.helper import path_mappings

from ..utils import authenticate


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
