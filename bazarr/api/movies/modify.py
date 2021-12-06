# coding=utf-8

# from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate


class MoviesModify(Resource):
    @authenticate
    def patch(self):
        # modify an existing movie in database
        pass
