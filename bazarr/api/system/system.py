# coding=utf-8

from flask import request
from flask_restx import Resource, Namespace

from ..utils import authenticate

api_ns_system = Namespace('system', description='System API endpoint')


@api_ns_system.hide
@api_ns_system.route('system')
class System(Resource):
    @authenticate
    def post(self):
        from app.server import webserver
        action = request.args.get('action')
        if action == "shutdown":
            webserver.shutdown()
        elif action == "restart":
            webserver.restart()
        return '', 204
