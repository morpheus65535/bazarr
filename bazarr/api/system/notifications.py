# coding=utf-8

import apprise

from flask import request
from flask_restful import Resource

from ..utils import authenticate


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
