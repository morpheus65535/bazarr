# coding=utf-8

bazarr_version = '0.9.1'

import os

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

from check_update import check_and_apply_update, check_releases
from server import app, webserver
from functools import wraps

# Check and install update on startup when running on Windows from installer
if args.release_update:
    check_and_apply_update()
# If not, update releases cache instead.
else:
    check_releases()

configure_proxy_func()

# Reset restart required warning on start
database.execute("UPDATE system SET configured='0', updated='0'")

# Load languages in database
load_language_in_db()

login_auth = settings.auth.type

update_notifier()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    apikey = settings.auth.apikey
    inject = dict()
    inject["apiKey"] = apikey
    inject["baseUrl"] = base_url

    template_url = base_url
    if not template_url.endswith("/"):
        template_url += "/"

    return render_template("index.html", BAZARR_SERVER_INJECT=inject, baseUrl=template_url)


@app.context_processor
def template_variable_processor():
    restart_required = database.execute("SELECT configured, updated FROM system", only_one=True)

    return dict(restart_required=restart_required['configured'], update_required=restart_required['updated'],
                settings=settings, args=args)



@app.route('/bazarr.log')
def download_log():
    r = Response()
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return send_file(os.path.join(args.config_dir, 'log', 'bazarr.log'), cache_timeout=0)


@app.route('/images/series/<path:url>', methods=['GET'])
def series_images(url):
    apikey = settings.sonarr.apikey
    url_image = (url_sonarr() + '/api/' + url + '?apikey=' + apikey).replace('poster-250', 'poster-500')
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route('/images/movies/<path:url>', methods=['GET'])
def movies_images(url):
    apikey = settings.radarr.apikey
    url_image = url_radarr() + '/api/' + url + '?apikey=' + apikey
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
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
