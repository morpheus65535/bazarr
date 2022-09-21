# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableEpisodes
from api.swaggerui import subtitles_model, subtitles_language_model, audio_language_model

from ..utils import authenticate, postprocessEpisode

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
        'rowid': fields.Integer(),
        'audio_codec': fields.String(),
        'audio_language': fields.Nested(get_audio_language_model),
        'episode': fields.Integer(),
        'episode_file_id': fields.Integer(),
        'failedAttempts': fields.String(),
        'file_size': fields.Integer(),
        'format': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'monitored': fields.Boolean(),
        'path': fields.String(),
        'resolution': fields.String(),
        'season': fields.Integer(),
        'sonarrEpisodeId': fields.Integer(),
        'sonarrSeriesId': fields.Integer(),
        'subtitles': fields.Nested(get_subtitles_model),
        'title': fields.String(),
        'video_codec': fields.String(),
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

        if len(episodeId) > 0:
            result = TableEpisodes.select().where(TableEpisodes.sonarrEpisodeId.in_(episodeId)).dicts()
        elif len(seriesId) > 0:
            result = TableEpisodes.select()\
                .where(TableEpisodes.sonarrSeriesId.in_(seriesId))\
                .order_by(TableEpisodes.season.desc(), TableEpisodes.episode.desc())\
                .dicts()
        else:
            return "Series or Episode ID not provided", 404

        result = list(result)
        for item in result:
            postprocessEpisode(item)

        return result
