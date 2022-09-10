# coding=utf-8

from flask import request, jsonify
from flask_restx import Resource, Namespace

from radarr.filesystem import browse_radarr_filesystem

from ..utils import authenticate

api_ns_files_radarr = Namespace('filesRadarr', description='Files Radarr API endpoint')


@api_ns_files_radarr.route('files/radarr')
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
