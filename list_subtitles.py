import os
import enzyme
import babelfish
from subliminal import *
import pycountry
import sqlite3
import ast
import langdetect
from bs4 import UnicodeDammit
from itertools import islice

from get_general_settings import *

def store_subtitles(file):
    languages = []
    actual_subtitles = []
    if os.path.exists(file):
        if os.path.splitext(file)[1] == '.mkv':
            try:
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)
                
                for subtitle_track in mkv.subtitle_tracks:
                    try:
                        actual_subtitles.append([str(pycountry.languages.lookup(subtitle_track.language).alpha_2),None])
                    except:
                        pass
            except:
                pass


        subtitles = core.search_external_subtitles(file)
        
        for subtitle, language in subtitles.iteritems():
            if str(language) != 'und':
                actual_subtitles.append([str(language), path_replace_reverse(os.path.join(os.path.dirname(file), subtitle))])
            else:
                with open(path_replace(os.path.join(os.path.dirname(file), subtitle)), 'r') as f:
                    text = list(islice(f, 20))
                    text = ' '.join(text)
                    encoding = UnicodeDammit(text)
                    try:
                        text = text.decode(encoding.original_encoding)
                    except Exception as e:
                        logging.exception('Error trying to detect character encoding for this subtitles file: ' + path_replace(os.path.join(os.path.dirname(file), subtitle)) + ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                    else:
                        detected_language = langdetect.detect(text)
                        if len(detected_language) > 0:
                            actual_subtitles.append([str(detected_language), path_replace_reverse(os.path.join(os.path.dirname(file), subtitle))])
        
        conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
        c_db = conn_db.cursor()
        
        c_db.execute("UPDATE table_episodes SET subtitles = ? WHERE path = ?", (str(actual_subtitles), path_replace_reverse(file)))
        conn_db.commit()

        c_db.close()

    return actual_subtitles
    
def list_missing_subtitles(*no):
    query_string = ''
    try:
        query_string = " WHERE table_shows.sonarrSeriesId = " + str(no[0])
    except:
        pass
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_subtitles = c_db.execute("SELECT table_episodes.sonarrEpisodeId, table_episodes.subtitles, table_shows.languages FROM table_episodes INNER JOIN table_shows on table_episodes.sonarrSeriesId = table_shows.sonarrSeriesId" + query_string).fetchall()
    c_db.close()

    missing_subtitles_global = []

    for episode_subtitles in episodes_subtitles:
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if episode_subtitles[1] != None:
            actual_subtitles = ast.literal_eval(episode_subtitles[1])
        if episode_subtitles[2] != None:
            desired_subtitles = ast.literal_eval(episode_subtitles[2])
        actual_subtitles_list = []
        if desired_subtitles == None:
            missing_subtitles_global.append(tuple(['[]', episode_subtitles[0]]))
        else:
            for item in actual_subtitles:
                actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            missing_subtitles_global.append(tuple([str(missing_subtitles), episode_subtitles[0]]))
            
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    c_db.executemany("UPDATE table_episodes SET missing_subtitles = ? WHERE sonarrEpisodeId = ?", (missing_subtitles_global))
    conn_db.commit()
    c_db.close()

def full_scan_subtitles():
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes = c_db.execute("SELECT path FROM table_episodes").fetchall()
    c_db.close()

    for episode in episodes:
        store_subtitles(path_replace(episode[0]))

def series_scan_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes = c_db.execute("SELECT path FROM table_episodes WHERE sonarrSeriesId = ?", (no,)).fetchall()
    c_db.close()
    
    for episode in episodes:
        store_subtitles(path_replace(episode[0]))

    list_missing_subtitles(no)

def new_scan_subtitles():
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes = c_db.execute("SELECT path FROM table_episodes WHERE subtitles is null").fetchall()
    c_db.close()

    for episode in episodes:
        store_subtitles(path_replace(episode[0]))
