# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .series import Series


api_bp_series = Blueprint('api_series', __name__)
api = Api(api_bp_series)

api.add_resource(Series, '/series')
