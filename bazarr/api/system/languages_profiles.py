# coding=utf-8

from flask import jsonify
from flask_restx import Resource, Namespace

from app.database import get_profiles_list

from ..utils import authenticate

api_ns_system_languages_profiles = Namespace('systemLanguagesProfiles', description='System languages profiles API '
                                                                                    'endpoint')


@api_ns_system_languages_profiles.route('system/languages/profiles')
class LanguagesProfiles(Resource):
    @authenticate
    def get(self):
        return jsonify(get_profiles_list())
