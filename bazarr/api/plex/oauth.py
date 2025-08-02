# coding=utf-8

import os
import requests
from flask import Blueprint, redirect, request, session, jsonify
from app.config import settings, save_settings

plex_oauth = Blueprint('plex_oauth', __name__)

@plex_oauth.route('/api/plex/oauth/login')
def plex_login():
    from bazarr.plex.service import PlexService
    return redirect(PlexService.start_oauth())

@plex_oauth.route('/api/plex/oauth/callback')
def plex_callback():
    from bazarr.plex.service import PlexService
    code = request.args.get('code')
    if not code:
        return 'Missing code', 400
    token_obj = PlexService.exchange_code_for_token(code)
    if not token_obj:
        return 'Failed to authenticate with Plex', 400
    return redirect('/settings/plex')

@plex_oauth.route('/api/plex/servers')
def plex_servers():
    from bazarr.plex.service import PlexService
    servers = PlexService.get_servers()
    if servers is None:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'servers': [s.to_dict() for s in servers]})

@plex_oauth.route('/api/plex/server', methods=['POST'])
def plex_select_server():
    from bazarr.plex.service import PlexService
    data = request.json
    success = PlexService.save_selected_server(data)
    return jsonify({'success': success})
