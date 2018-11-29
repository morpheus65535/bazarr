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
from get_settings import path_replace_reverse, path_replace, path_replace_reverse_movie, path_replace_movie, \
    get_general_settings
from get_languages import alpha2_from_alpha3

gc.enable()


def store_subtitles(file):
    # languages = []
    actual_subtitles = []
    if os.path.exists(file):
        if os.path.splitext(file)[1] == '.mkv':
            try:
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)

                for subtitle_track in mkv.subtitle_tracks:
                    try:
                        if alpha2_from_alpha3(subtitle_track.language) != None:
                            actual_subtitles.append([str(alpha2_from_alpha3(subtitle_track.language)), None])
                    except:
                        pass
            except:
                pass

        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        try:
            # fixme: set subliminal_patch.core.CUSTOM_PATHS to a list of absolute folders or subfolders to support
            #   subtitles outside the media file folder
            subtitles = search_external_subtitles(file)
        except:
            pass
        else:
            for subtitle, language in subtitles.iteritems():
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)) is True:
                    actual_subtitles.append(
                        [str("pb"), path_replace_reverse(os.path.join(os.path.dirname(file), subtitle))])
                elif str(language) != 'und':
                    actual_subtitles.append(
                        [str(language), path_replace_reverse(os.path.join(os.path.dirname(file), subtitle))])
                else:
                    with open(path_replace(os.path.join(os.path.dirname(file), subtitle)), 'r') as f:
                        text = list(islice(f, 100))
                        text = ' '.join(text)
                        encoding = UnicodeDammit(text)
                        try:
                            text = text.decode(encoding.original_encoding)
                            detected_language = langdetect.detect(text)
                        except Exception as e:
                            logging.exception(
                                'BAZARR Error trying to detect character encoding for this subtitles file: ' + path_replace(
                                    os.path.join(os.path.dirname(file),
                                                 subtitle)) + ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                        else:
                            if len(detected_language) > 0:
                                actual_subtitles.append([str(detected_language), path_replace_reverse(
                                    os.path.join(os.path.dirname(file), subtitle))])

            conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c_db = conn_db.cursor()

            c_db.execute("UPDATE table_episodes SET subtitles = ? WHERE path = ?",
                         (str(actual_subtitles), path_replace_reverse(file)))
            conn_db.commit()

            c_db.close()

    return actual_subtitles


def store_subtitles_movie(file):
    # languages = []
    actual_subtitles = []
    if os.path.exists(file):
        if os.path.splitext(file)[1] == '.mkv':
            try:
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)

                for subtitle_track in mkv.subtitle_tracks:
                    try:
                        if alpha2_from_alpha3(subtitle_track.language) != None:
                            actual_subtitles.append([str(alpha2_from_alpha3(subtitle_track.language)), None])
                    except:
                        pass
            except:
                pass

        # fixme: set subliminal_patch.core.CUSTOM_PATHS to a list of absolute folders or subfolders to support
        #   subtitles outside the media file folder
        subtitles = search_external_subtitles(file)
        brazilian_portuguese = [".pt-br", ".pob", "pb"]

        for subtitle, language in subtitles.iteritems():
            if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)) is True:
                actual_subtitles.append(
                    [str("pb"), path_replace_reverse_movie(os.path.join(os.path.dirname(file), subtitle))])
            elif str(language) != 'und':
                actual_subtitles.append(
                    [str(language), path_replace_reverse_movie(os.path.join(os.path.dirname(file), subtitle))])
            else:
                if os.path.splitext(subtitle)[1] != ".sub":
                    with open(path_replace_movie(os.path.join(os.path.dirname(file), subtitle)), 'r') as f:
                        text = list(islice(f, 100))
                        text = ' '.join(text)
                        encoding = UnicodeDammit(text)
                        try:
                            text = text.decode(encoding.original_encoding)
                            detected_language = langdetect.detect(text)
                        except Exception as e:
                            logging.exception(
                                'BAZARR Error trying to detect character encoding for this subtitles file: ' + path_replace_movie(
                                    os.path.join(os.path.dirname(file),
                                                 subtitle)) + ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                        else:
                            if len(detected_language) > 0:
                                actual_subtitles.append([str(detected_language), path_replace_reverse_movie(
                                    os.path.join(os.path.dirname(file), subtitle))])

        conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
        c_db = conn_db.cursor()

        c_db.execute("UPDATE table_movies SET subtitles = ? WHERE path = ?",
                     (str(actual_subtitles), path_replace_reverse_movie(file)))
        conn_db.commit()

        c_db.close()

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
    use_embedded_subs = get_general_settings()[23]
    for episode_subtitles in episodes_subtitles:
        actual_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if episode_subtitles[1] != None:
            if use_embedded_subs is True:
                actual_subtitles = ast.literal_eval(episode_subtitles[1])
            else:
                actual_subtitles_temp = ast.literal_eval(episode_subtitles[1])
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] != None:
                        actual_subtitles.append(subtitle)
        if episode_subtitles[2] != None:
            desired_subtitles = ast.literal_eval(episode_subtitles[2])
        actual_subtitles_list = []
        if desired_subtitles == None:
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
    use_embedded_subs = get_general_settings()[23]
    for movie_subtitles in movies_subtitles:
        actual_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if movie_subtitles[1] != None:
            if use_embedded_subs is True:
                actual_subtitles = ast.literal_eval(movie_subtitles[1])
            else:
                actual_subtitles_temp = ast.literal_eval(movie_subtitles[1])
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] != None:
                        actual_subtitles.append(subtitle)
        if movie_subtitles[2] != None:
            desired_subtitles = ast.literal_eval(movie_subtitles[2])
        actual_subtitles_list = []
        if desired_subtitles == None:
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
