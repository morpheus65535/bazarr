# coding=utf-8

from flask_restx import Resource, Namespace, reqparse

from app.database import get_profiles_list

from ..utils import authenticate

api_ns_system_languages_profiles = Namespace('System Languages Profiles', description='List languages profiles')


@api_ns_system_languages_profiles.route('system/languages/profiles')
class LanguagesProfiles(Resource):
    @authenticate
    @api_ns_system_languages_profiles.doc(parser=None)
    @api_ns_system_languages_profiles.response(200, 'Success')
    @api_ns_system_languages_profiles.response(401, 'Not Authenticated')
    def get(self):
        """List languages profiles"""
        return get_profiles_list()
