# coding=utf-8

from flask_restx import Namespace

from .episodes import Episodes
from .episodes_subtitles import EpisodesSubtitles
from .history import EpisodesHistory
from .wanted import EpisodesWanted
from .blacklist import EpisodesBlacklist


api_ns_episodes = Namespace('episodes', description='Episodes API endpoint')

api_ns_episodes.add_resource(Episodes, 'episodes')
api_ns_episodes.add_resource(EpisodesWanted, 'episodes/wanted')
api_ns_episodes.add_resource(EpisodesSubtitles, 'episodes/subtitles')
api_ns_episodes.add_resource(EpisodesHistory, 'episodes/history')
api_ns_episodes.add_resource(EpisodesBlacklist, 'episodes/blacklist')
