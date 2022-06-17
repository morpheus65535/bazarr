# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from utilities.filesystem import browse_bazarr_filesystem

from ..utils import authenticate


class BrowseBazarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        try:
            result = browse_bazarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        data = [{'name': item['name'], 'children': True, 'path': item['path']} for item in result['directories']]

        return jsonify(data)
