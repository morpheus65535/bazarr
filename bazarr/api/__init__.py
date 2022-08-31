# coding=utf-8

from flask import url_for

from flask import Blueprint, url_for
from flask_restx import Api, apidoc

from .badges import api_ns_badges
from .system import api_ns_system
from .series import api_ns_series
from .episodes import api_ns_episodes
from .providers import api_ns_providers
from .subtitles import api_ns_subtitles
from .webhooks import api_ns_webhooks
from .history import api_ns_history
from .files import api_ns_files
from .movies import api_ns_movies
from .swaggerui import swaggerui_api_params

api_ns_list = [
    api_ns_badges,
    api_ns_episodes,
    api_ns_files,
    api_ns_history,
    api_ns_movies,
    api_ns_providers,
    api_ns_series,
    api_ns_subtitles,
    api_ns_system,
    api_ns_webhooks,
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


api = Api(api_bp, authorizations=authorizations, security='apikey', **swaggerui_api_params)

for api_ns in api_ns_list:
    api.add_namespace(api_ns, "/")
