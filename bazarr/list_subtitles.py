# coding=utf-8

from __future__ import absolute_import
import gc
import os
import babelfish
import logging
import ast
import langdetect
import subliminal
import subliminal_patch
import operator
from subliminal import core
from subliminal_patch import search_external_subtitles
from bs4 import UnicodeDammit
from itertools import islice
from database import TableShows, TableEpisodes, TableMovies
from peewee import fn, JOIN

from get_args import args
from get_languages import alpha2_from_alpha3, get_language_set
from config import settings
from helper import path_replace, path_replace_movie, path_replace_reverse, \
    path_replace_reverse_movie, get_subtitle_destination_folder

from queueconfig import notifications
from embedded_subs_reader import embedded_subs_reader
import six

gc.enable()


def store_subtitles(file):
    logging.debug('BAZARR started subtitles indexing for this file: ' + file)
    actual_subtitles = []
    if os.path.exists(file):
        if settings.general.getboolean('use_embedded_subs'):
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader.list_languages(file)
                for subtitle_language, subtitle_forced in subtitle_languages:
                    try:
                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_language))
                            if subtitle_forced:
                                lang = lang + ":forced"
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_language)
                        pass
            except Exception as e:
                logging.exception(
                    "BAZARR error when trying to analyze this %s file: %s" % (os.path.splitext(file)[1], file))
                pass
        
        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        brazilian_portuguese_forced = [".pt-br.forced", ".pob.forced", "pb.forced"]
        try:
            dest_folder = get_subtitle_destination_folder()
            subliminal_patch.core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
            subtitles = search_external_subtitles(file, languages=get_language_set(),
                                                  only_one=settings.general.getboolean('single_language'))
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in six.iteritems(subtitles):
                subtitle_path = get_external_subtitles_path(file, subtitle)
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)):
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append(
                        [str("pb"), path_replace_reverse(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese_forced)):
                    logging.debug("BAZARR external subtitles detected: " + "pb:forced")
                    actual_subtitles.append(
                        [str("pb:forced"), path_replace_reverse(subtitle_path)])
                
                elif str(language) != 'und':
                    logging.debug("BAZARR external subtitles detected: " + str(language))
                    actual_subtitles.append(
                        [str(language), path_replace_reverse(subtitle_path)])
                else:
                    if os.path.splitext(subtitle)[1] != ".sub":
                        logging.debug("BAZARR falling back to file content analysis to detect language.")
                        with open(os.path.join(os.path.dirname(file), subtitle), 'r') as f:
                            text = list(islice(f, 100))
                            text = ' '.join(text)
                            encoding = UnicodeDammit(text)
                            try:
                                text = text.decode(encoding.original_encoding)
                                detected_language = langdetect.detect(text)
                            except Exception as e:
                                logging.exception(
                                    'BAZARR Error trying to detect language for this subtitles file: ' +
                                    os.path.join(os.path.dirname(file), subtitle) +
                                    ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                            else:
                                if len(detected_language) > 0:
                                    logging.debug(
                                        "BAZARR external subtitles detected and analysis guessed this language: " + str(
                                            detected_language))
                                    actual_subtitles.append([str(detected_language), path_replace_reverse(
                                        os.path.join(os.path.dirname(file), subtitle))])

        update_count = TableEpisodes.update(
            {
                TableEpisodes.subtitles: str(actual_subtitles)
            }
        ).where(
            TableEpisodes.path == path_replace_reverse(file)
        ).execute()
        if update_count > 0:
            logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
        else:
            logging.debug("BAZARR haven't been able to update existing subtitles to DB : " + str(actual_subtitles))
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + file)
    
    return actual_subtitles


def store_subtitles_movie(file):
    logging.debug('BAZARR started subtitles indexing for this file: ' + file)
    actual_subtitles = []
    if os.path.exists(file):
        if settings.general.getboolean('use_embedded_subs'):
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader.list_languages(file)
                for subtitle_language, subtitle_forced in subtitle_languages:
                    try:
                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_language))
                            if subtitle_forced:
                                lang = lang + ':forced'
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_language)
                        pass
            except Exception as e:
                logging.exception(
                    "BAZARR error when trying to analyze this %s file: %s" % (os.path.splitext(file)[1], file))
                pass
        
        dest_folder = get_subtitle_destination_folder() or ''
        subliminal_patch.core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        brazilian_portuguese_forced = [".pt-br.forced", ".pob.forced", "pb.forced"]
        try:
            subtitles = search_external_subtitles(file, languages=get_language_set(),
                                                  only_one=settings.general.getboolean('single_language'))
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in six.iteritems(subtitles):
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)) is True:
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append(
                        [str("pb"),
                         path_replace_reverse_movie(os.path.join(os.path.dirname(file), dest_folder, subtitle))])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese_forced)) is True:
                    logging.debug("BAZARR external subtitles detected: " + "pb:forced")
                    actual_subtitles.append(
                        [str("pb:forced"),
                         path_replace_reverse_movie(os.path.join(os.path.dirname(file), dest_folder, subtitle))])
                elif str(language) != 'und':
                    logging.debug("BAZARR external subtitles detected: " + str(language))
                    actual_subtitles.append(
                        [str(language),
                         path_replace_reverse_movie(os.path.join(os.path.dirname(file), dest_folder, subtitle))])
                else:
                    if os.path.splitext(subtitle)[1] != ".sub":
                        logging.debug("BAZARR falling back to file content analysis to detect language.")
                        with open(os.path.join(os.path.dirname(file), dest_folder, subtitle), 'r') as f:
                            text = list(islice(f, 100))
                            text = ' '.join(text)
                            encoding = UnicodeDammit(text)
                            try:
                                text = text.decode(encoding.original_encoding)
                                detected_language = langdetect.detect(text)
                            except Exception as e:
                                logging.exception(
                                    'BAZARR Error trying to detect language for this subtitles file: ' +
                                    os.path.join(os.path.dirname(file), subtitle) +
                                    ' You should try to delete this subtitles file manually and ask Bazarr to download it again.')
                            else:
                                if len(detected_language) > 0:
                                    logging.debug(
                                        "BAZARR external subtitles detected and analysis guessed this language: " + str(
                                            detected_language))
                                    actual_subtitles.append([str(detected_language), path_replace_reverse_movie(
                                        os.path.join(os.path.dirname(file), dest_folder, subtitle))])
        
        update_count = TableMovies.update(
            {
                TableMovies.subtitles: str(actual_subtitles)
            }
        ).where(
            TableMovies.path == path_replace_reverse_movie(file)
        ).execute()
        if update_count > 0:
            logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
        else:
            logging.debug("BAZARR haven't been able to update existing subtitles to DB : " + str(actual_subtitles))
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + file)
    
    return actual_subtitles


