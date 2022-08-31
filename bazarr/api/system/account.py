# coding=utf-8

import gc

from flask import request, session
from flask_restx import Resource

from app.config import settings
from utilities.helper import check_credentials


class SystemAccount(Resource):
    def post(self):
        if settings.auth.type != 'form':
            return 'Unknown authentication type define in config.ini', 404

        action = request.args.get('action')
        if action == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            if check_credentials(username, password):
                session['logged_in'] = True
                return '', 204
        elif action == 'logout':
            session.clear()
            gc.collect()
            return '', 204

        return 'Unknown action', 400
