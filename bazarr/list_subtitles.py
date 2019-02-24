# coding=utf-8

import gc
import os
import enzyme
import babelfish
import logging
import sqlite3
import ast
import langdetect
import subliminal
import subliminal_patch
from subliminal import core
from subliminal_patch import search_external_subtitles
from bs4 import UnicodeDammit
from itertools import islice

from get_args import args
from get_languages import alpha2_from_alpha3
from config import settings
from helper import path_replace, path_replace_movie, path_replace_reverse, \
    path_replace_reverse_movie, get_subtitle_destination_folder

from queueconfig import notifications

gc.enable()


def store_subtitles(file):
    logging.debug('BAZARR started subtitles indexing for this file: ' + file)
    actual_subtitles = []
    if os.path.exists(file):
        notifications.write(msg='Analyzing this file for subtitles: ' + file, queue='list_subtitles')
        if os.path.splitext(file)[1] == '.mkv':
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)
                
                for subtitle_track in mkv.subtitle_tracks:
                    try:
                        if alpha2_from_alpha3(subtitle_track.language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_track.language))
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_track.language)
                        pass
            except Exception as e:
                logging.exception("BAZARR error when trying to analyze this mkv file: " + file)
                pass
        else:
            logging.debug("BAZARR This file isn't an .mkv file.")
        
        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        try:
            dest_folder = get_subtitle_destination_folder()
            subliminal_patch.core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
            subtitles = search_external_subtitles(file)
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in subtitles.iteritems():
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)):
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append(
                        [str("pb"), path_replace_reverse(os.path.join(os.path.dirname(file), subtitle))])
                elif str(language) != 'und':
                    logging.debug("BAZARR external subtitles detected: " + str(language))
                    actual_subtitles.append(
                        [str(language), path_replace_reverse(os.path.join(os.path.dirname(file), subtitle))])
                else:
                    if os.path.splitext(subtitle)[1] != ".sub":
                        logging.debug("BAZARR falling back to file content analysis to detect language.")
                        with open(path_replace(os.path.join(os.path.dirname(file), subtitle)), 'r') as f:
                            text = list(islice(f, 100))
                            text = ' '.join(text)
                            encoding = UnicodeDammit(text)
                            try:
                                text = text.decode(encoding.original_encoding)
                                detected_language = langdetect.detect(text)
                            except Exception as e:
                                logging.exception(
                                    'BAZARR Error trying to detect language for this subtitles file: ' + path_replace(
                                        os.path.join(os.path.dirname(file),
                                                     subtitle)) + ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                            else:
                                if len(detected_language) > 0:
                                    logging.debug(
                                        "BAZARR external subtitles detected and analysis guessed this language: " + str(
                                            detected_language))
                                    actual_subtitles.append([str(detected_language), path_replace_reverse(
                                        os.path.join(os.path.dirname(file), subtitle))])
        
        conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
        c_db = conn_db.cursor()
        logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
        c_db.execute("UPDATE table_episodes SET subtitles = ? WHERE path = ?",
                     (str(actual_subtitles), path_replace_reverse(file)))
        conn_db.commit()
        
        c_db.close()
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + file)
    
    return actual_subtitles


def store_subtitles_movie(file):
    logging.debug('BAZARR started subtitles indexing for this file: ' + file)
    actual_subtitles = []
    if os.path.exists(file):
        notifications.write(msg='Analyzing this file for subtitles: ' + file, queue='list_subtitles')
        if os.path.splitext(file)[1] == '.mkv':
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)
                
                for subtitle_track in mkv.subtitle_tracks:
                    try:
                        if alpha2_from_alpha3(subtitle_track.language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_track.language))
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_track.language)
                        pass
            except Exception as e:
                logging.exception("BAZARR error when trying to analyze this mkv file: " + file)
                pass
        else:
            logging.debug("BAZARR This file isn't an .mkv file.")

        dest_folder = get_subtitle_destination_folder()
        subliminal_patch.core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
        subtitles = search_external_subtitles(file)
        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        try:
            subtitles = core.search_external_subtitles(file)
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in subtitles.iteritems():
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)) is True:
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append(
                        [str("pb"), path_replace_reverse_movie(os.path.join(os.path.dirname(file), subtitle))])
                elif str(language) != 'und':
                    logging.debug("BAZARR external subtitles detected: " + str(language))
                    actual_subtitles.append(
                        [str(language), path_replace_reverse_movie(os.path.join(os.path.dirname(file), subtitle))])
                else:
                    if os.path.splitext(subtitle)[1] != ".sub":
                        logging.debug("BAZARR falling back to file content analysis to detect language.")
                        with open(path_replace_movie(os.path.join(os.path.dirname(file), subtitle)), 'r') as f:
                            text = list(islice(f, 100))
                            text = ' '.join(text)
                            encoding = UnicodeDammit(text)
                            try:
                                text = text.decode(encoding.original_encoding)
                                detected_language = langdetect.detect(text)
                            except Exception as e:
                                logging.exception(
                                    'BAZARR Error trying to detect language for this subtitles file: ' + path_replace(
                                        os.path.join(os.path.dirname(file),
                                                     subtitle)) + ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                            else:
                                if len(detected_language) > 0:
                                    logging.debug(
                                        "BAZARR external subtitles detected and analysis guessed this language: " + str(
                                            detected_language))
                                    actual_subtitles.append([str(detected_language), path_replace_reverse_movie(
                                        os.path.join(os.path.dirname(file), subtitle))])
        
        conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
        c_db = conn_db.cursor()
        logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
        c_db.execute("UPDATE table_movies SET subtitles = ? WHERE path = ?",
                     (str(actual_subtitles), path_replace_reverse_movie(file)))
        conn_db.commit()
        
        c_db.close()
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + file)
    
    return actual_subtitles


