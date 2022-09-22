# coding=utf-8

import gc

from flask import session
from flask_restx import Resource, Namespace, reqparse

from app.config import settings
from utilities.helper import check_credentials

api_ns_system_account = Namespace('System Account', description='Login or logout from Bazarr UI')


@api_ns_system_account.hide
@api_ns_system_account.route('system/account')
class SystemAccount(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('action', type=str, required=True, help='Action from ["login", "logout"]')
    post_request_parser.add_argument('username', type=str, required=False, help='Bazarr username')
    post_request_parser.add_argument('password', type=str, required=False, help='Bazarr password')

    @api_ns_system_account.doc(parser=post_request_parser)
    @api_ns_system_account.response(204, 'Success')
    @api_ns_system_account.response(400, 'Unknown action')
    @api_ns_system_account.response(404, 'Unknown authentication type define in config.ini')
    def post(self):
        """Login or logout from Bazarr UI when using form login"""
        args = self.patch_request_parser.parse_args()
        if settings.auth.type != 'form':
            return 'Unknown authentication type define in config.ini', 404

        action = args.get('action')
        if action == 'login':
            username = args.get('username')
            password = args.get('password')
            if check_credentials(username, password):
                session['logged_in'] = True
                return '', 204
        elif action == 'logout':
            session.clear()
            gc.collect()
            return '', 204

        return 'Unknown action', 400
