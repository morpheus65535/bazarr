# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableEpisodes, database, select
from api.swaggerui import subtitles_model, subtitles_language_model, audio_language_model

from ..utils import authenticate, postprocess

api_ns_episodes = Namespace('Episodes', description='List episodes metadata for specific series or episodes.')


@api_ns_episodes.route('episodes')
class Episodes(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('seriesid[]', type=int, action='append', required=False, default=[],
                                    help='Series IDs to list episodes for')
    get_request_parser.add_argument('episodeid[]', type=int, action='append', required=False, default=[],
                                    help='Episodes ID to list')

    get_subtitles_model = api_ns_episodes.model('subtitles_model', subtitles_model)
    get_subtitles_language_model = api_ns_episodes.model('subtitles_language_model', subtitles_language_model)
    get_audio_language_model = api_ns_episodes.model('audio_language_model', audio_language_model)

    get_response_model = api_ns_episodes.model('EpisodeGetResponse', {
        'audio_language': fields.Nested(get_audio_language_model),
        'episode': fields.Integer(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'monitored': fields.Boolean(),
        'path': fields.String(),
        'season': fields.Integer(),
        'sonarrEpisodeId': fields.Integer(),
        'sonarrSeriesId': fields.Integer(),
        'subtitles': fields.Nested(get_subtitles_model),
        'title': fields.String(),
        'sceneName': fields.String(),
    })

    @authenticate
    @api_ns_episodes.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_episodes.doc(parser=get_request_parser)
    @api_ns_episodes.response(200, 'Success')
    @api_ns_episodes.response(401, 'Not Authenticated')
    @api_ns_episodes.response(404, 'Series or Episode ID not provided')
    def get(self):
        """List episodes metadata for specific series or episodes"""
        args = self.get_request_parser.parse_args()
        seriesId = args.get('seriesid[]')
        episodeId = args.get('episodeid[]')

        stmt = select(
                TableEpisodes.audio_language,
                TableEpisodes.episode,
                TableEpisodes.missing_subtitles,
                TableEpisodes.monitored,
                TableEpisodes.path,
                TableEpisodes.season,
                TableEpisodes.sonarrEpisodeId,
                TableEpisodes.sonarrSeriesId,
                TableEpisodes.subtitles,
                TableEpisodes.title,
                TableEpisodes.sceneName,
            )

        if len(episodeId) > 0:
            stmt_query = database.execute(
                stmt
                .where(TableEpisodes.sonarrEpisodeId.in_(episodeId)))\
                .all()
        elif len(seriesId) > 0:
            stmt_query = database.execute(
                stmt
                .where(TableEpisodes.sonarrSeriesId.in_(seriesId))
                .order_by(TableEpisodes.season.desc(), TableEpisodes.episode.desc()))\
                .all()
        else:
            return "Series or Episode ID not provided", 404

        return [postprocess({
                'audio_language': x.audio_language,
                'episode': x.episode,
                'missing_subtitles': x.missing_subtitles,
                'monitored': x.monitored,
                'path': x.path,
                'season': x.season,
                'sonarrEpisodeId': x.sonarrEpisodeId,
                'sonarrSeriesId': x.sonarrSeriesId,
                'subtitles': x.subtitles,
                'title': x.title,
                'sceneName': x.sceneName,
                }) for x in stmt_query]
