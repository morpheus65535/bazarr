# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .plex import WebHooksPlex


api_bp_webhooks = Blueprint('api_webhooks', __name__)
api = Api(api_bp_webhooks)

api.add_resource(WebHooksPlex, '/webhooks/plex')
