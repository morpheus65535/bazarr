# coding=utf-8

import ast

from flask_restx import Resource, Namespace, fields, marshal

from app.database import TableMovies, database, select

from ..utils import authenticate

api_ns_movies_tags = Namespace('Movies Tags', description='List tags assigned to movies')


@api_ns_movies_tags.route('movies/tags')
class MoviesTags(Resource):
    get_response_model = api_ns_movies_tags.model('MoviesTagsGetResponse', {
        'tag': fields.String(),
    })

    @authenticate
    @api_ns_movies_tags.response(200, 'Success')
    @api_ns_movies_tags.response(401, 'Not Authenticated')
    def get(self):
        """List all distinct tags assigned to any movie"""
        rows = database.execute(
            select(TableMovies.tags).where(TableMovies.tags.is_not(None))).all()
        tags = set()
        for row in rows:
            if row.tags:
                tags.update(ast.literal_eval(row.tags))
        return marshal([{'tag': tag} for tag in sorted(tags)], self.get_response_model, envelope='data')
