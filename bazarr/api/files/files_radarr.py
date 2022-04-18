# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from radarr.filesystem import browse_radarr_filesystem

from ..utils import authenticate


class BrowseRadarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        try:
            result = browse_radarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)
