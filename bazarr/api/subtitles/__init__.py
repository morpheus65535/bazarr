# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .subtitles import Subtitles
from .subtitles_info import SubtitleNameInfo


api_bp_subtitles = Blueprint('api_subtitles', __name__)
api = Api(api_bp_subtitles)

api.add_resource(Subtitles, '/subtitles')
api.add_resource(SubtitleNameInfo, '/subtitles/info')
