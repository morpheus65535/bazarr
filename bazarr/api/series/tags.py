# coding=utf-8

import ast

from flask_restx import Resource, Namespace, fields, marshal

from app.database import TableShows, database, select

from ..utils import authenticate

api_ns_series_tags = Namespace('Series Tags', description='List tags assigned to series')


@api_ns_series_tags.route('series/tags')
class SeriesTags(Resource):
    get_response_model = api_ns_series_tags.model('SeriesTagsGetResponse', {
        'tag': fields.String(),
    })

    @authenticate
    @api_ns_series_tags.response(200, 'Success')
    @api_ns_series_tags.response(401, 'Not Authenticated')
    def get(self):
        """List all distinct tags assigned to any series"""
        rows = database.execute(
            select(TableShows.tags).where(TableShows.tags.is_not(None))).all()
        tags = set()
        for row in rows:
            if row.tags:
                tags.update(ast.literal_eval(row.tags))
        return marshal([{'tag': tag} for tag in sorted(tags)], self.get_response_model, envelope='data')