def list_missing_subtitles(no=None):
    episodes_subtitles_clause = {TableShows.sonarr_series_id.is_null(False)}
    if no is not None:
        episodes_subtitles_clause = {TableShows.sonarr_series_id ** no}

    episodes_subtitles = TableEpisodes.select(
        TableEpisodes.sonarr_episode_id,
        TableEpisodes.subtitles,
        TableShows.languages,
        TableShows.forced
    ).join_from(
        TableEpisodes, TableShows, JOIN.LEFT_OUTER
    ).where(
        episodes_subtitles_clause
    ).objects()

    missing_subtitles_global = []
    use_embedded_subs = settings.general.getboolean('use_embedded_subs')
    for episode_subtitles in episodes_subtitles:
        actual_subtitles_temp = []
        desired_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if episode_subtitles.subtitles is not None:
            if use_embedded_subs:
                actual_subtitles = ast.literal_eval(episode_subtitles.subtitles)
            else:
                actual_subtitles_temp = ast.literal_eval(episode_subtitles.subtitles)
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] is not None:
                        actual_subtitles.append(subtitle)
        if episode_subtitles.languages is not None:
            desired_subtitles = ast.literal_eval(episode_subtitles.languages)
            if episode_subtitles.forced == "True" and desired_subtitles is not None:
                for i, desired_subtitle in enumerate(desired_subtitles):
                    desired_subtitles[i] = desired_subtitle + ":forced"
            elif episode_subtitles.forced == "Both" and desired_subtitles is not None:
                for desired_subtitle in desired_subtitles:
                    desired_subtitles_temp.append(desired_subtitle)
                    desired_subtitles_temp.append(desired_subtitle + ":forced")
                desired_subtitles = desired_subtitles_temp
        actual_subtitles_list = []
        if desired_subtitles is None:
            missing_subtitles_global.append(tuple(['[]', episode_subtitles.sonarr_episode_id]))
        else:
            for item in actual_subtitles:
                if item[0] == "pt-BR":
                    actual_subtitles_list.append("pb")
                elif item[0] == "pt-BR:forced":
                    actual_subtitles_list.append("pb:forced")
                else:
                    actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            missing_subtitles_global.append(tuple([str(missing_subtitles), episode_subtitles.sonarr_episode_id]))

    for missing_subtitles_item in missing_subtitles_global:
        TableEpisodes.update(
            {
                TableEpisodes.missing_subtitles: missing_subtitles_item[0]
            }
        ).where(
            TableEpisodes.sonarr_episode_id == missing_subtitles_item[1]
        ).execute()


