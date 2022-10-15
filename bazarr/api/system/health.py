# coding=utf-8

from flask_restx import Resource, Namespace

from utilities.health import get_health_issues

from ..utils import authenticate

api_ns_system_health = Namespace('System Health', description='List health issues')


@api_ns_system_health.route('system/health')
class SystemHealth(Resource):
    @authenticate
    @api_ns_system_health.doc(parser=None)
    @api_ns_system_health.response(200, 'Success')
    @api_ns_system_health.response(401, 'Not Authenticated')
    def get(self):
        """List health issues"""
        return {'data': get_health_issues()}
