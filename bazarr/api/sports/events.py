# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.database import TableSportsEvents, database, select
from api.swaggerui import subtitles_model, subtitles_language_model, audio_language_model

from ..utils import authenticate, postprocess

api_ns_sports_events = Namespace('Sports Events', description='List sports events metadata for specific leagues or '
                                                              'events.')


@api_ns_sports_events.route('sports/events')
class SportsEvents(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('leagueid[]', type=int, action='append', required=False, default=[],
                                    help='League IDs to list events for')
    get_request_parser.add_argument('eventid[]', type=int, action='append', required=False, default=[],
                                    help='Sports events ID to list')

    get_subtitles_model = api_ns_sports_events.model('subtitles_model', subtitles_model)
    get_subtitles_language_model = api_ns_sports_events.model('subtitles_language_model', subtitles_language_model)
    get_audio_language_model = api_ns_sports_events.model('audio_language_model', audio_language_model)

    get_response_model = api_ns_sports_events.model('SportsEventGetResponse', {
        'audio_language': fields.Nested(get_audio_language_model),
        'episode': fields.Integer(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'monitored': fields.Boolean(),
        'path': fields.String(),
        'season': fields.Integer(),
        'sportsEventId': fields.Integer(),
        'sportarrLeagueId': fields.Integer(),
        'subtitles': fields.Nested(get_subtitles_model),
        'title': fields.String(),
        'partName': fields.String(),
        'partNumber': fields.Integer(),
        'sceneName': fields.String(),
        'broadcastDate': fields.String(),
    })

    @authenticate
    @api_ns_sports_events.doc(parser=get_request_parser)
    @api_ns_sports_events.response(200, 'Success')
    @api_ns_sports_events.response(401, 'Not Authenticated')
    @api_ns_sports_events.response(404, 'League or Sports event ID not provided')
    def get(self):
        """List sports events metadata for specific leagues or events"""
        args = self.get_request_parser.parse_args()
        leagueId = args.get('leagueid[]')
        eventId = args.get('eventid[]')

        stmt = select(
                TableSportsEvents.audio_language,
                TableSportsEvents.episode,
                TableSportsEvents.missing_subtitles,
                TableSportsEvents.monitored,
                TableSportsEvents.path,
                TableSportsEvents.season,
                TableSportsEvents.id,
                TableSportsEvents.sportarrLeagueId,
                TableSportsEvents.title,
                TableSportsEvents.partName,
                TableSportsEvents.partNumber,
                TableSportsEvents.sceneName,
                TableSportsEvents.broadcastDate,
            )

        if len(eventId) > 0:
            stmt_query = database.execute(
                stmt
                .where(TableSportsEvents.id.in_(eventId)))\
                .all()
        elif len(leagueId) > 0:
            # An event can hold more than one file, so order by the part as well
            # to keep the prelims above the main card.
            stmt_query = database.execute(
                stmt
                .where(TableSportsEvents.sportarrLeagueId.in_(leagueId))
                .order_by(TableSportsEvents.season.desc(), TableSportsEvents.episode.desc(),
                          TableSportsEvents.partNumber.asc()))\
                .all()
        else:
            return "League or Sports event ID not provided", 404

        return marshal([postprocess({
                'audio_language': x.audio_language,
                'episode': x.episode,
                'missing_subtitles': x.missing_subtitles,
                'monitored': x.monitored,
                'path': x.path,
                'season': x.season,
                'sportsEventId': x.id,
                'sportarrLeagueId': x.sportarrLeagueId,
                'title': x.title,
                'partName': x.partName,
                'partNumber': x.partNumber,
                'sceneName': x.sceneName,
                'broadcastDate': x.broadcastDate,
                }) for x in stmt_query], self.get_response_model, envelope='data')
