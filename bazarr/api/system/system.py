# coding=utf-8

from flask import request
from flask_restful import Resource

from ..utils import authenticate


class System(Resource):
    @authenticate
    def post(self):
        from server import webserver
        action = request.args.get('action')
        if action == "shutdown":
            webserver.shutdown()
        elif action == "restart":
            webserver.restart()
        return '', 204
