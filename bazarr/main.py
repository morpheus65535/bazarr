# coding=utf-8

import os

bazarr_version = 'unknown'

version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
if os.path.isfile(version_file):
    with open(version_file, 'r') as f:
        bazarr_version = f.readline()
        bazarr_version = bazarr_version.rstrip('\n')

os.environ["BAZARR_VERSION"] = bazarr_version

import gc
import libs

import hashlib
import calendar

from get_args import args
from logger import empty_log
from config import settings, url_sonarr, url_radarr, configure_proxy_func, base_url

from init import *
from database import database

from notifier import update_notifier

from urllib.parse import unquote
from get_languages import load_language_in_db, language_from_alpha2, alpha3_from_alpha2
from flask import make_response, request, redirect, abort, render_template, Response, session, flash, url_for, \
    send_file, stream_with_context

from get_series import *
from get_episodes import *
from get_movies import *

from check_update import apply_update, check_if_new_update, check_releases
from server import app, webserver
from functools import wraps

# Install downloaded update
if bazarr_version != '':
    apply_update()
check_releases()

configure_proxy_func()

# Reset the updated once Bazarr have been restarted after an update
database.execute("UPDATE system SET updated='0'")

# Load languages in database
load_language_in_db()

login_auth = settings.auth.type

update_notifier()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")


@app.context_processor
def template_variable_processor():
    updated = False
    try:
        updated = database.execute("SELECT updated FROM system", only_one=True)['updated']
    except:
        pass

    inject = dict()
    inject["apiKey"] = settings.auth.apikey
    inject["baseUrl"] = base_url
    inject["canUpdate"] = not args.no_update
    inject["hasUpdate"] = updated != '0'

    template_url = base_url
    if not template_url.endswith("/"):
        template_url += "/"

    return dict(BAZARR_SERVER_INJECT=inject, baseUrl=template_url)



@app.route('/bazarr.log')
def download_log():

    return send_file(os.path.join(args.config_dir, 'log', 'bazarr.log'), cache_timeout=0, as_attachment=True)


@app.route('/images/series/<path:url>', methods=['GET'])
def series_images(url):
    url = url.strip("/")
    apikey = settings.sonarr.apikey
    baseUrl = settings.sonarr.base_url
    url_image = (url_sonarr() + '/api/' + url.lstrip(baseUrl) + '?apikey=' + apikey).replace('poster-250', 'poster-500')
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return '', 404
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route('/images/movies/<path:url>', methods=['GET'])
def movies_images(url):
    apikey = settings.radarr.apikey
    baseUrl = settings.radarr.base_url
    url_image = url_radarr() + '/api/' + url.lstrip(baseUrl) + '?apikey=' + apikey
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
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
    database.execute("UPDATE system SET configured = 1")


@app.route('/test', methods=['GET'])
@app.route('/test/<protocol>/<path:url>', methods=['GET'])
def proxy(protocol, url):
    url = protocol + '://' + unquote(url)
    params = request.args
    try:
        result = requests.get(url, params, allow_redirects=False, verify=False, timeout=5)
    except Exception as e:
        return dict(status=False, error=repr(e))
    else:
        if result.status_code == 200:
            try:
                version = result.json()['version']
                return dict(status=True, version=version)
            except Exception:
                return dict(status=False, error='Error Occured. Check your settings.')
        elif result.status_code == 401:
            return dict(status=False, error='Access Denied. Check API key.')
        elif 300 <= result.status_code <= 399:
            return dict(status=False, error='Wrong URL Base.')
        else:
            return dict(status=False, error=result.raise_for_status())


if __name__ == "__main__":
    webserver.start()
