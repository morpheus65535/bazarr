# coding=utf-8

from .leagues import api_ns_sports_leagues
from .events import api_ns_sports_events
from .history import api_ns_sports_history
from .wanted import api_ns_sports_wanted
from .blacklist import api_ns_sports_blacklist


api_ns_list_sports = [
    api_ns_sports_blacklist,
    api_ns_sports_events,
    api_ns_sports_history,
    api_ns_sports_leagues,
    api_ns_sports_wanted,
]
