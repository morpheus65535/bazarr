# coding=utf-8

import gc

from flask import request, session
from flask_restful import Resource

from config import settings
from utils import check_credentials


class SystemAccount(Resource):
    def post(self):
        if settings.auth.type != 'form':
            return '', 405

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

        return '', 401
