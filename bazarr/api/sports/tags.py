# coding=utf-8

import ast

from flask_restx import Resource, Namespace, fields, marshal

from app.database import TableSportsLeagues, database, select

from ..utils import authenticate

api_ns_sports_tags = Namespace('Sports Tags', description='List tags assigned to sports leagues')


@api_ns_sports_tags.route('sports/leagues/tags')
class SportsLeaguesTags(Resource):
    get_response_model = api_ns_sports_tags.model('SportsLeaguesTagsGetResponse', {
        'tag': fields.String(),
    })

    @authenticate
    @api_ns_sports_tags.response(200, 'Success')
    @api_ns_sports_tags.response(401, 'Not Authenticated')
    def get(self):
        """List all distinct tags assigned to any sports league"""
        rows = database.execute(
            select(TableSportsLeagues.tags).where(TableSportsLeagues.tags.is_not(None))).all()
        tags = set()
        for row in rows:
            if row.tags:
                tags.update(ast.literal_eval(row.tags))
        return marshal([{'tag': tag} for tag in sorted(tags)], self.get_response_model, envelope='data')
