# coding=utf-8

import apprise

from flask import request
from flask_restx import Resource, Namespace

from ..utils import authenticate

api_ns_system_notifications = Namespace('systemNotifications', description='System notifications API endpoint')


@api_ns_system_notifications.route('system/notifications')
class Notifications(Resource):
    @authenticate
    def patch(self):
        url = request.form.get("url")

        asset = apprise.AppriseAsset(async_mode=False)

        apobj = apprise.Apprise(asset=asset)

        apobj.add(url)

        apobj.notify(
            title='Bazarr test notification',
            body='Test notification'
        )

        return '', 204
