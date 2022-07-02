# coding=utf-8

from flask import jsonify
from flask_restful import Resource

from app.database import get_profiles_list

from ..utils import authenticate


class LanguagesProfiles(Resource):
    @authenticate
    def get(self):
        return jsonify(get_profiles_list())
