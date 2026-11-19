# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from functools import reduce

from app.database import get_exclusion_clause, TableSportsEvents, TableSportsLeagues, TableMissingSubtitles, database, \
    select, func
from api.swaggerui import subtitles_language_model
from subtitles.wanted_state import get_missing_languages_map

from ..utils import authenticate, postprocess

api_ns_sports_wanted = Namespace('Sports Wanted', description='List sports events wanted subtitles')


@api_ns_sports_wanted.route('sports/wanted')
class SportsWanted(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('eventid[]', type=int, action='append', required=False, default=[],
                                    help='Sports events ID to list')

    get_subtitles_language_model = api_ns_sports_wanted.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_sports_wanted.model('wanted_sports_data_model', {
        'leagueTitle': fields.String(),
        'eventTitle': fields.String(),
        'partName': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'sportarrLeagueId': fields.Integer(),
        'sportsEventId': fields.Integer(),
        'sceneName': fields.String(),
        'tags': fields.List(fields.String),
        'sport': fields.String(),
    })

    get_response_model = api_ns_sports_wanted.model('SportsWantedGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_sports_wanted.response(401, 'Not Authenticated')
    @api_ns_sports_wanted.doc(parser=get_request_parser)
    def get(self):
        """List sports events wanted subtitles"""
        args = self.get_request_parser.parse_args()
        eventid = args.get('eventid[]')

        wanted_conditions = [select(TableMissingSubtitles.id)
                             .where(TableMissingSubtitles.media_type == 'sports')
                             .where(TableMissingSubtitles.media_id == TableSportsEvents.id)
                             .exists()]
        if len(eventid) > 0:
            wanted_conditions.append((TableSportsEvents.id.in_(eventid)))
            start = 0
            length = 0
        else:
            start = args.get('start')
            length = args.get('length')

        wanted_conditions += get_exclusion_clause('sports')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        stmt = select(TableSportsLeagues.title.label('leagueTitle'),
                      TableSportsEvents.title.label('eventTitle'),
                      TableSportsEvents.partName,
                      TableSportsEvents.sportarrLeagueId,
                      TableSportsEvents.id.label('sportsEventId'),
                      TableSportsEvents.sceneName,
                      TableSportsLeagues.tags,
                      TableSportsLeagues.sport) \
            .select_from(TableSportsEvents) \
            .join(TableSportsLeagues) \
            .where(wanted_condition)

        if length > 0:
            stmt = stmt.order_by(TableSportsEvents.id.desc()).limit(length).offset(start)

        events = database.execute(stmt).all()
        missing_languages = get_missing_languages_map('sports', [x.sportsEventId for x in events])

        results = [postprocess({
            'leagueTitle': x.leagueTitle,
            'eventTitle': x.eventTitle,
            'partName': x.partName,
            'missing_subtitles': missing_languages[x.sportsEventId],
            'sportarrLeagueId': x.sportarrLeagueId,
            'sportsEventId': x.sportsEventId,
            'sceneName': x.sceneName,
            'tags': x.tags,
            'sport': x.sport,
        }) for x in events]

        count = database.execute(
            select(func.count())
            .select_from(TableSportsEvents)
            .join(TableSportsLeagues)
            .where(wanted_condition)) \
            .scalar()

        return marshal({'data': results, 'total': count}, self.get_response_model)
