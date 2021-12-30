# coding=utf-8

from flask import jsonify
from flask_restful import Resource

from ..utils import authenticate
from utils import get_health_issues


class SystemHealth(Resource):
    @authenticate
    def get(self):
        return jsonify(data=get_health_issues())
