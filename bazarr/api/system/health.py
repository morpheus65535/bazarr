# coding=utf-8

from flask import jsonify
from flask_restful import Resource

from utilities.utils import get_health_issues

from ..utils import authenticate


class SystemHealth(Resource):
    @authenticate
    def get(self):
        return jsonify(data=get_health_issues())
