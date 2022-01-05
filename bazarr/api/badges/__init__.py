# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .badges import Badges


api_bp_badges = Blueprint('api_badges', __name__)
api = Api(api_bp_badges)

api.add_resource(Badges, '/badges')
