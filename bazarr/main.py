# coding=utf-8

import os

bazarr_version = 'unknown'

version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
if os.path.isfile(version_file):
    with open(version_file, 'r') as f:
        bazarr_version = f.readline()
        bazarr_version = bazarr_version.rstrip('\n')

os.environ["BAZARR_VERSION"] = bazarr_version.lstrip('v')

import libs  # noqa W0611

from get_args import args  # noqa E402
from config import settings, url_sonarr, url_radarr, configure_proxy_func, base_url  # noqa E402

from init import *  # noqa E402
from database import System  # noqa E402

from notifier import update_notifier  # noqa E402

from urllib.parse import unquote  # noqa E402
from get_languages import load_language_in_db  # noqa E402
from flask import request, redirect, abort, render_template, Response, session, send_file, stream_with_context  # noqa E402
from threading import Thread  # noqa E402
import requests  # noqa E402

from get_series import *  # noqa E402
from get_episodes import *  # noqa E402
from get_movies import *  # noqa E402
from signalr_client import sonarr_signalr_client, radarr_signalr_client  # noqa E402

from check_update import apply_update, check_releases  # noqa E402
from server import app, webserver  # noqa E402
from functools import wraps  # noqa E402
from utils import check_credentials, get_sonarr_info, get_radarr_info  # noqa E402

# Install downloaded update
if bazarr_version != '':
    apply_update()
check_releases()

configure_proxy_func()

# Reset the updated once Bazarr have been restarted after an update
System.update({System.updated: '0'}).execute()

# Load languages in database
load_language_in_db()

login_auth = settings.auth.type

update_notifier()

headers = {"User-Agent": os.environ["SZ_USER_AGENT"]}


def check_login(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
        if settings.auth.type == 'basic':
            auth = request.authorization
            if not (auth and check_credentials(request.authorization.username, request.authorization.password)):
                return ('Unauthorized', 401, {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })
        elif settings.auth.type == 'form':
            if 'logged_in' not in session:
                return abort(401, message="Unauthorized")
        actual_method(*args, **kwargs)


@app.errorhandler(404)
def page_not_found(e):
    return redirect(base_url, code=302)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    auth = True
    if settings.auth.type == 'basic':
        auth = request.authorization
        if not (auth and check_credentials(request.authorization.username, request.authorization.password)):
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })
    elif settings.auth.type == 'form':
        if 'logged_in' not in session:
            auth = False

    try:
        updated = System.get().updated
    except Exception:
        updated = '0'

    inject = dict()
    inject["baseUrl"] = base_url
    inject["canUpdate"] = not args.no_update
    inject["hasUpdate"] = updated != '0'

    if auth:
        inject["apiKey"] = settings.auth.apikey

    template_url = base_url
    if not template_url.endswith("/"):
        template_url += "/"

    return render_template("index.html", BAZARR_SERVER_INJECT=inject, baseUrl=template_url)


@check_login
@app.route('/bazarr.log')
def download_log():
    return send_file(os.path.join(args.config_dir, 'log', 'bazarr.log'), cache_timeout=0, as_attachment=True)


@check_login
@app.route('/images/series/<path:url>', methods=['GET'])
def series_images(url):
    url = url.strip("/")
    apikey = settings.sonarr.apikey
    baseUrl = settings.sonarr.base_url
    if get_sonarr_info.is_legacy():
        url_image = (url_sonarr() + '/api/' + url.lstrip(baseUrl) + '?apikey=' +
                     apikey).replace('poster-250', 'poster-500')
    else:
        url_image = (url_sonarr() + '/api/v3/' + url.lstrip(baseUrl) + '?apikey=' +
                     apikey).replace('poster-250', 'poster-500')
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False, headers=headers)
    except Exception:
        return '', 404
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@check_login
@app.route('/images/movies/<path:url>', methods=['GET'])
def movies_images(url):
    apikey = settings.radarr.apikey
    baseUrl = settings.radarr.base_url
    if get_radarr_info.is_legacy():
        url_image = url_radarr() + '/api/' + url.lstrip(baseUrl) + '?apikey=' + apikey
    else:
        url_image = url_radarr() + '/api/v3/' + url.lstrip(baseUrl) + '?apikey=' + apikey
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False, headers=headers)
    except Exception:
        return '', 404
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


# @app.route('/check_update')
# @authenticate
# def check_update():
#     if not args.no_update:
#         check_and_apply_update()

#     return '', 200


def configured():
    System.update({System.configured: '1'}).execute()


@check_login
@app.route('/test', methods=['GET'])
@app.route('/test/<protocol>/<path:url>', methods=['GET'])
def proxy(protocol, url):
    url = protocol + '://' + unquote(url)
    params = request.args
    try:
        result = requests.get(url, params, allow_redirects=False, verify=False, timeout=5, headers=headers)
    except Exception as e:
        return dict(status=False, error=repr(e))
    else:
        if result.status_code == 200:
            try:
                version = result.json()['version']
                return dict(status=True, version=version)
            except Exception:
                return dict(status=False, error='Error Occurred. Check your settings.')
        elif result.status_code == 401:
            return dict(status=False, error='Access Denied. Check API key.')
        elif result.status_code == 404:
            return dict(status=False, error='Cannot get version. Maybe unsupported legacy API call?')
        elif 300 <= result.status_code <= 399:
            return dict(status=False, error='Wrong URL Base.')
        else:
            return dict(status=False, error=result.raise_for_status())


if settings.general.getboolean('use_sonarr'):
    Thread(target=sonarr_signalr_client.start).start()
if settings.general.getboolean('use_radarr'):
    Thread(target=radarr_signalr_client.start).start()


if __name__ == "__main__":
    webserver.start()
