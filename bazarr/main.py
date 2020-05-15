# coding=utf-8

bazarr_version = '0.9'

import os
os.environ["SZ_USER_AGENT"] = "Bazarr/1"
os.environ["BAZARR_VERSION"] = bazarr_version

import gc
import sys
import libs
import io

import hashlib
import warnings
import apprise
import requests
import calendar


from get_args import args
from logger import empty_log
from config import settings, url_sonarr, url_radarr, url_radarr_short, url_sonarr_short, base_url, configure_proxy_func

from init import *
import logging
from database import database, dict_mapper

from notifier import update_notifier

from waitress.server import create_server

from urllib.parse import unquote
from get_languages import load_language_in_db, language_from_alpha3, language_from_alpha2, alpha2_from_alpha3
from flask import make_response, request, redirect, abort, render_template, Response, session, flash, url_for, \
    send_file, stream_with_context

from get_series import *
from get_episodes import *
from get_movies import *

from scheduler import Scheduler
from check_update import check_and_apply_update
from functools import wraps

from app import create_app
app = create_app()

from api import api_bp
app.register_blueprint(api_bp)

scheduler = Scheduler()

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

        return render_template("login.html", error=error, password_reset=password_reset)

    except Exception as e:
        # flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error=error)


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


@app.route('/emptylog')
@login_required
def emptylog():
    empty_log()
    return '', 200


@app.route('/bazarr.log')
@login_required
def download_log():
    r = Response()
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return send_file(os.path.join(args.config_dir, 'log', 'bazarr.log'), cache_timeout=0)


@app.route('/image_proxy/<path:url>', methods=['GET'])
@login_required
def image_proxy(url):
    apikey = settings.sonarr.apikey
    url_image = (url_sonarr() + '/api/' + url + '?apikey=' + apikey).replace('poster-250', 'poster-500')
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route('/image_proxy_movies/<path:url>', methods=['GET'])
@login_required
def image_proxy_movies(url):
    apikey = settings.radarr.apikey
    url_image = url_radarr() + '/api/' + url + '?apikey=' + apikey
    try:
        req = requests.get(url_image, stream=True, timeout=15, verify=False)
    except:
        return None
    else:
        return Response(stream_with_context(req.iter_content(2048)), content_type=req.headers['content-type'])


@app.route("/")
@login_required
def redirect_root():
    if settings.general.getboolean('use_sonarr'):
        return redirect(url_for('series'))
    elif settings.general.getboolean('use_radarr'):
        return redirect(url_for('movies'))
    else:
        return redirect(url_for('settingsgeneral'))


@app.route('/series/')
@login_required
def series():
    return render_template('series.html')


@app.route('/serieseditor/')
@login_required
def serieseditor():
    return render_template('serieseditor.html')


@app.route('/episodes/<no>')
@login_required
def episodes(no):
    return render_template('episodes.html', id=str(no))


@app.route('/movies')
@login_required
def movies():
    return render_template('movies.html')


@app.route('/movieseditor')
@login_required
def movieseditor():
    return render_template('movieseditor.html')


@app.route('/movie/<no>')
@login_required
def movie(no):
    return render_template('movie.html', id=str(no))


@app.route('/history/series/')
@login_required
def historyseries():
    return render_template('historyseries.html')


@app.route('/history/movies/')
@login_required
def historymovies():
    return render_template('historymovies.html')


@app.route('/wanted/series/')
@login_required
def wantedseries():
    return render_template('wantedseries.html')


@app.route('/wanted/movies/')
@login_required
def wantedmovies():
    return render_template('wantedmovies.html')


@app.route('/settings/general/')
@login_required
def settingsgeneral():
    return render_template('settingsgeneral.html')


@app.route('/settings/sonarr/')
@login_required
def settingssonarr():
    return render_template('settingssonarr.html')


@app.route('/settings/radarr/')
@login_required
def settingsradarr():
    return render_template('settingsradarr.html')


@app.route('/settings/subtitles/')
@login_required
def settingssubtitles():
    return render_template('settingssubtitles.html', os=sys.platform)


@app.route('/settings/languages/')
@login_required
def settingslanguages():
    return render_template('settingslanguages.html')


@app.route('/settings/providers/')
@login_required
def settingsproviders():
    return render_template('settingsproviders.html')


@app.route('/settings/notifications/')
@login_required
def settingsnotifications():
    return render_template('settingsnotifications.html')


@app.route('/settings/scheduler/')
@login_required
def settingsscheduler():
    days_of_the_week = list(enumerate(calendar.day_name))
    return render_template('settingsscheduler.html', days=days_of_the_week)


@app.route('/check_update')
@login_required
def check_update():
    if not args.no_update:
        check_and_apply_update()

    return '', 200


@app.route('/system/tasks')
@login_required
def systemtasks():
    return render_template('systemtasks.html')


@app.route('/system/logs')
@login_required
def systemlogs():
    return render_template('systemlogs.html')


