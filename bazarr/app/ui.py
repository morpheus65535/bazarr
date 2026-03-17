# coding=utf-8

import os
import requests
import mimetypes

from flask import (request, abort, render_template, Response, session, send_file, stream_with_context, Blueprint,
                   redirect)
from functools import wraps
from urllib.parse import unquote

from constants import HEADERS
from literals import FILE_LOG
from sonarr.info import url_api_sonarr
from radarr.info import url_api_radarr
from utilities.helper import check_credentials
from utilities.central import get_log_file_path

from .config import settings, base_url
from .database import database, System
from .get_args import args

frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'build')

ui_bp = Blueprint('ui', __name__,
                  template_folder=frontend_build_path,
                  static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend',
                                             'build', 'assets'),
                  static_url_path='/assets')

if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'build',
                               'images')):
    static_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'build',
                                    'images')
else:
    static_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'public',
                                    'images')
static_bp = Blueprint('images', __name__, static_folder=static_directory, static_url_path='/images')

ui_bp.register_blueprint(static_bp)

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/x-icon', '.ico')
mimetypes.add_type('application/manifest+json', '.webmanifest')

pwa_assets = ['registerSW.js', 'manifest.webmanifest', 'sw.js']


def check_login(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
        if settings.auth.type == 'basic':
            auth = request.authorization
            if not (auth and
                    check_credentials(request.authorization.username, request.authorization.password, request)):
                return ('Unauthorized', 401, {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })
        elif settings.auth.type == 'form':
            if 'logged_in' not in session:
                return abort(401, message="Unauthorized")
        return actual_method(*args, **kwargs)
    return wrapper


@ui_bp.route('/', defaults={'path': ''})
@ui_bp.route('/<path:path>')
def catch_all(path):
    if path.startswith('login') and settings.auth.type not in ['basic', 'form']:
        # login page has been accessed when no authentication is enabled
        return redirect(base_url or "/", code=302)

    # PWA Assets are returned from frontend root folder
    if path in pwa_assets or path.startswith('workbox-'):
        return send_file(os.path.join(frontend_build_path, path))

    auth = True
    if settings.auth.type == 'basic':
        auth = request.authorization
        if not (auth and check_credentials(request.authorization.username, request.authorization.password, request,
                                           log_success=False)):
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })
    elif settings.auth.type == 'form':
        if 'logged_in' not in session or not session['logged_in']:
            auth = False

    try:
        updated = database.scalar(System.updated)
    except Exception:
        updated = '0'

    try:
        configured = database.scalar(System.configured)
    except Exception:
        configured = '0'

    inject = dict()

    if not path.startswith('api/'):
        inject["baseUrl"] = base_url
        inject["canUpdate"] = not args.no_update
        inject["hasUpdate"] = updated != '0'
        inject["isConfigured"] = configured != '0'

        if auth:
            inject["apiKey"] = settings.auth.apikey

    template_url = base_url
    if not template_url.endswith("/"):
        template_url += "/"

    return render_template("index.html", BAZARR_SERVER_INJECT=inject, baseUrl=template_url)


@check_login
@ui_bp.route('/' + FILE_LOG)
def download_log():
    return send_file(get_log_file_path(), max_age=0, as_attachment=True)


@check_login
@ui_bp.route('/images/series/<path:url>', methods=['GET'])
def series_images(url):
    url = url.strip("/")
    apikey = settings.sonarr.apikey
    baseUrl = settings.sonarr.base_url
    url_image = f'{url_api_sonarr()}{url.lstrip(baseUrl)}?apikey={apikey}'.replace('poster-250', 'poster-500')
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False, headers=HEADERS)
    except Exception:
        return '', 404
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@check_login
@ui_bp.route('/images/movies/<path:url>', methods=['GET'])
def movies_images(url):
    apikey = settings.radarr.apikey
    baseUrl = settings.radarr.base_url
    url_image = f'{url_api_radarr()}{url.lstrip(baseUrl)}?apikey={apikey}'
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False, headers=HEADERS)
    except Exception:
        return '', 404
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@check_login
@ui_bp.route('/system/backup/download/<path:filename>', methods=['GET'])
def backup_download(filename):
    fullpath = os.path.normpath(os.path.join(settings.backup.folder, filename))
    if not fullpath.startswith(settings.backup.folder):
        return '', 404
    else:
        return send_file(fullpath, max_age=0, as_attachment=True)


@ui_bp.route('/api/swaggerui/static/<path:filename>', methods=['GET'])
def swaggerui_static(filename):
    basepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'libs', 'flask_restx',
                            'static')
    fullpath = os.path.realpath(os.path.join(basepath, filename))
    # Use startswith to prevent path traversal
    if not fullpath.startswith(os.path.realpath(basepath) + os.sep):
        return '', 404
    else:
        return send_file(fullpath)


@check_login
@ui_bp.route('/test', methods=['GET'])
@ui_bp.route('/test/<protocol>/<path:url>', methods=['GET'])
def proxy(protocol, url):
    if protocol.lower() not in ['http', 'https']:
        return dict(status=False, error='Unsupported protocol', code=0)
    url = f'{protocol}://{unquote(url)}'
    params = request.args
    try:
        result = requests.get(url, params, allow_redirects=False, verify=False, timeout=5, headers=HEADERS)
    except Exception as e:
        return dict(status=False, error=repr(e))
    else:
        if result.status_code == 200:
            try:
                version = result.json()['version']
                return dict(status=True, version=version, code=result.status_code)
            except Exception:
                return dict(status=False, error='Error Occurred. Check your settings.', code=result.status_code)
        elif result.status_code == 401:
            return dict(status=False, error='Access Denied. Check API key.', code=result.status_code)
        elif result.status_code == 404:
            return dict(status=False, error='Cannot get version. Maybe unsupported legacy API call?',
                        code=result.status_code)
        elif 300 <= result.status_code <= 399:
            return dict(status=False, error='Wrong URL Base.', code=result.status_code)
        else:
            return dict(status=False, error=result.raise_for_status(), code=result.status_code)