def list_missing_subtitles_movies(no=None):
    movies_subtitles_clause = {TableMovies.radarr_id.is_null(False)}
    if no is not None:
        movies_subtitles_clause = {TableMovies.radarr_id ** no}

    movies_subtitles = TableMovies.select(
        TableMovies.radarr_id,
        TableMovies.subtitles,
        TableMovies.languages,
        TableMovies.forced
    ).where(
        movies_subtitles_clause
    )
    
    missing_subtitles_global = []
    use_embedded_subs = settings.general.getboolean('use_embedded_subs')
    for movie_subtitles in movies_subtitles:
        actual_subtitles_temp = []
        desired_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if movie_subtitles.subtitles is not None:
            if use_embedded_subs:
                actual_subtitles = ast.literal_eval(movie_subtitles.subtitles)
            else:
                actual_subtitles_temp = ast.literal_eval(movie_subtitles.subtitles)
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] is not None:
                        actual_subtitles.append(subtitle)
        if movie_subtitles.languages is not None:
            desired_subtitles = ast.literal_eval(movie_subtitles.languages)
            if movie_subtitles.forced == "True" and desired_subtitles is not None:
                for i, desired_subtitle in enumerate(desired_subtitles):
                    desired_subtitles[i] = desired_subtitle + ":forced"
            elif movie_subtitles.forced == "Both" and desired_subtitles is not None:
                for desired_subtitle in desired_subtitles:
                    desired_subtitles_temp.append(desired_subtitle)
                    desired_subtitles_temp.append(desired_subtitle + ":forced")
                desired_subtitles = desired_subtitles_temp
        actual_subtitles_list = []
        if desired_subtitles is None:
            missing_subtitles_global.append(tuple(['[]', movie_subtitles.radarr_id]))
        else:
            for item in actual_subtitles:
                if item[0] == "pt-BR":
                    actual_subtitles_list.append("pb")
                elif item[0] == "pt-BR:forced":
                    actual_subtitles_list.append("pb:forced")
                else:
                    actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            missing_subtitles_global.append(tuple([str(missing_subtitles), movie_subtitles.radarr_id]))
    
    for missing_subtitles_item in missing_subtitles_global:
        TableMovies.update(
            {
                TableMovies.missing_subtitles: missing_subtitles_item[0]
            }
        ).where(
            TableMovies.radarr_id == missing_subtitles_item[1]
        ).execute()


def series_full_scan_subtitles():
    episodes = TableEpisodes.select(
        TableEpisodes.path
    )
    count_episodes = episodes.count()
    
    for i, episode in enumerate(episodes, 1):
        notifications.write(msg='Updating all episodes subtitles from disk...',
                            queue='list_subtitles_series', item=i, length=count_episodes)
        store_subtitles(path_replace(episode.path))
    
    gc.collect()


def movies_full_scan_subtitles():
    movies = TableMovies.select(
        TableMovies.path
    )
    count_movies = movies.count()
    
    for i, movie in enumerate(movies, 1):
        notifications.write(msg='Updating all movies subtitles from disk...',
                            queue='list_subtitles_movies', item=i, length=count_movies)
        store_subtitles_movie(path_replace_movie(movie.path))
    
    gc.collect()


def series_scan_subtitles(no):
    episodes = TableEpisodes.select(
        TableEpisodes.path
    ).where(
        TableEpisodes.sonarr_series_id == no
    )
    
    for episode in episodes:
        store_subtitles(path_replace(episode.path))
    
    list_missing_subtitles(no)


def movies_scan_subtitles(no):
    movies = TableMovies.select(
        TableMovies.path
    ).where(
        TableMovies.radarr_id == no
    )
    
    for movie in movies:
        store_subtitles_movie(path_replace_movie(movie.path))
    
    list_missing_subtitles_movies(no)


def get_external_subtitles_path(file, subtitle):
    fld = os.path.dirname(file)
    
    if settings.general.subfolder == "current":
        path = os.path.join(fld, subtitle)
    elif settings.general.subfolder == "absolute":
        custom_fld = settings.general.subfolder_custom
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    elif settings.general.subfolder == "relative":
        custom_fld = os.path.join(fld, settings.general.subfolder_custom)
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    else:
        path = None
    
    return path
