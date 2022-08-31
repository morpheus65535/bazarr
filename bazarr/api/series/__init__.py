# coding=utf-8

from flask_restx import Namespace

from .series import Series


api_ns_series = Namespace('series', description='Series API endpoint')

api_ns_series.add_resource(Series, 'series')
