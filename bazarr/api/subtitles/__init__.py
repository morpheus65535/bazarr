# coding=utf-8

from flask_restx import Namespace

from .subtitles import Subtitles
from .subtitles_info import SubtitleNameInfo


api_ns_subtitles = Namespace('subtitles', description='Subtitles API endpoint')

api_ns_subtitles.add_resource(Subtitles, 'subtitles')
api_ns_subtitles.add_resource(SubtitleNameInfo, 'subtitles/info')
