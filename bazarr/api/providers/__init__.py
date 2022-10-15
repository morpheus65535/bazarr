# coding=utf-8

from .providers import api_ns_providers
from .providers_episodes import api_ns_providers_episodes
from .providers_movies import api_ns_providers_movies


api_ns_list_providers = [
    api_ns_providers,
    api_ns_providers_episodes,
    api_ns_providers_movies,
]
