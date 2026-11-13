# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from functools import reduce

from app.database import get_exclusion_clause, TableSportsEvents, TableSportsLeagues, database, select, update, func
from subtitles.indexer.sports import list_missing_subtitles_sports, sports_scan_subtitles
from subtitles.mass_download import league_download_subtitles
from subtitles.wanted import wanted_search_missing_subtitles_sports
from sportarr.sync.leagues import update_one_league
from sportarr.sync.events import sync_events
from app.event_handler import event_stream
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, None_Keys, postprocess, add_list_query_args, profile_filter_clause, \
    monitored_filter_clause, tags_filter_clause, audio_language_filter_clause, apply_sort

api_ns_sports_leagues = Namespace('Sports Leagues', description='List sports leagues metadata, update languages '
                                                                'profile or run actions on specific leagues.')


@api_ns_sports_leagues.route('sports/leagues')
class SportsLeagues(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('leagueid[]', type=int, action='append', required=False, default=[],
                                    help='Sportarr league IDs to get')
    add_list_query_args(get_request_parser)

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
        'created_at_timestamp': fields.String(),
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

        file_count = select(TableSportsEvents.sportarrLeagueId,
                            func.count().label('episodeFileCount')) \
            .group_by(TableSportsEvents.sportarrLeagueId).subquery()

        missing_conditions = [TableSportsEvents.missing_subtitles.is_not(None),
                              TableSportsEvents.missing_subtitles != '[]']
        missing_conditions += get_exclusion_clause('sports')
        missing_count = select(TableSportsEvents.sportarrLeagueId,
                               func.count().label('episodeMissingCount')) \
            .select_from(TableSportsEvents) \
            .join(TableSportsLeagues) \
            .where(reduce(operator.and_, missing_conditions)) \
            .group_by(TableSportsEvents.sportarrLeagueId).subquery()

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
                      TableSportsLeagues.audio_language,
                      TableSportsLeagues.created_at_timestamp,
                      func.coalesce(file_count.c.episodeFileCount, 0).label('episodeFileCount'),
                      func.coalesce(missing_count.c.episodeMissingCount, 0).label('episodeMissingCount')) \
            .select_from(TableSportsLeagues) \
            .join(file_count, TableSportsLeagues.sportarrLeagueId == file_count.c.sportarrLeagueId, isouter=True) \
            .join(missing_count, TableSportsLeagues.sportarrLeagueId == missing_count.c.sportarrLeagueId, isouter=True)

        where_clauses = []
        if leagueId:
            where_clauses.append(TableSportsLeagues.sportarrLeagueId.in_(leagueId))
        if args.get('monitored') is not None:
            where_clauses.append(monitored_filter_clause(TableSportsLeagues.monitored, args['monitored']))
        if args.get('profileid') is not None:
            where_clauses.append(profile_filter_clause(TableSportsLeagues.profileId, args['profileid']))
        if args.get('missing') is not None:
            missing_clause = func.coalesce(missing_count.c.episodeMissingCount, 0) > 0
            if args['missing'] == 'false':
                missing_clause = func.coalesce(missing_count.c.episodeMissingCount, 0) == 0
            where_clauses.append(missing_clause)
        if args.get('audio_language') is not None:
            where_clauses.append(audio_language_filter_clause(TableSportsLeagues.audio_language,
                                                               args['audio_language']))
        if args.get('tags[]'):
            where_clauses.append(tags_filter_clause(TableSportsLeagues.tags, args['tags[]']))
        if where_clauses:
            stmt = stmt.where(reduce(operator.and_, where_clauses))

        stmt = apply_sort(stmt, {
            'title': TableSportsLeagues.sortTitle,
            'sport': TableSportsLeagues.sport,
            'episodeFileCount': file_count.c.episodeFileCount,
            'episodeMissingCount': missing_count.c.episodeMissingCount,
            'profileId': TableSportsLeagues.profileId,
            'createdAtTimestamp': TableSportsLeagues.created_at_timestamp,
        }, TableSportsLeagues.sortTitle, args.get('sort_by'), args.get('sort_order'))

        if length > 0:
            stmt = stmt.limit(length).offset(start)

        results = [postprocess({
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
                'created_at_timestamp': x.created_at_timestamp,
                'alternativeTitles': [],
                'episodeFileCount': x.episodeFileCount,
                'episodeMissingCount': x.episodeMissingCount,
            }) for x in database.execute(stmt).all()]

        count_stmt = select(func.count()).select_from(TableSportsLeagues) \
            .join(missing_count, TableSportsLeagues.sportarrLeagueId == missing_count.c.sportarrLeagueId, isouter=True)
        if where_clauses:
            count_stmt = count_stmt.where(reduce(operator.and_, where_clauses))
        count = database.execute(count_stmt).scalar()

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
            sync_events(league_id=leagueid)
            return '', 204

        return 'Unknown action', 400
