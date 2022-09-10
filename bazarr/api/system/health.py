# coding=utf-8

from flask import jsonify
from flask_restx import Resource, Namespace

from utilities.health import get_health_issues

from ..utils import authenticate

api_ns_system_health = Namespace('systemHealth', description='System health API endpoint')


@api_ns_system_health.route('system/health')
class SystemHealth(Resource):
    @authenticate
    def get(self):
        return jsonify(data=get_health_issues())
