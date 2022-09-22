# coding=utf-8

from flask_restx import Resource, Namespace, reqparse

from ..utils import authenticate

api_ns_system = Namespace('System', description='Shutdown or restart Bazarr')


@api_ns_system.hide
@api_ns_system.route('system')
class System(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('action', type=str, required=True,
                                     help='Action to perform from ["shutdown", "restart"]')

    @authenticate
    @api_ns_system.doc(parser=post_request_parser)
    @api_ns_system.response(204, 'Success')
    @api_ns_system.response(401, 'Not Authenticated')
    def post(self):
        """Shutdown or restart Bazarr"""
        args = self.post_request_parser.parse_args()
        from app.server import webserver
        action = args.get('action')
        if action == "shutdown":
            webserver.shutdown()
        elif action == "restart":
            webserver.restart()
        return '', 204
