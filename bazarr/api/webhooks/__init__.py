# coding=utf-8

from flask_restx import Namespace

from .plex import WebHooksPlex
from .sonarr import WebHooksSonarr
from .radarr import WebHooksRadarr


api_ns_webhooks = Namespace('webhooks', description='Webhooks API endpoint')

api_ns_webhooks.add_resource(WebHooksPlex, 'webhooks/plex')
api_ns_webhooks.add_resource(WebHooksSonarr, 'webhooks/sonarr')
api_ns_webhooks.add_resource(WebHooksRadarr, 'webhooks/radarr')
