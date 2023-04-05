# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields
from operator import itemgetter

from app.database import TableHistory, TableHistoryMovie, database
from app.get_providers import list_throttled_providers, reset_throttled_providers

from ..utils import authenticate, False_Keys

api_ns_providers = Namespace('Providers', description='Get and reset providers status')


@api_ns_providers.route('providers')
class Providers(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('history', type=str, required=False, help='Provider name for history stats')

    get_response_model = api_ns_providers.model('MovieBlacklistGetResponse', {
        'name': fields.String(),
        'status': fields.String(),
        'retry': fields.String(),
    })

    @authenticate
    @api_ns_providers.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_providers.response(200, 'Success')
    @api_ns_providers.response(401, 'Not Authenticated')
    @api_ns_providers.doc(parser=get_request_parser)
    def get(self):
        """Get providers status"""
        args = self.get_request_parser.parse_args()
        history = args.get('history')
        if history and history not in False_Keys:
            providers = list(database.query(TableHistory.provider)
                             .where(TableHistory.provider and
                                    TableHistory.provider != "manual")
                             .distinct())
            providers += list(database.query(TableHistoryMovie.provider)
                              .where(TableHistoryMovie.provider and
                                     TableHistoryMovie.provider != "manual")
                              .distinct())
            providers_list = [x.provider for x in providers]
            providers_dicts = []
            for provider in providers_list:
                if provider not in [x['name'] for x in providers_dicts]:
                    providers_dicts.append({
                        'name': provider,
                        'status': 'History',
                        'retry': '-'
                    })
        else:
            throttled_providers = list_throttled_providers()

            providers_dicts = list()
            for provider in throttled_providers:
                providers_dicts.append({
                    "name": provider[0],
                    "status": provider[1] if provider[1] is not None else "Good",
                    "retry": provider[2] if provider[2] != "now" else "-"
                })
        return sorted(providers_dicts, key=itemgetter('name'))

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('action', type=str, required=True, help='Action to perform from ["reset"]')

    @authenticate
    @api_ns_providers.doc(parser=post_request_parser)
    @api_ns_providers.response(204, 'Success')
    @api_ns_providers.response(401, 'Not Authenticated')
    @api_ns_providers.response(400, 'Unknown action')
    def post(self):
        """Reset providers status"""
        args = self.post_request_parser.parse_args()
        action = args.get('action')

        if action == 'reset':
            reset_throttled_providers()
            return '', 204

        return 'Unknown action', 400
