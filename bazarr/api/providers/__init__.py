# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .providers import Providers
from .providers_episodes import ProviderEpisodes
from .providers_movies import ProviderMovies


api_bp_providers = Blueprint('api_providers', __name__)
api = Api(api_bp_providers)

api.add_resource(Providers, '/providers')
api.add_resource(ProviderMovies, '/providers/movies')
api.add_resource(ProviderEpisodes, '/providers/episodes')
