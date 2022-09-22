# coding=utf-8

import apprise

from flask_restx import Resource, Namespace, reqparse

from ..utils import authenticate

api_ns_system_notifications = Namespace('System Notifications', description='Send test notifications provider message')


@api_ns_system_notifications.hide
@api_ns_system_notifications.route('system/notifications')
class Notifications(Resource):
    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('url', type=str, required=True, help='Notifications provider URL')

    @authenticate
    @api_ns_system_notifications.doc(parser=patch_request_parser)
    @api_ns_system_notifications.response(204, 'Success')
    @api_ns_system_notifications.response(401, 'Not Authenticated')
    def patch(self):
        """Test a notifications provider URL"""
        args = self.patch_request_parser.parse_args()
        url = args.get("url")

        asset = apprise.AppriseAsset(async_mode=False)

        apobj = apprise.Apprise(asset=asset)

        apobj.add(url)

        apobj.notify(
            title='Bazarr test notification',
            body='Test notification'
        )

        return '', 204
