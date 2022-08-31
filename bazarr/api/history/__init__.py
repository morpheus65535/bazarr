# coding=utf-8

from flask_restx import Namespace

from .stats import HistoryStats


api_ns_history = Namespace('history', decription='History API endpoint')

api_ns_history.add_resource(HistoryStats, 'history/stats')
