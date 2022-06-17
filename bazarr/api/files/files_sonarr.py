# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from sonarr.filesystem import browse_sonarr_filesystem

from ..utils import authenticate


class BrowseSonarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        try:
            result = browse_sonarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        data = [{'name': item['name'], 'children': True, 'path': item['path']} for item in result['directories']]

        return jsonify(data)
