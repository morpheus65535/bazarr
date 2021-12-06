# coding=utf-8

from flask_restful import Resource

from ..utils import authenticate


class SeriesModify(Resource):
    @authenticate
    def patch(self):
        # modify an existing series in database
        pass
