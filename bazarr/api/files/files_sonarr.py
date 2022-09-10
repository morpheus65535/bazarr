# coding=utf-8

from flask import request, jsonify
from flask_restx import Resource, Namespace

from sonarr.filesystem import browse_sonarr_filesystem

from ..utils import authenticate

api_ns_files_sonarr = Namespace('filesSonarr', description='Files Sonarr API endpoint')


@api_ns_files_sonarr.route('files/sonarr')
class BrowseSonarrFS(Resource):
    @authenticate
    def get(self):
        path = request.args.get('path') or ''
        data = []
        try:
            result = browse_sonarr_filesystem(path)
            if result is None:
                raise ValueError
        except Exception:
            return jsonify([])
        for item in result['directories']:
            data.append({'name': item['name'], 'children': True, 'path': item['path']})
        return jsonify(data)
