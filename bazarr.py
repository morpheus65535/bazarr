from bottle import route, run, template, static_file, request, redirect
import bottle
bottle.debug(True)
bottle.TEMPLATES.clear()

import sqlite3
import itertools
import operator
import requests
import pycountry
from PIL import Image
from io import BytesIO
from fdsend import send_file
import urllib

from init_db import *
from get_languages import *
from get_providers import *

from get_general_settings import *
from get_sonarr_settings import *
from list_subtitles import *
from get_subtitle import *
from utils import *

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

@route('/image_proxy/<url:path>', method='GET')
def image_proxy(url):
    img_pil = Image.open(BytesIO(requests.get(url_sonarr_short + '/' + url).content))
    img_buffer = BytesIO()
    img_pil.tobytes()
    img_pil.save(img_buffer, img_pil.format)
    img_buffer.seek(0)
    return send_file(img_buffer, ctype=img_pil.format)

@route('/')
def series():
    db = sqlite3.connect('bazarr.db')
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()
    c.execute("SELECT tvdbId, title, path_substitution(path), languages, hearing_impaired, sonarrSeriesId, poster FROM table_shows ORDER BY title")
    data = c.fetchall()
    c.execute("SELECT code2, name FROM table_settings_languages WHERE enabled = 1")
    languages = c.fetchall()
    c.close()
    output = template('series', rows=data, languages=languages, url_sonarr_short=url_sonarr_short)
    return output

@route('/edit_series/<no:int>', method='POST')
def edit_series(no):
    lang = request.forms.getall('languages')
    if len(lang) > 0:
        if lang[0] == '':
            lang = None
        else:
            pass
    else:
        lang = None
    hi = request.forms.get('hearing_impaired')

    if hi == "on":
        hi = "True"
    else:
        hi = "False"

    conn = sqlite3.connect('bazarr.db')
    c = conn.cursor()
    c.execute("UPDATE table_shows SET languages = ?, hearing_impaired = ? WHERE tvdbId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    redirect('/')

@route('/episodes/<no:int>', method='GET')
def episodes(no):
    conn = sqlite3.connect('bazarr.db')
    conn.create_function("path_substitution", 1, path_replace)
    conn.create_function("missing_subtitles", 1, list_missing_subtitles)
    c = conn.cursor()

    series_details = []
    series_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired FROM table_shows WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchone()

    sqlite3.enable_callback_tracebacks(True)
    episodes = c.execute("SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles(path), sonarrEpisodeId FROM table_episodes WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchall()
    episodes = reversed(sorted(episodes, key=operator.itemgetter(2)))
    seasons_list = []
    for key,season in itertools.groupby(episodes,operator.itemgetter(2)):
        seasons_list.append(list(season))
    c.close()
    
    return template('episodes', details=series_details, seasons=seasons_list, url_sonarr_short=url_sonarr_short)

@route('/history')
def history():
    db = sqlite3.connect('bazarr.db')
    c = db.cursor()
    c.execute("SELECT table_history.action, table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_history.timestamp, table_history.description, table_history.sonarrSeriesId FROM table_history INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId ORDER BY id DESC LIMIT 15")
    data = c.fetchall()
    data = reversed(sorted(data, key=operator.itemgetter(4)))
    c.close()
    return template('history', rows=data)

@route('/settings')
def settings():
    db = sqlite3.connect('bazarr.db')
    c = db.cursor()
    c.execute("SELECT * FROM table_settings_general")
    settings_general = c.fetchone()
    c.execute("SELECT * FROM table_settings_languages ORDER BY name")
    settings_languages = c.fetchall()
    c.execute("SELECT * FROM table_settings_providers ORDER BY name")
    settings_providers = c.fetchall()
    c.execute("SELECT * FROM table_settings_sonarr")
    settings_sonarr = c.fetchone()
    c.close()
    return template('settings', settings_general=settings_general, settings_languages=settings_languages, settings_providers=settings_providers, settings_sonarr=settings_sonarr)

@route('/save_settings', method='POST')
def save_settings():
    lang = request.forms.getall('languages')
    if len(lang) > 0:
        if lang[0] == '':
            lang = None
        else:
            pass
    else:
        lang = None
    hi = request.forms.get('hearing_impaired')

    if hi == "on":
        hi = "True"
    else:
        hi = "False"

    conn = sqlite3.connect('bazarr.db')
    c = conn.cursor()
    c.execute("UPDATE table_shows SET languages = ?, hearing_impaired = ? WHERE tvdbId LIKE ?", (str(lang), hi, no))
    conn.commit()
    c.close()

    redirect('/settings')

@route('/system')
def system():
    db = sqlite3.connect('bazarr.db')
    c = db.cursor()
    c.execute("SELECT * FROM table_scheduler")
    data = c.fetchall()
    c.close()
    return template('system', rows=data)

@route('/remove_subtitles', method='GET')
def remove_subtitles():
        episodePath = request.GET.episodePath
        language = request.GET.language
        subtitlesPath = request.GET.subtitlesPath
        sonarrSeriesId = request.GET.sonarrSeriesId
        sonarrEpisodeId = request.GET.sonarrEpisodeId

        try:
            os.remove(subtitlesPath)
            result = pycountry.languages.lookup(language).name + " subtitles deleted from disk."
            history_log(0, sonarrSeriesId, sonarrEpisodeId, result)
        except OSError:
            pass
        store_subtitles(episodePath)
        redirect('/episodes/' + sonarrSeriesId)

@route('/get_subtitle', method='GET')
def get_subtitle():
        episodePath = request.GET.episodePath
        language = request.GET.language
        hi = request.GET.hi
        sonarrSeriesId = request.GET.sonarrSeriesId
        sonarrEpisodeId = request.GET.sonarrEpisodeId
        
        try:
            result = download_subtitle(episodePath, language, hi, None)
            history_log(1, sonarrSeriesId, sonarrEpisodeId, result)
            store_subtitles(episodePath)
            redirect('/episodes/' + sonarrSeriesId)
        except OSError:
            redirect('/episodes/' + sonarrSeriesId + '?error=2')

run(host=ip, port=port)
