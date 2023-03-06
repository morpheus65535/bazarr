# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields
from subliminal_patch.core import guessit

from ..utils import authenticate


api_ns_subtitles_info = Namespace('Subtitles Info', description='Guess season number, episode number or language from '
                                                                'uploaded subtitles filename')


@api_ns_subtitles_info.route('subtitles/info')
class SubtitleNameInfo(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('filenames[]', type=str, required=True, action='append',
                                    help='Subtitles filenames')

    get_response_model = api_ns_subtitles_info.model('SubtitlesInfoGetResponse', {
        'filename': fields.String(),
        'subtitle_language': fields.String(),
        'season': fields.Integer(),
        'episode': fields.Integer(),
    })

    @authenticate
    @api_ns_subtitles_info.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_subtitles_info.response(200, 'Success')
    @api_ns_subtitles_info.response(401, 'Not Authenticated')
    @api_ns_subtitles_info.doc(parser=get_request_parser)
    def get(self):
        """Guessit over subtitles filename"""
        args = self.get_request_parser.parse_args()
        names = args.get('filenames[]')
        results = []
        opts = dict(type='episode')
        for name in names:
            guessit_result = guessit(name, options=opts)
            result = {}
            result['filename'] = name
            result['subtitle_language'] = str(guessit_result.get('subtitle_language', ''))

            episode = guessit_result.get('episode')
            result['episode'] = (episode[0] if isinstance(episode, list) and episode else episode) or 0

            result['season'] = guessit_result.get('season', 0)
            results.append(result)

        return results
