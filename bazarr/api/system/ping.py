# coding=utf-8

from flask_restx import Resource, Namespace

api_ns_system_ping = Namespace('System Ping', description='Unauthenticated endpoint to check Bazarr availability')


@api_ns_system_ping.route('system/ping')
class SystemPing(Resource):
    @api_ns_system_ping.response(200, "Success")
    def get(self):
        """Return status and http 200"""
        return {'status': 'OK'}, 200
