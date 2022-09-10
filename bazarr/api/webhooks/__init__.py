# coding=utf-8

from .plex import api_ns_webhooks_plex
from .sonarr import api_ns_webhooks_sonarr
from .radarr import api_ns_webhooks_radarr


api_ns_list_webhooks = [
    api_ns_webhooks_plex,
    api_ns_webhooks_sonarr,
    api_ns_webhooks_radarr,
]
