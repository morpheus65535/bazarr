# coding=utf-8

from flask import request
from flask_restful import Resource

from ..utils import authenticate
from indexer.movies.local.movies_indexer import get_movies_metadata
from database import TableMovies
from list_subtitles import store_subtitles_movie


class MoviesAdd(Resource):
    @authenticate
    def post(self):
        # add a new movie to database
        tmdbId = request.args.get('tmdbid')
        rootdir_id = request.args.get('rootdir_id')
        directory = request.args.get('directory')
        movies_metadata = get_movies_metadata(tmdbid=tmdbId, root_dir_id=rootdir_id, dir_name=directory)
        if movies_metadata and movies_metadata['path']:
            try:
                result = TableMovies.insert(movies_metadata).execute()
            except Exception:
                pass
            else:
                if result:
                    store_subtitles_movie(movies_metadata['path'])
