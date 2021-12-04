# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .stats import HistoryStats


api_bp_history = Blueprint('api_history', __name__)
api = Api(api_bp_history)

api.add_resource(HistoryStats, '/history/stats')
