# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .series import Series
from .rootfolders import SeriesRootfolders
from .directories import SeriesDirectories
from .lookup import SeriesLookup
from .add import SeriesAdd
from .modify import SeriesModify


api_bp_series = Blueprint('api_series', __name__)
api = Api(api_bp_series)

api.add_resource(Series, '/series')
api.add_resource(SeriesRootfolders, '/series/rootfolders')
api.add_resource(SeriesDirectories, '/series/directories')
api.add_resource(SeriesLookup, '/series/lookup')
api.add_resource(SeriesAdd, '/series/add')
api.add_resource(SeriesModify, '/series/modify')
