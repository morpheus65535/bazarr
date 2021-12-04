# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .files import BrowseBazarrFS
from .files_sonarr import BrowseSonarrFS
from .files_radarr import BrowseRadarrFS


api_bp_files = Blueprint('api_files', __name__)
api = Api(api_bp_files)

api.add_resource(BrowseBazarrFS, '/files')
api.add_resource(BrowseSonarrFS, '/files/sonarr')
api.add_resource(BrowseRadarrFS, '/files/radarr')
