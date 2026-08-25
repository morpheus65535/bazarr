# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from functools import reduce

from app.database import get_exclusion_clause, TableSportsEvents, TableSportsLeagues, database, select, update, func
from subtitles.indexer.sports import list_missing_subtitles_sports, sports_scan_subtitles
from subtitles.mass_download import league_download_subtitles
from subtitles.wanted import wanted_search_missing_subtitles_sports
from sportarr.sync.leagues import update_one_league
from app.event_handler import event_stream
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, None_Keys, postprocess

api_ns_sports_leagues = Namespace('Sports Leagues', description='List sports leagues metadata, update languages '
                                                                'profile or run actions on specific leagues.')


@api_ns_sports_leagues.route('sports/leagues')
class SportsLeagues(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('leagueid[]', type=int, action='append', required=False, default=[],
                                    help='Sportarr league IDs to get')

    get_subtitles_language_model = api_ns_sports_leagues.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_sports_leagues.model('sports_leagues_data_model', {
        'sportarrLeagueId': fields.Integer(),
        'externalId': fields.String(),
        'title': fields.String(),
        'sortTitle': fields.String(),
        'sport': fields.String(),
        'path': fields.String(),
        'poster': fields.String(),
        'fanart': fields.String(),
        'overview': fields.String(),
        'monitored': fields.Boolean(),
        'profileId': fields.Integer(),
        'tags': fields.List(fields.String),
        'audio_language': fields.Nested(get_subtitles_language_model),
        'alternativeTitles': fields.List(fields.String),
        'episodeFileCount': fields.Integer(),
        'episodeMissingCount': fields.Integer(),
    })

    get_response_model = api_ns_sports_leagues.model('SportsLeaguesGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_sports_leagues.response(401, 'Not Authenticated')
    @api_ns_sports_leagues.doc(parser=get_request_parser)
    def get(self):
        """List sports leagues metadata"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        leagueId = args.get('leagueid[]')

        stmt = select(TableSportsLeagues.sportarrLeagueId,
                      TableSportsLeagues.externalId,
                      TableSportsLeagues.title,
                      TableSportsLeagues.sortTitle,
                      TableSportsLeagues.sport,
                      TableSportsLeagues.path,
                      TableSportsLeagues.poster,
                      TableSportsLeagues.fanart,
                      TableSportsLeagues.overview,
                      TableSportsLeagues.monitored,
                      TableSportsLeagues.profileId,
                      TableSportsLeagues.tags,
                      TableSportsLeagues.audio_language) \
            .order_by(TableSportsLeagues.sortTitle)

        if len(leagueId) > 0:
            stmt = stmt.where(TableSportsLeagues.sportarrLeagueId.in_(leagueId))
        elif length > 0:
            stmt = stmt.limit(length).offset(start)

        results = []
        for x in database.execute(stmt).all():
            # Counted per playable file, because a row is one part. An event with
            # two parts needs subtitles for both.
            file_count = database.execute(
                select(func.count())
                .select_from(TableSportsEvents)
                .where(TableSportsEvents.sportarrLeagueId == x.sportarrLeagueId)) \
                .scalar()

            missing_conditions = [(TableSportsEvents.sportarrLeagueId == x.sportarrLeagueId),
                                  (TableSportsEvents.missing_subtitles.is_not(None)),
                                  (TableSportsEvents.missing_subtitles != '[]')]
            missing_conditions += get_exclusion_clause('sports')
            missing_count = database.execute(
                select(func.count())
                .select_from(TableSportsEvents)
                .join(TableSportsLeagues)
                .where(reduce(operator.and_, missing_conditions))) \
                .scalar()

            results.append(postprocess({
                'sportarrLeagueId': x.sportarrLeagueId,
                'externalId': x.externalId,
                'title': x.title,
                'sortTitle': x.sortTitle,
                'sport': x.sport,
                'path': x.path,
                'poster': x.poster,
                'fanart': x.fanart,
                'overview': x.overview,
                'monitored': x.monitored,
                'profileId': x.profileId,
                'tags': x.tags,
                'audio_language': x.audio_language,
                # Sportarr keeps no alternative titles for a league. The empty
                # list keeps the shape the same as a series or a movie.
                'alternativeTitles': [],
                'episodeFileCount': file_count,
                'episodeMissingCount': missing_count,
            }))

        count = database.execute(
            select(func.count())
            .select_from(TableSportsLeagues)) \
            .scalar()

        return marshal({'data': results, 'total': count}, self.get_response_model)

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('leagueid', type=int, action='append', required=False, default=[],
                                     help='Sportarr league ID')
    post_request_parser.add_argument('profileid', type=str, action='append', required=False, default=[],
                                     help='Languages profile(s) ID or "none"')

    @authenticate
    @api_ns_sports_leagues.doc(parser=post_request_parser)
    @api_ns_sports_leagues.response(204, 'Success')
    @api_ns_sports_leagues.response(401, 'Not Authenticated')
    @api_ns_sports_leagues.response(404, 'Languages profile not found')
    def post(self):
        """Update specific sports leagues languages profile"""
        args = self.post_request_parser.parse_args()
        leagueIdList = args.get('leagueid')
        profileIdList = args.get('profileid')

        for idx in range(len(leagueIdList)):
            leagueId = leagueIdList[idx]
            profileId = profileIdList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return 'Languages profile not found', 404

            database.execute(
                update(TableSportsLeagues)
                .values(profileId=profileId)
                .where(TableSportsLeagues.sportarrLeagueId == leagueId))

            list_missing_subtitles_sports(no=leagueId)

            event_stream(type='sports-league', payload=leagueId)

            event_id_list = database.execute(
                select(TableSportsEvents.id)
                .where(TableSportsEvents.sportarrLeagueId == leagueId))\
                .all()

            for item in event_id_list:
                event_stream(type='sports-event-wanted', payload=item.id)

        event_stream(type='badges')

        return '', 204

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('leagueid', type=int, required=False, help='Sportarr league ID')
    patch_request_parser.add_argument('action', type=str, required=False,
                                      help='Action to perform from ["scan-disk", "search-missing", "search-wanted", '
                                           '"sync"]')

    @authenticate
    @api_ns_sports_leagues.doc(parser=patch_request_parser)
    @api_ns_sports_leagues.response(204, 'Success')
    @api_ns_sports_leagues.response(400, 'Unknown action')
    @api_ns_sports_leagues.response(401, 'Not Authenticated')
    @api_ns_sports_leagues.response(500, 'League directory not found. Path mapping issue?')
    def patch(self):
        """Run actions on specific sports leagues"""
        args = self.patch_request_parser.parse_args()
        leagueid = args.get('leagueid')
        action = args.get('action')
        if action == "scan-disk":
            sports_scan_subtitles(leagueid)
            return '', 204
        elif action == "search-missing":
            try:
                league_download_subtitles(leagueid)
            except OSError:
                return 'League directory not found. Path mapping issue?', 500
            else:
                return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_sports()
            return '', 204
        elif action == "sync":
            update_one_league(leagueid, 'updated')
            return '', 204

        return 'Unknown action', 400
