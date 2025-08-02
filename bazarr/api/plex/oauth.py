# coding=utf-8

from flask import redirect, request
from flask_restx import Namespace, Resource
from app.config import settings

api_ns_plex = Namespace('Plex', description='Plex OAuth operations')

@api_ns_plex.route('/oauth/login')
class PlexLogin(Resource):
    def get(self):
        from bazarr.plex.service import PlexService
        return {'redirect_url': PlexService.start_oauth()}

@api_ns_plex.route('/oauth/callback')
class PlexCallback(Resource):
    def get(self):
        from bazarr.plex.service import PlexService
        code = request.args.get('code')
        if not code:
            return {'error': 'Missing code'}, 400
        token_obj = PlexService.exchange_code_for_token(code)
        if not token_obj:
            return {'error': 'Failed to authenticate with Plex'}, 400
        return {'success': True, 'token': token_obj.to_dict()}

@api_ns_plex.route('/servers')
class PlexServers(Resource):
    def get(self):
        from bazarr.plex.service import PlexService
        servers = PlexService.get_servers()
        if servers is None:
            return {'error': 'Not authenticated'}, 401
        return {'servers': [s.to_dict() for s in servers]}

@api_ns_plex.route('/server')
class PlexSelectServer(Resource):
    def post(self):
        from bazarr.plex.service import PlexService
        data = request.json
        success = PlexService.save_selected_server(data)
        return {'success': success}
