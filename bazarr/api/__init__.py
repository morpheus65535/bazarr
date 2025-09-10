# coding=utf-8

from flask import Blueprint, url_for
from flask_restx import Api, apidoc

from .badges import api_ns_list_badges
from .episodes import api_ns_list_episodes
from .files import api_ns_list_files
from .history import api_ns_list_history
from .movies import api_ns_list_movies
from .providers import api_ns_list_providers
from .series import api_ns_list_series
from .subtitles import api_ns_list_subtitles
from .system import api_ns_list_system
from .webhooks import api_ns_list_webhooks
from .plex import api_ns_list_plex
from .swaggerui import swaggerui_api_params

api_ns_list = [
    api_ns_list_badges,
    api_ns_list_episodes,
    api_ns_list_files,
    api_ns_list_history,
    api_ns_list_movies,
    api_ns_list_providers,
    api_ns_list_series,
    api_ns_list_subtitles,
    api_ns_list_system,
    api_ns_list_webhooks,
    api_ns_list_plex,
]

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

api_bp = Blueprint('api', __name__, url_prefix='/api')


@apidoc.apidoc.add_app_template_global
def swagger_static(filename):
    return url_for('ui.swaggerui_static', filename=filename)


api = Api(api_bp, authorizations=authorizations, security='apikey', validate=True, **swaggerui_api_params)

for api_ns in api_ns_list:
    for item in api_ns:
        api.add_namespace(item, "/")
