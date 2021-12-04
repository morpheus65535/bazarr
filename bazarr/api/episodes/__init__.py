# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .episodes import Episodes
from .episodes_subtitles import EpisodesSubtitles
from .history import EpisodesHistory
from .wanted import EpisodesWanted
from .blacklist import EpisodesBlacklist


api_bp_episodes = Blueprint('api_episodes', __name__)
api = Api(api_bp_episodes)

api.add_resource(Episodes, '/episodes')
api.add_resource(EpisodesWanted, '/episodes/wanted')
api.add_resource(EpisodesSubtitles, '/episodes/subtitles')
api.add_resource(EpisodesHistory, '/episodes/history')
api.add_resource(EpisodesBlacklist, '/episodes/blacklist')
