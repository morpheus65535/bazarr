# coding=utf-8

from flask_restx import Resource, Namespace, reqparse

from app.announcements import get_all_announcements, mark_announcement_as_dismissed

from ..utils import authenticate

api_ns_system_announcements = Namespace('System Announcements', description='List announcements relative to Bazarr')


@api_ns_system_announcements.route('system/announcements')
class SystemAnnouncements(Resource):
    @authenticate
    @api_ns_system_announcements.doc(parser=None)
    @api_ns_system_announcements.response(200, 'Success')
    @api_ns_system_announcements.response(401, 'Not Authenticated')
    def get(self):
        """List announcements relative to Bazarr"""
        return {'data': get_all_announcements()}

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('hash', type=str, required=True, help='hash of the announcement to dismiss')

    @authenticate
    @api_ns_system_announcements.doc(parser=post_request_parser)
    @api_ns_system_announcements.response(204, 'Success')
    @api_ns_system_announcements.response(401, 'Not Authenticated')
    def post(self):
        """Mark announcement as dismissed"""
        args = self.post_request_parser.parse_args()
        hashed_announcement = args.get('hash')

        mark_announcement_as_dismissed(hashed_announcement=hashed_announcement)
        return '', 204
