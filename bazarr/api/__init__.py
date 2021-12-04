# coding=utf-8

from .badges import api_bp_badges
from .system import api_bp_system
from .series import api_bp_series
from .episodes import api_bp_episodes
from .providers import api_bp_providers
from .subtitles import api_bp_subtitles
from .webhooks import api_bp_webhooks
from .history import api_bp_history
from .files import api_bp_files
from .movies import api_bp_movies

api_bp_list = [
    api_bp_badges,
    api_bp_system,
    api_bp_series,
    api_bp_episodes,
    api_bp_providers,
    api_bp_subtitles,
    api_bp_webhooks,
    api_bp_history,
    api_bp_files,
    api_bp_movies
]
