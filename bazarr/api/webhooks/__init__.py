# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .plex import WebHooksPlex
from .sonarr import WebHooksSonarr
from .radarr import WebHooksRadarr


api_bp_webhooks = Blueprint("api_webhooks", __name__)
api = Api(api_bp_webhooks)

api.add_resource(WebHooksPlex, "/webhooks/plex")
api.add_resource(WebHooksSonarr, "/webhooks/sonarr")
api.add_resource(WebHooksRadarr, "/webhooks/radarr")