@app.route('/system/providers')
@login_required
def systemproviders():
    return render_template('systemproviders.html')


@app.route('/system/status')
@login_required
def systemstatus():
    return render_template('systemstatus.html')


@app.route('/system/releases')
@login_required
def systemreleases():
    return render_template('systemreleases.html')


def configured():
    database.execute("UPDATE system SET configured = 1")


@app.route('/api/series/wanted')
def api_wanted():
    data = database.execute("SELECT table_shows.title as seriesTitle, table_episodes.season || 'x' || "
                            "table_episodes.episode as episode_number, table_episodes.title as episodeTitle, "
                            "table_episodes.missing_subtitles FROM table_episodes INNER JOIN table_shows on "
                            "table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE "
                            "table_episodes.missing_subtitles != '[]' ORDER BY table_episodes._rowid_ DESC LIMIT 10")

    wanted_subs = []
    for item in data:
        wanted_subs.append([item['seriesTitle'], item['episode_number'], item['episodeTitle'],
                            item['missing_subtitles']])

    return dict(subtitles=wanted_subs)


@app.route('/api/series/history')
def api_history():
    data = database.execute("SELECT table_shows.title as seriesTitle, "
                            "table_episodes.season || 'x' || table_episodes.episode as episode_number, "
                            "table_episodes.title as episodeTitle, "
                            "strftime('%Y-%m-%d', datetime(table_history.timestamp, 'unixepoch')) as date, "
                            "table_history.description FROM table_history "
                            "INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId "
                            "INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = "
                            "table_history.sonarrEpisodeId WHERE table_history.action != '0' ORDER BY id DESC LIMIT 10")

    history_subs = []
    for item in data:
        history_subs.append([item['seriesTitle'], item['episode_number'], item['episodeTitle'], item['date'],
                             item['description']])

    return dict(subtitles=history_subs)


@app.route('/api/movies/wanted/')
def api_movies_wanted():
    data = database.execute("SELECT table_movies.title, table_movies.missing_subtitles FROM table_movies "
                            "WHERE table_movies.missing_subtitles != '[]' ORDER BY table_movies._rowid_ DESC LIMIT 10")

    wanted_subs = []
    for item in data:
        wanted_subs.append([item['title'], item['missing_subtitles']])

    return dict(subtitles=wanted_subs)


@app.route('/api/movies/history/')
def api_movies_history():
    data = database.execute("SELECT table_movies.title, strftime('%Y-%m-%d', "
                            "datetime(table_history_movie.timestamp, 'unixepoch')) as date, "
                            "table_history_movie.description FROM table_history_movie "
                            "INNER JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId "
                            "WHERE table_history_movie.action != '0' ORDER BY id DESC LIMIT 10")

    history_subs = []
    for item in data:
        history_subs.append([item['title'], item['date'], item['description']])

    return dict(subtitles=history_subs)


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
    apobj = apprise.Apprise()
    apobj.add(protocol + "://" + provider)

    apobj.notify(
        title='Bazarr test notification',
        body='Test notification'
    )

    return '', 200


class Server():
    def __init__(self):
        # Mute DeprecationWarning
        warnings.simplefilter("ignore", DeprecationWarning)
        # Mute Insecure HTTPS requests made to Sonarr and Radarr
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        # Mute Python3 BrokenPipeError
        warnings.simplefilter("ignore", BrokenPipeError)

        if args.dev:
            self.server = app.run(
                host=str(settings.general.ip),
                port=(int(args.port) if args.port else int(settings.general.port)))
        else:
            self.server = create_server(app,
                                        host=str(settings.general.ip),
                                        port=int(args.port) if args.port else int(settings.general.port),
                                        threads=24)

    def start(self):
        try:
            logging.info(
                'BAZARR is started and waiting for request on http://' + str(settings.general.ip) + ':' + (str(
                    args.port) if args.port else str(settings.general.port)) + str(base_url))
            if not args.dev:
                self.server.run()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        try:
            self.server.close()
        except:
            logging.error('BAZARR Cannot stop Waitress.')
        else:
            database.close()
            try:
                stop_file = io.open(os.path.join(args.config_dir, "bazarr.stop"), "w", encoding='UTF-8')
            except Exception as e:
                logging.error('BAZARR Cannot create bazarr.stop file.')
            else:
                logging.info('Bazarr is being shutdown...')
                stop_file.write(str(''))
                stop_file.close()
                os._exit(0)

    def restart(self):
        try:
            self.server.close()
        except:
            logging.error('BAZARR Cannot stop Waitress.')
        else:
            database.close()
            try:
                restart_file = io.open(os.path.join(args.config_dir, "bazarr.restart"), "w", encoding='UTF-8')
            except Exception as e:
                logging.error('BAZARR Cannot create bazarr.restart file.')
            else:
                logging.info('Bazarr is being restarted...')
                restart_file.write(str(''))
                restart_file.close()
                os._exit(0)


webserver = Server()


if __name__ == "__main__":
    webserver.start()
