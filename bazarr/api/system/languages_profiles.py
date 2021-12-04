# coding=utf-8

from flask import jsonify
from flask_restful import Resource

from ..utils import authenticate
from database import get_profiles_list


class LanguagesProfiles(Resource):
    @authenticate
    def get(self):
        return jsonify(get_profiles_list())