def list_missing_subtitles(*no):
    query_string = ''
    try:
        query_string = " WHERE table_shows.sonarrSeriesId = " + str(no[0])
    except:
        pass
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_subtitles = c_db.execute(
        "SELECT table_episodes.sonarrEpisodeId, table_episodes.subtitles, table_shows.languages FROM table_episodes INNER JOIN table_shows on table_episodes.sonarrSeriesId = table_shows.sonarrSeriesId" + query_string).fetchall()
    c_db.close()
    
    missing_subtitles_global = []
    use_embedded_subs = settings.general.getboolean('use_embedded_subs')
    for episode_subtitles in episodes_subtitles:
        actual_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if episode_subtitles[1] is not None:
            if use_embedded_subs:
                actual_subtitles = ast.literal_eval(episode_subtitles[1])
            else:
                actual_subtitles_temp = ast.literal_eval(episode_subtitles[1])
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] is not None:
                        actual_subtitles.append(subtitle)
        if episode_subtitles[2] is not None:
            desired_subtitles = ast.literal_eval(episode_subtitles[2])
        actual_subtitles_list = []
        if desired_subtitles is None:
            missing_subtitles_global.append(tuple(['[]', episode_subtitles[0]]))
        else:
            for item in actual_subtitles:
                if item[0] == "pt-BR":
                    actual_subtitles_list.append("pb")
                else:
                    actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            missing_subtitles_global.append(tuple([str(missing_subtitles), episode_subtitles[0]]))
    
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    c_db.executemany("UPDATE table_episodes SET missing_subtitles = ? WHERE sonarrEpisodeId = ?",
                     (missing_subtitles_global))
    conn_db.commit()
    c_db.close()


def list_missing_subtitles_movies(*no):
    query_string = ''
    try:
        query_string = " WHERE table_movies.radarrId = " + str(no[0])
    except:
        pass
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movies_subtitles = c_db.execute("SELECT radarrId, subtitles, languages FROM table_movies" + query_string).fetchall()
    c_db.close()
    
    missing_subtitles_global = []
    use_embedded_subs = settings.general.getboolean('use_embedded_subs')
    for movie_subtitles in movies_subtitles:
        actual_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if movie_subtitles[1] is not None:
            if use_embedded_subs:
                actual_subtitles = ast.literal_eval(movie_subtitles[1])
            else:
                actual_subtitles_temp = ast.literal_eval(movie_subtitles[1])
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] is not None:
                        actual_subtitles.append(subtitle)
        if movie_subtitles[2] is not None:
            desired_subtitles = ast.literal_eval(movie_subtitles[2])
        actual_subtitles_list = []
        if desired_subtitles is None:
            missing_subtitles_global.append(tuple(['[]', movie_subtitles[0]]))
        else:
            for item in actual_subtitles:
                if item[0] == "pt-BR":
                    actual_subtitles_list.append("pb")
                else:
                    actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            missing_subtitles_global.append(tuple([str(missing_subtitles), movie_subtitles[0]]))
    
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    c_db.executemany("UPDATE table_movies SET missing_subtitles = ? WHERE radarrId = ?", (missing_subtitles_global))
    conn_db.commit()
    c_db.close()


def series_full_scan_subtitles():
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes = c_db.execute("SELECT path FROM table_episodes").fetchall()
    c_db.close()
    
    for episode in episodes:
        store_subtitles(path_replace(episode[0]))
    
    gc.collect()


def movies_full_scan_subtitles():
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movies = c_db.execute("SELECT path FROM table_movies").fetchall()
    c_db.close()
    
    for movie in movies:
        store_subtitles_movie(path_replace_movie(movie[0]))
    
    gc.collect()


def series_scan_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes = c_db.execute("SELECT path FROM table_episodes WHERE sonarrSeriesId = ?", (no,)).fetchall()
    c_db.close()
    
    for episode in episodes:
        store_subtitles(path_replace(episode[0]))
    
    list_missing_subtitles(no)


def movies_scan_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movies = c_db.execute("SELECT path FROM table_movies WHERE radarrId = ?", (no,)).fetchall()
    c_db.close()
    
    for movie in movies:
        store_subtitles_movie(path_replace_movie(movie[0]))
    
    list_missing_subtitles_movies(no)
