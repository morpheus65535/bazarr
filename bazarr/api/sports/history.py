# coding=utf-8

import operator
import ast
from functools import reduce

from api.swaggerui import subtitles_language_model
from app.database import (TableSportsEvents, TableSportsLeagues, TableHistorySports, TableBlacklistSports, database,
                          select, func)

import pretty
from flask_restx import Resource, Namespace, reqparse, fields, marshal
from ..utils import authenticate, postprocess

api_ns_sports_history = Namespace('Sports History', description='List sports events history events')


@api_ns_sports_history.route('sports/history')
class SportsHistory(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('eventid', type=int, required=False, help='Sports event ID')

    get_language_model = api_ns_sports_history.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_sports_history.model('history_sports_data_model', {
        'leagueTitle': fields.String(),
        'monitored': fields.Boolean(),
        'eventTitle': fields.String(),
        'partName': fields.String(),
        'timestamp': fields.String(),
        'subs_id': fields.String(),
        'description': fields.String(),
        'sportarrLeagueId': fields.Integer(),
        'language': fields.Nested(get_language_model),
        'score': fields.String(),
        'tags': fields.List(fields.String),
        'action': fields.Integer(),
        'subtitles_path': fields.String(),
        'sportsEventId': fields.Integer(),
        'provider': fields.String(),
        'parsed_timestamp': fields.String(),
        'blacklisted': fields.Boolean(),
        'matches': fields.List(fields.String),
        'dont_matches': fields.List(fields.String),
    })

    get_response_model = api_ns_sports_history.model('SportsHistoryGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_sports_history.response(401, 'Not Authenticated')
    @api_ns_sports_history.doc(parser=get_request_parser)
    def get(self):
        """List sports events history events"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        eventid = args.get('eventid')

        blacklisted_subtitles = select(TableBlacklistSports.provider,
                                       TableBlacklistSports.subs_id) \
            .subquery()

        query_conditions = [(TableSportsEvents.title.is_not(None))]
        if eventid:
            query_conditions.append((TableSportsEvents.id == eventid))

        stmt = select(TableHistorySports.id,
                      TableSportsLeagues.title.label('leagueTitle'),
                      TableSportsEvents.monitored,
                      TableSportsEvents.title.label('eventTitle'),
                      TableSportsEvents.partName,
                      TableHistorySports.timestamp,
                      TableHistorySports.subs_id,
                      TableHistorySports.description,
                      TableHistorySports.sportarrLeagueId,
                      TableSportsEvents.path,
                      TableHistorySports.language,
                      TableHistorySports.score,
                      TableHistorySports.score_out_of,
                      TableSportsLeagues.tags,
                      TableHistorySports.action,
                      TableHistorySports.video_path,
                      TableHistorySports.subtitles_path,
                      TableHistorySports.sportsEventId,
                      TableHistorySports.provider,
                      TableSportsLeagues.sport,
                      TableHistorySports.matched,
                      TableHistorySports.not_matched,
                      blacklisted_subtitles.c.subs_id.label('blacklisted')) \
            .select_from(TableHistorySports) \
            .join(TableSportsLeagues,
                  onclause=TableHistorySports.sportarrLeagueId == TableSportsLeagues.sportarrLeagueId) \
            .join(TableSportsEvents, onclause=TableHistorySports.sportsEventId == TableSportsEvents.id) \
            .join(blacklisted_subtitles, onclause=TableHistorySports.subs_id == blacklisted_subtitles.c.subs_id,
                  isouter=True) \
            .where(reduce(operator.and_, query_conditions)) \
            .order_by(TableHistorySports.timestamp.desc())
        if length > 0:
            stmt = stmt.limit(length).offset(start)
        sports_history = [{
            'id': x.id,
            'leagueTitle': x.leagueTitle,
            'monitored': x.monitored,
            'eventTitle': x.eventTitle,
            'partName': x.partName,
            'timestamp': x.timestamp,
            'subs_id': x.subs_id,
            'description': x.description,
            'sportarrLeagueId': x.sportarrLeagueId,
            'path': x.path,
            'language': x.language,
            'score': x.score,
            'score_out_of': x.score_out_of,
            'tags': x.tags,
            'action': x.action,
            'video_path': x.video_path,
            'subtitles_path': x.subtitles_path,
            'sportsEventId': x.sportsEventId,
            'provider': x.provider,
            'matches': x.matched,
            'dont_matches': x.not_matched,
            'blacklisted': bool(x.blacklisted),
        } for x in database.execute(stmt).all()]

        for item in sports_history:
            item.update(postprocess(item))

            del item['path']
            del item['video_path']

            if item['score']:
                item['score'] = f"{round((int(item['score']) * 100 / item['score_out_of']), 2)}%"

            # Make timestamp pretty
            if item['timestamp']:
                item["parsed_timestamp"] = item['timestamp'].strftime('%x %X')
                item['timestamp'] = pretty.date(item["timestamp"])

            # Parse matches and dont_matches
            if item['matches']:
                item.update({'matches': ast.literal_eval(item['matches'])})
            else:
                item.update({'matches': []})

            if item['dont_matches']:
                item.update({'dont_matches': ast.literal_eval(item['dont_matches'])})
            else:
                item.update({'dont_matches': []})

        count = database.execute(
            select(func.count())
            .select_from(TableHistorySports)
            .join(TableSportsEvents, onclause=TableHistorySports.sportsEventId == TableSportsEvents.id)
            .where(TableSportsEvents.title.is_not(None))) \
            .scalar()

        return marshal({'data': sports_history, 'total': count}, self.get_response_model)
