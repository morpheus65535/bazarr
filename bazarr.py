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

from get_series import *
from get_episodes import *
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

@route('/update_series')
def update_series_list():
    update_series()

    redirect('/')

@route('/update_all_episodes')
def update_all_episodes_list():
    update_all_episodes()

    redirect('/')

@route('/episodes/<no:int>', method='GET')
def episodes(no):
    conn = sqlite3.connect('bazarr.db')
    conn.create_function("path_substitution", 1, path_replace)
    c = conn.cursor()

    series_details = []
    series_details = c.execute("SELECT title, overview, poster, fanart, hearing_impaired FROM table_shows WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchone()

    episodes = c.execute("SELECT title, path_substitution(path), season, episode, subtitles, sonarrSeriesId, missing_subtitles, sonarrEpisodeId FROM table_episodes WHERE sonarrSeriesId LIKE ?", (str(no),)).fetchall()
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
    
    c.execute("SELECT COUNT(*) FROM table_history")
    row_count = c.fetchone()
    row_count = row_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = (row_count / 15) + 1

    c.execute("SELECT table_history.action, table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_history.timestamp, table_history.description, table_history.sonarrSeriesId FROM table_history INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId ORDER BY id DESC LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    data = reversed(sorted(data, key=operator.itemgetter(4)))
    c.close()
    return template('history', rows=data, row_count=row_count, page=page, max_page=max_page)

@route('/wanted')
def wanted():
    db = sqlite3.connect('bazarr.db')
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'")
    missing_count = c.fetchone()
    missing_count = missing_count[0]
    page = request.GET.page
    if page == "":
        page = "1"
    offset = (int(page) - 1) * 15
    max_page = (missing_count / 15) + 1

    c.execute("SELECT table_shows.title, table_episodes.season || 'x' || table_episodes.episode, table_episodes.title, table_episodes.missing_subtitles, table_episodes.sonarrSeriesId, path_substitution(table_episodes.path), table_shows.hearing_impaired, table_episodes.sonarrEpisodeId FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.missing_subtitles != '[]' LIMIT 15 OFFSET ?", (offset,))
    data = c.fetchall()
    c.close()
    return template('wanted', rows=data, missing_count=missing_count, page=page, max_page=max_page)

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
    conn = sqlite3.connect('bazarr.db')
    c = conn.cursor()    

    settings_general_ip = request.forms.get('settings_general_ip')
    settings_general_port = request.forms.get('settings_general_port')
    settings_general_baseurl = request.forms.get('settings_general_baseurl')
    settings_general_sourcepath = request.forms.getall('settings_general_sourcepath')
    settings_general_destpath = request.forms.getall('settings_general_destpath')
    settings_general_pathmapping = []
    settings_general_pathmapping.extend([list(a) for a in zip(settings_general_sourcepath, settings_general_destpath)])
    c.execute("UPDATE table_settings_general SET ip = ?, port = ?, base_url = ?, path_mapping = ?", (settings_general_ip, settings_general_port, settings_general_baseurl, str(settings_general_pathmapping)))
    
    settings_sonarr_ip = request.forms.get('settings_sonarr_ip')
    settings_sonarr_port = request.forms.get('settings_sonarr_port')
    settings_sonarr_baseurl = request.forms.get('settings_sonarr_baseurl')
    settings_sonarr_ssl = request.forms.get('settings_sonarr_ssl')
    if settings_sonarr_ssl is None:
        settings_sonarr_ssl = 'False'
    else:
        settings_sonarr_ssl = 'True'
    settings_sonarr_apikey = request.forms.get('settings_sonarr_apikey')
    c.execute("UPDATE table_settings_sonarr SET ip = ?, port = ?, base_url = ?, ssl = ?, apikey = ?", (settings_sonarr_ip, settings_sonarr_port, settings_sonarr_baseurl, settings_sonarr_ssl, settings_sonarr_apikey))
    
    settings_subliminal_providers = request.forms.getall('settings_subliminal_providers')
    c.execute("UPDATE table_settings_providers SET enabled = 0")
    for item in settings_subliminal_providers:
        c.execute("UPDATE table_settings_providers SET enabled = '1' WHERE name = ?", (item,))
    settings_subliminal_languages = request.forms.getall('settings_subliminal_languages')
    c.execute("UPDATE table_settings_languages SET enabled = 0")
    for item in settings_subliminal_languages:
        c.execute("UPDATE table_settings_languages SET enabled = '1' WHERE code2 = ?", (item,))
    
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
        list_missing_subtitles()
        redirect('/episodes/' + sonarrSeriesId)

@route('/get_subtitle', method='GET')
def get_subtitle():
        ref = request.environ['HTTP_REFERER']

        episodePath = request.GET.episodePath
        language = request.GET.language
        hi = request.GET.hi
        sonarrSeriesId = request.GET.sonarrSeriesId
        sonarrEpisodeId = request.GET.sonarrEpisodeId

        db = sqlite3.connect('bazarr.db')
        c = db.cursor()
        c.execute("SELECT name FROM table_settings_providers WHERE enabled = 1")
        providers = c.fetchall()
        c.close()

        providers_list = []
        for provider in providers:
            providers_list.append(provider[0])
        
        try:
            result = download_subtitle(episodePath, language, hi, providers_list)
            if result is not None:
                history_log(1, sonarrSeriesId, sonarrEpisodeId, result)
                store_subtitles(episodePath)
                list_missing_subtitles()
            redirect(ref)
        except OSError:
            redirect(ref + '?error=2')

run(host=ip, port=port, server='waitress')
