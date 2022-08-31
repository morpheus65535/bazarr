# coding=utf-8

from flask_restx import Namespace

from .providers import Providers
from .providers_episodes import ProviderEpisodes
from .providers_movies import ProviderMovies


api_ns_providers = Namespace('providers', description='Providers API endpoint')

api_ns_providers.add_resource(Providers, 'providers')
api_ns_providers.add_resource(ProviderMovies, 'providers/movies')
api_ns_providers.add_resource(ProviderEpisodes, 'providers/episodes')
