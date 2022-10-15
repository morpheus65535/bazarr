# coding=utf-8

from .files import api_ns_files
from .files_sonarr import api_ns_files_sonarr
from .files_radarr import api_ns_files_radarr

api_ns_list_files = [
    api_ns_files,
    api_ns_files_radarr,
    api_ns_files_sonarr,
]
