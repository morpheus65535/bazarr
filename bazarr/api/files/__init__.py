# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .files import BrowseBazarrFS


api_bp_files = Blueprint('api_files', __name__)
api = Api(api_bp_files)

api.add_resource(BrowseBazarrFS, '/files')
