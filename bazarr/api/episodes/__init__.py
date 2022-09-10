# coding=utf-8

from .episodes import api_ns_episodes
from .episodes_subtitles import api_ns_episodes_subtitles
from .history import api_ns_episodes_history
from .wanted import api_ns_episodes_wanted
from .blacklist import api_ns_episodes_blacklist


api_ns_list_episodes = [
    api_ns_episodes,
    api_ns_episodes_blacklist,
    api_ns_episodes_history,
    api_ns_episodes_subtitles,
    api_ns_episodes_wanted,
]
