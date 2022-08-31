# coding=utf-8

from flask_restx import Namespace

from .files import BrowseBazarrFS
from .files_sonarr import BrowseSonarrFS
from .files_radarr import BrowseRadarrFS


api_ns_files = Namespace('files', description='Files API endpoint')

api_ns_files.add_resource(BrowseBazarrFS, 'files')
api_ns_files.add_resource(BrowseSonarrFS, 'files/sonarr')
api_ns_files.add_resource(BrowseRadarrFS, 'files/radarr')
