# coding=utf-8

from flask_restx import Namespace

from .badges import Badges


api_ns_badges = Namespace('badges', description='Badges API endpoint')

api_ns_badges.add_resource(Badges, 'badges')
