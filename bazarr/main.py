# coding=utf-8

bazarr_version = '0.9.0.6'

import os
os.environ["BAZARR_VERSION"] = bazarr_version

import gc
import sys
import libs

import hashlib
import apprise
import requests
import calendar


from get_args import args
from config import settings, url_sonarr, url_radarr, url_radarr_short, url_sonarr_short, base_url, configure_proxy_func

from init import *
from database import database, dict_mapper

from notifier import update_notifier

from urllib.parse import unquote
from get_languages import load_language_in_db, language_from_alpha3, language_from_alpha2, alpha2_from_alpha3, \
    alpha3_from_alpha2
from flask import make_response, request, redirect, abort, render_template, Response, session, flash, url_for, \
    send_file, stream_with_context

from get_series import *
from get_episodes import *
from get_movies import *

from check_update import check_and_apply_update
from server import app, webserver
from functools import wraps

# Check and install update on startup when running on Windows from installer
if args.release_update:
    check_and_apply_update()

configure_proxy_func()

# Reset restart required warning on start
database.execute("UPDATE system SET configured='0', updated='0'")

# Load languages in database
load_language_in_db()

login_auth = settings.auth.type

update_notifier()


def check_credentials(user, pw):
    username = settings.auth.username
    password = settings.auth.password
    if hashlib.md5(pw.encode('utf-8')).hexdigest() == password and user == username:
        return True
    return False


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if settings.auth.type == 'basic':
            auth = request.authorization
            if not (auth and check_credentials(request.authorization.username, request.authorization.password)):
                return ('Unauthorized', 401, {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })

            return f(*args, **kwargs)
        elif settings.auth.type == 'form':
            if 'logged_in' in session:
                return f(*args, **kwargs)
            else:
                flash("You need to login first")
                return redirect(url_for('login_page'))
        else:
            return f(*args, **kwargs)
    return wrap


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

@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error = ''
    password_reset = False
    if settings.auth.password == hashlib.md5(settings.auth.username.encode('utf-8')).hexdigest():
        password_reset = True
    try:
        if request.method == "POST":
            if check_credentials(request.form['username'], request.form['password']):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash("You are now logged in")
                return redirect(url_for("redirect_root"))
            else:
                error = "Invalid credentials, try again."
        gc.collect()

        # return render_template("login.html", error=error, password_reset=password_reset)
        return ""

    except Exception as e:
        # flash(e)
        error = "Invalid credentials, try again."
        # return "render_template("login.html", error=error)"
        return ""


@app.context_processor
def template_variable_processor():
    restart_required = database.execute("SELECT configured, updated FROM system", only_one=True)

    return dict(restart_required=restart_required['configured'], update_required=restart_required['updated'],
                settings=settings, args=args)


def api_authorize():
    if 'apikey' in request.GET.dict:
        if request.GET.dict['apikey'][0] == settings.auth.apikey:
            return
        else:
            abort(401, 'Unauthorized')
    else:
        abort(401, 'Unauthorized')


def post_get(name, default=''):
    return request.POST.get(name, default).strip()


@app.route("/logout/")
@login_required
def logout():
    if settings.auth.type == 'basic':
        return abort(401)
    elif settings.auth.type == 'form':
        session.clear()
        flash("You have been logged out!")
        gc.collect()
        return redirect(url_for('redirect_root'))


@app.route('/bazarr.log')
@login_required
def download_log():
    r = Response()
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return send_file(os.path.join(args.config_dir, 'log', 'bazarr.log'), cache_timeout=0)


@app.route('/images/series/<path:url>', methods=['GET'])
@login_required
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
@login_required
def movies_images(url):
    apikey = settings.radarr.apikey
    url_image = url_radarr() + '/api/' + url + '?apikey=' + apikey
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route('/check_update')
@login_required
def check_update():
    if not args.no_update:
        check_and_apply_update()

    return '', 200


def configured():
    database.execute("UPDATE system SET configured = 1")


@app.route('/test_url', methods=['GET'])
@app.route('/test_url/<protocol>/<path:url>', methods=['GET'])
@login_required
def test_url(protocol, url):
    url = protocol + '://' + unquote(url)
    try:
        result = requests.get(url, allow_redirects=False, verify=False, timeout=5)
    except Exception as e:
        return dict(status=False, error=repr(e))
    else:
        if result.status_code == 200:
            return dict(status=True, version=result.json()['version'])
        elif result.status_code == 401:
            return dict(status=False, error='Access Denied. Check API key.')
        elif 300 <= result.status_code <= 399:
            return dict(status=False, error='Wrong URL Base.')
        else:
            return dict(status=False, error=result.raise_for_status())


@app.route('/test_notification', methods=['GET'])
@app.route('/test_notification/<protocol>/<path:provider>', methods=['GET'])
@login_required
def test_notification(protocol, provider):

    provider = unquote(provider)

    asset = apprise.AppriseAsset(async_mode=False)

    apobj = apprise.Apprise(asset=asset)

    apobj.add(protocol + "://" + provider)

    apobj.notify(
        title='Bazarr test notification',
        body='Test notification'
    )

    return '', 200


if __name__ == "__main__":
    webserver.start()
