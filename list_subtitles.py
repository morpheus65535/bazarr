import os
import enzyme
import babelfish
import pycountry
import sqlite3
import ast

from get_general_settings import *

def store_subtitles(file):
    languages = []
    if os.path.exists(file):
        if os.path.splitext(file)[1] == '.mkv':
            try:
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)
                
                for subtitle_track in mkv.subtitle_tracks:
                    try:
                        languages.append([str(pycountry.languages.lookup(subtitle_track.language).alpha_2),None])
                    except:
                        pass
            except:
                pass

        conn_db = sqlite3.connect('bazarr.db')
        c_db = conn_db.cursor()
        enabled_languages = c_db.execute("SELECT code2 FROM table_settings_languages WHERE enabled = 1").fetchall()
        
        for language in enabled_languages:
            subtitle_path = os.path.splitext(file)[0] + "." + str(language[0]) + ".srt"
            if os.path.isfile(subtitle_path):
                languages.append([str(language[0]),str(path_replace_reverse(subtitle_path))])
        try:
            c_db.execute("UPDATE table_episodes SET subtitles = ? WHERE path = ?", (str(languages), path_replace_reverse(file)))
            conn_db.commit()
        except:
            pass
        c_db.close()

    return languages
    
def list_missing_subtitles(file):
    conn_db = sqlite3.connect('bazarr.db')
    c_db = conn_db.cursor()
    actual_subtitles_long = c_db.execute("SELECT sonarrSeriesId, subtitles FROM table_episodes WHERE path = ?", (file,)).fetchone()
    desired_subtitles = c_db.execute("SELECT languages FROM table_shows WHERE sonarrSeriesId = ?", (actual_subtitles_long[0],)).fetchone()
    c_db.close()
    missing_subtitles = []
    actual_subtitles = []
    if desired_subtitles[0] == "None":
        pass
    else:
        actual_subtitles_long = ast.literal_eval(actual_subtitles_long[1])
        for actual_subtitle in actual_subtitles_long:
            actual_subtitles.append(actual_subtitle[0])

        desired_subtitles = ast.literal_eval(desired_subtitles[0])
        
        missing_subtitles = (list(set(desired_subtitles) - set(actual_subtitles)))
    return str(missing_subtitles)

def full_scan_subtitles():
    conn_db = sqlite3.connect('bazarr.db')
    c_db = conn_db.cursor()
    all_path = c_db.execute("SELECT path FROM table_episodes").fetchall()
    c_db.close()

    for path in all_path:
        print store_subtitles(path_replace(path[0]))

#print list_missing_subtitles('/tv/Fear the Walking Dead/Season 3/Fear.The.Walking.Dead.S03E01.CONVERT.720p.WEB.h264-TBS[rarbg].mkv')
#full_scan_subtitles()
