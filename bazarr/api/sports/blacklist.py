# coding=utf-8

import pretty

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.database import TableSportsEvents, TableSportsLeagues, TableBlacklistSports, database, select
from subtitles.tools.delete import delete_subtitles
from sportarr.blacklist import blacklist_log_sports, blacklist_delete_all_sports, blacklist_delete_sports
from utilities.path_mappings import path_mappings
from subtitles.mass_download import sports_event_download_subtitles
from app.event_handler import event_stream
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocess

api_ns_sports_blacklist = Namespace('Sports Blacklist', description='List, add or remove subtitles to or from '
                                                                    'sports events blacklist')


@api_ns_sports_blacklist.route('sports/blacklist')
class SportsBlacklist(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')

    get_language_model = api_ns_sports_blacklist.model('subtitles_language_model', subtitles_language_model)

    get_response_model = api_ns_sports_blacklist.model('SportsBlacklistGetResponse', {
        'leagueTitle': fields.String(),
        'eventTitle': fields.String(),
        'partName': fields.String(),
        'sportarrLeagueId': fields.Integer(),
        'sportsEventId': fields.Integer(),
        'provider': fields.String(),
        'subs_id': fields.String(),
        'language': fields.Nested(get_language_model),
        'timestamp': fields.String(),
        'parsed_timestamp': fields.String(),
    })

    @authenticate
    @api_ns_sports_blacklist.response(401, 'Not Authenticated')
    @api_ns_sports_blacklist.doc(parser=get_request_parser)
    def get(self):
        """List blacklisted sports events subtitles"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')

        stmt = select(TableSportsLeagues.title.label('leagueTitle'),
                      TableSportsEvents.title.label('eventTitle'),
                      TableSportsEvents.partName,
                      TableBlacklistSports.sportarr_league_id.label('sportarrLeagueId'),
                      TableBlacklistSports.sports_event_id.label('sportsEventId'),
                      TableBlacklistSports.provider,
                      TableBlacklistSports.subs_id,
                      TableBlacklistSports.language,
                      TableBlacklistSports.timestamp) \
            .select_from(TableBlacklistSports) \
            .join(TableSportsLeagues,
                  onclause=TableBlacklistSports.sportarr_league_id == TableSportsLeagues.sportarrLeagueId) \
            .join(TableSportsEvents, onclause=TableBlacklistSports.sports_event_id == TableSportsEvents.id) \
            .order_by(TableBlacklistSports.timestamp.desc())
        if length > 0:
            stmt = stmt.limit(length).offset(start)

        return marshal([postprocess({
            'leagueTitle': x.leagueTitle,
            'eventTitle': x.eventTitle,
            'partName': x.partName,
            'sportarrLeagueId': x.sportarrLeagueId,
            'sportsEventId': x.sportsEventId,
            'provider': x.provider,
            'subs_id': x.subs_id,
            'language': x.language,
            'timestamp': pretty.date(x.timestamp),
            'parsed_timestamp': x.timestamp.strftime('%x %X')
        }) for x in database.execute(stmt).all()], self.get_response_model, envelope='data')

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('leagueid', type=int, required=True, help='League ID')
    post_request_parser.add_argument('eventid', type=int, required=True, help='Sports event ID')
    post_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    post_request_parser.add_argument('subs_id', type=str, required=True, help='Subtitles ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Subtitles language')
    post_request_parser.add_argument('subtitles_path', type=str, required=True, help='Subtitles file path')

    @authenticate
    @api_ns_sports_blacklist.doc(parser=post_request_parser)
    @api_ns_sports_blacklist.response(200, 'Success')
    @api_ns_sports_blacklist.response(401, 'Not Authenticated')
    @api_ns_sports_blacklist.response(404, 'Sports event not found')
    @api_ns_sports_blacklist.response(500, 'Subtitles file not found or permission issue.')
    def post(self):
        """Add a sports events subtitles to blacklist"""
        args = self.post_request_parser.parse_args()
        sportarr_league_id = args.get('leagueid')
        sports_event_id = args.get('eventid')
        provider = args.get('provider')
        subs_id = args.get('subs_id')
        language = args.get('language')

        eventInfo = database.execute(
            select(TableSportsEvents.path)
            .where(TableSportsEvents.id == sports_event_id)) \
            .first()

        if not eventInfo:
            return 'Sports event not found', 404

        media_path = eventInfo.path
        subtitles_path = args.get('subtitles_path')

        blacklist_log_sports(sportarr_league_id=sportarr_league_id,
                             sports_event_id=sports_event_id,
                             provider=provider,
                             subs_id=subs_id,
                             language=language)
        if delete_subtitles(media_type='sports',
                            language=language,
                            forced=False,
                            hi=False,
                            media_path=path_mappings.path_replace_sports(media_path),
                            subtitles_path=subtitles_path,
                            sportarr_league_id=sportarr_league_id,
                            sports_event_id=sports_event_id):
            sports_event_download_subtitles(no=sports_event_id)
            event_stream(type='sports-event-history')
            return '', 200
        else:
            return 'Subtitles file not found or permission issue.', 500

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('all', type=str, required=False, help='Empty sports events subtitles blacklist')
    delete_request_parser.add_argument('provider', type=str, required=False, help='Provider name')
    delete_request_parser.add_argument('subs_id', type=str, required=False, help='Subtitles ID')

    @authenticate
    @api_ns_sports_blacklist.doc(parser=delete_request_parser)
    @api_ns_sports_blacklist.response(204, 'Success')
    @api_ns_sports_blacklist.response(401, 'Not Authenticated')
    def delete(self):
        """Delete a sports events subtitles from blacklist"""
        args = self.delete_request_parser.parse_args()
        if args.get("all") == "true":
            blacklist_delete_all_sports()
        else:
            provider = args.get('provider')
            subs_id = args.get('subs_id')
            blacklist_delete_sports(provider=provider, subs_id=subs_id)
        return '', 204
