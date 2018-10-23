from get_argv import config_dir

import os
import sqlite3
import ast
import logging
import operator
import subprocess
import time
from datetime import datetime, timedelta
from babelfish import Language
from subliminal import region, scan_video, Video, download_best_subtitles, compute_score, save_subtitles, AsyncProviderPool, score, list_subtitles, download_subtitles
from subliminal.subtitle import get_subtitle_path
from get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2
from bs4 import UnicodeDammit
from get_settings import get_general_settings, pp_replace, path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie
from list_subtitles import store_subtitles, list_missing_subtitles, store_subtitles_movie, list_missing_subtitles_movies
from utils import history_log, history_log_movie
from notifier import send_notifications, send_notifications_movie
import cPickle as pickle
import codecs
from get_providers import get_providers, get_providers_auth

# configure the cache
region.configure('dogpile.cache.memory')

def download_subtitle(path, language, hi, providers, providers_auth, sceneName, media_type):
    logging.debug('BAZARR Searching subtitles for this file: ' + path)
    if hi == "True":
        hi = True
    else:
        hi = False
    language_set = set()
    if language == 'pob':
        language_set.add(Language('por', 'BR'))
    else:
        language_set.add(Language(language))

    use_scenename = get_general_settings()[9]
    minimum_score = get_general_settings()[8]
    minimum_score_movie = get_general_settings()[22]
    use_postprocessing = get_general_settings()[10]
    postprocessing_cmd = get_general_settings()[11]

    try:
        if sceneName == "None" or use_scenename is False:
            used_sceneName = False
            video = scan_video(path)
        else:
            used_sceneName = True
            video = Video.fromname(sceneName)
    except Exception as e:
        logging.exception("BAZARR Error trying to get video information for this file: " + path)
        pass
    else:
        if media_type == "movie":
            max_score = 120.0
        elif media_type == "series":
            max_score = 360.0

        try:
            with AsyncProviderPool(max_workers=None, providers=providers, provider_configs=providers_auth) as p:
                subtitles = p.list_subtitles(video, language_set)
        except Exception as e:
            logging.exception("BAZARR Error trying to get subtitle list from provider for this file: " + path)
        else:
            subtitles_list = []
            try:
                sorted_subtitles = sorted([(s, compute_score(s, video, hearing_impaired=hi)) for s in subtitles], key=operator.itemgetter(1), reverse=True)
            except Exception as e:
                logging.exception('BAZARR Exception raised while trying to compute score for this file: ' + path)
                return None
            else:
                for s, preliminary_score in sorted_subtitles:
                    if media_type == "movie":
                        if (preliminary_score / max_score * 100) < int(minimum_score_movie):
                            continue
                        matched = set(s.get_matches(video))
                        if hi == s.hearing_impaired:
                            matched.add('hearing_impaired')
                        not_matched = set(score.movie_scores.keys()) - matched
                        required = set(['title'])
                        if any(elem in required for elem in not_matched):
                            continue
                    elif media_type == "series":
                        if (preliminary_score / max_score * 100) < int(minimum_score):
                            continue
                        matched = set(s.get_matches(video))
                        if hi == s.hearing_impaired:
                            matched.add('hearing_impaired')
                        not_matched = set(score.episode_scores.keys()) - matched
                        required = set(['series', 'season', 'episode'])
                        if any(elem in required for elem in not_matched):
                            continue
                    subtitles_list.append(s)
                logging.debug('BAZARR ' + str(len(subtitles_list)) + " subtitles have been found for this file: " + path)
                if len(subtitles_list) > 0:
                    try:
                        best_subtitle = subtitles_list[0]
                        download_subtitles([best_subtitle], providers=providers, provider_configs=providers_auth)
                        logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
                    except Exception as e:
                        logging.exception('BAZARR Error downloading subtitles for this file ' + path)
                        return None
                    else:
                        try:
                            calculated_score = round(float(compute_score(best_subtitle, video, hearing_impaired=hi)) / max_score * 100, 2)
                            if used_sceneName == True:
                                video = scan_video(path)
                            single = get_general_settings()[7]
                            if single is True:
                                result = save_subtitles(video, [best_subtitle], single=True, encoding='utf-8')
                            else:
                                result = save_subtitles(video, [best_subtitle], encoding='utf-8')
                        except Exception as e:
                            logging.exception('BAZARR Error saving subtitles file to disk for this file:' + path)
                            pass
                        else:
                            if len(result) > 0:
                                downloaded_provider = result[0].provider_name
                                downloaded_language = language_from_alpha3(result[0].language.alpha3)
                                downloaded_language_code2 = alpha2_from_alpha3(result[0].language.alpha3)
                                downloaded_language_code3 = result[0].language.alpha3
                                downloaded_path = get_subtitle_path(path, language=language_set)
                                logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                                if used_sceneName == True:
                                    message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(calculated_score) + "% using this scene name: " + sceneName
                                else:
                                    message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(calculated_score) + "% using filename guessing."

                                if use_postprocessing is True:
                                    command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language, downloaded_language_code2, downloaded_language_code3)
                                    try:
                                        if os.name == 'nt':
                                            codepage = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                            # wait for the process to terminate
                                            out_codepage, err_codepage = codepage.communicate()
                                            encoding = out_codepage.split(':')[-1].strip()

                                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                        # wait for the process to terminate
                                        out, err = process.communicate()

                                        if os.name == 'nt':
                                            out = out.decode(encoding)

                                    except:
                                        if out == "":
                                            logging.error('BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                                        else:
                                            logging.error('BAZARR Post-processing result for file ' + path + ' : ' + out)
                                    else:
                                        if out == "":
                                            logging.info('BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                                        else:
                                            logging.info('BAZARR Post-processing result for file ' + path + ' : ' + out)

                                return message
                            else:
                                logging.error('BAZARR Tried to download best subtitles available for file: ' + path + ' but it had no content. Going to retry on next search.')
                                return None
                else:
                    return None
    logging.debug('BAZARR Ended searching subtitles for file: ' + path)

def manual_search(path, language, hi, providers, providers_auth, sceneName, media_type):
    logging.debug('BAZARR Manually searching subtitles for this file: ' + path)
    if hi == "True":
        hi = True
    else:
        hi = False
    language_set = set()
    for lang in ast.literal_eval(language):
        lang = alpha3_from_alpha2(lang)
        if lang == 'pob':
            language_set.add(Language('por', 'BR'))
        else:
            language_set.add(Language(lang))

    use_scenename = get_general_settings()[9]
    use_postprocessing = get_general_settings()[10]
    postprocessing_cmd = get_general_settings()[11]

    try:
        if sceneName == "None" or use_scenename is False:
            used_sceneName = False
            video = scan_video(path)
        else:
            used_sceneName = True
            video = Video.fromname(sceneName)
    except:
        logging.exception("BAZARR Error trying to get video information for this file: " + path)
    else:
        if media_type == "movie":
            max_score = 120.0
        elif media_type == "series":
            max_score = 360.0

        try:
            with AsyncProviderPool(max_workers=None, providers=providers, provider_configs=providers_auth) as p:
                subtitles = p.list_subtitles(video, language_set)
        except Exception as e:
            logging.exception("BAZARR Error trying to get subtitle list from provider for this file: " + path)
        else:
            subtitles_list = []
            for s in subtitles:
                {s: compute_score(s, video, hearing_impaired=hi)}
                if media_type == "movie":
                    matched = set(s.get_matches(video))
                    if hi == s.hearing_impaired:
                        matched.add('hearing_impaired')
                    not_matched = set(score.movie_scores.keys()) - matched
                    required = set(['title'])
                    if any(elem in required for elem in not_matched):
                        continue
                    if used_sceneName:
                        not_matched.remove('hash')
                elif media_type == "series":
                    matched = set(s.get_matches(video))
                    if hi == s.hearing_impaired:
                        matched.add('hearing_impaired')
                    not_matched = set(score.episode_scores.keys()) - matched
                    required = set(['series', 'season', 'episode'])
                    if any(elem in required for elem in not_matched):
                        continue
                    if used_sceneName:
                        not_matched.remove('hash')
                subtitles_list.append(dict(score=round((compute_score(s, video, hearing_impaired=hi) / max_score * 100), 2), language=alpha2_from_alpha3(s.language.alpha3), hearing_impaired=str(s.hearing_impaired), provider=s.provider_name, subtitle=codecs.encode(pickle.dumps(s), "base64").decode(), url=s.page_link, matches=list(matched), dont_matches=list(not_matched)))
            subtitles_dict = {}
            subtitles_dict = sorted(subtitles_list, key=lambda x: x['score'], reverse=True)
            logging.debug('BAZARR ' + str(len(subtitles_dict)) + " subtitles have been found for this file: " + path)
            logging.debug('BAZARR Ended searching subtitles for this file: ' + path)
            return(subtitles_dict)

def manual_download_subtitle(path, language, hi, subtitle, provider, providers_auth, sceneName, media_type):
    logging.debug('BAZARR Manually downloading subtitles for this file: ' + path)
    if hi == "True":
        hi = True
    else:
        hi = False
    subtitle = pickle.loads(codecs.decode(subtitle.encode(), "base64"))
    if media_type == 'series':
        type_of_score = 360
    elif media_type == 'movie':
        type_of_score = 120
    use_scenename = get_general_settings()[9]
    use_postprocessing = get_general_settings()[10]
    postprocessing_cmd = get_general_settings()[11]

    language = alpha3_from_alpha2(language)
    if language == 'pob':
        lang_obj = Language('por', 'BR')
    else:
        lang_obj = Language(language)

    try:
        if sceneName is None or use_scenename is False:
            used_sceneName = False
            video = scan_video(path)
        else:
            used_sceneName = True
            video = Video.fromname(sceneName)
    except Exception as e:
        logging.exception("BAZARR Error trying to get video information for this file: " + path)
        pass
    else:
        try:
            best_subtitle = subtitle
            download_subtitles([best_subtitle], providers=provider, provider_configs=providers_auth)
            logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
        except Exception as e:
            logging.exception('BAZARR Error downloading subtitles for this file ' + path)
            return None
        else:
            single = get_general_settings()[7]
            try:
                score = round(float(compute_score(best_subtitle, video, hearing_impaired=hi)) / type_of_score * 100, 2)
                if used_sceneName == True:
                    video = scan_video(path)
                if single is True:
                    result = save_subtitles(video, [best_subtitle], single=True, encoding='utf-8')
                else:
                    result = save_subtitles(video, [best_subtitle], encoding='utf-8')
            except Exception as e:
                logging.exception('BAZARR Error saving subtitles file to disk for this file:' + path)
                return None
            else:
                if len(result) > 0:
                    downloaded_provider = result[0].provider_name
                    downloaded_language = language_from_alpha3(result[0].language.alpha3)
                    downloaded_language_code2 = alpha2_from_alpha3(result[0].language.alpha3)
                    downloaded_language_code3 = result[0].language.alpha3
                    downloaded_path = get_subtitle_path(path, language=lang_obj)
                    logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                    message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(score) + "% using manual search."

                    if use_postprocessing is True:
                        command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language, downloaded_language_code2, downloaded_language_code3)
                        try:
                            if os.name == 'nt':
                                codepage = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                # wait for the process to terminate
                                out_codepage, err_codepage = codepage.communicate()
                                encoding = out_codepage.split(':')[-1].strip()

                            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            # wait for the process to terminate
                            out, err = process.communicate()

                            if os.name == 'nt':
                                out = out.decode(encoding)

                        except:
                            if out == "":
                                logging.error('BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                            else:
                                logging.error('BAZARR Post-processing result for file ' + path + ' : ' + out)
                        else:
                            if out == "":
                                logging.info('BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                            else:
                                logging.info('BAZARR Post-processing result for file ' + path + ' : ' + out)

                    return message
                else:
                    logging.error('BAZARR Tried to manually download a subtitles for file: ' + path + ' but it had no content. Going to retry on next search.')
                    return None
    logging.debug('BAZARR Ended manually downloading subtitles for file: ' + path)

def series_download_subtitles(no):
    if get_general_settings()[24] is True:
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""

    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute('SELECT path, missing_subtitles, sonarrEpisodeId, scene_name FROM table_episodes WHERE sonarrSeriesId = ? AND missing_subtitles != "[]"' + monitored_only_query_string, (no,)).fetchall()
    series_details = c_db.execute("SELECT hearing_impaired FROM table_shows WHERE sonarrSeriesId = ?", (no,)).fetchone()
    c_db.close()
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
        
    for episode in episodes_details:
        for language in ast.literal_eval(episode[1]):
            if language is not None:
                message = download_subtitle(path_replace(episode[0]), str(alpha3_from_alpha2(language)), series_details[0], providers_list, providers_auth, str(episode[3]), 'series')
                if message is not None:
                    store_subtitles(path_replace(episode[0]))
                    history_log(1, no, episode[2], message)
                    send_notifications(no, episode[2], message)
    list_missing_subtitles(no)


def movies_download_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movie = c_db.execute("SELECT path, missing_subtitles, radarrId, sceneName, hearing_impaired FROM table_movies WHERE radarrId = ?", (no,)).fetchone()
    c_db.close()

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for language in ast.literal_eval(movie[1]):
        if language is not None:
            message = download_subtitle(path_replace_movie(movie[0]), str(alpha3_from_alpha2(language)), movie[4], providers_list, providers_auth, str(movie[3]), 'movie')
            if message is not None:
                store_subtitles_movie(path_replace_movie(movie[0]))
                history_log_movie(1, no, message)
                send_notifications_movie(no, message)
    list_missing_subtitles_movies(no)


def wanted_download_subtitles(path):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute("SELECT table_episodes.path, table_episodes.missing_subtitles, table_episodes.sonarrEpisodeId, table_episodes.sonarrSeriesId, table_shows.hearing_impaired, table_episodes.scene_name, table_episodes.failedAttempts FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.path = ? AND missing_subtitles != '[]'", (path_replace_reverse(path),)).fetchall()
    c_db.close()

    providers_list = get_providers()
    providers_auth = get_providers_auth()
        
    for episode in episodes_details:
        attempt = episode[6]
        if type(attempt) == unicode:
            attempt = ast.literal_eval(attempt)
        for language in ast.literal_eval(episode[1]):
            if attempt is None:
                attempt = []
                attempt.append([language, time.time()])
            else:
                att = zip(*attempt)[0]
                if language not in att:
                    attempt.append([language, time.time()])
                    
            conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c_db = conn_db.cursor()
            c_db.execute('UPDATE table_episodes SET failedAttempts = ? WHERE sonarrEpisodeId = ?', (unicode(attempt), episode[2]))
            conn_db.commit()
            c_db.close()
            
            for i in range(len(attempt)):
                if attempt[i][0] == language:
                    if search_active(attempt[i][1]) is True:
                        message = download_subtitle(path_replace(episode[0]), str(alpha3_from_alpha2(language)), episode[4], providers_list, providers_auth, str(episode[5]), 'series')
                        if message is not None:
                            store_subtitles(path_replace(episode[0]))
                            list_missing_subtitles(episode[3])
                            history_log(1, episode[3], episode[2], message)
                            send_notifications(episode[3], episode[2], message)
                    else:
                        logging.debug('BAZARR Search is not active for episode ' + episode[0] + ' Language: ' + attempt[i][0])


def wanted_download_subtitles_movie(path):
    conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movies_details = c_db.execute("SELECT path, missing_subtitles, radarrId, radarrId, hearing_impaired, sceneName, failedAttempts FROM table_movies WHERE path = ? AND missing_subtitles != '[]'", (path_replace_reverse_movie(path),)).fetchall()
    c_db.close()

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for movie in movies_details:
        attempt = movie[6]
        if type(attempt) == unicode:
            attempt = ast.literal_eval(attempt)
        for language in ast.literal_eval(movie[1]):
            if attempt is None:
                attempt = []
                attempt.append([language, time.time()])
            else:
                att = zip(*attempt)[0]
                if language not in att:
                    attempt.append([language, time.time()])
                    
            conn_db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c_db = conn_db.cursor()
            c_db.execute('UPDATE table_movies SET failedAttempts = ? WHERE radarrId = ?', (unicode(attempt), movie[2]))
            conn_db.commit()
            c_db.close()
            
            for i in range(len(attempt)):
                if attempt[i][0] == language:
                    if search_active(attempt[i][1]) is True:
                        message = download_subtitle(path_replace_movie(movie[0]), str(alpha3_from_alpha2(language)), movie[4], providers_list, providers_auth, str(movie[5]), 'movie')
                        if message is not None:
                            store_subtitles_movie(path_replace_movie(movie[0]))
                            list_missing_subtitles_movies(movie[3])
                            history_log_movie(1, movie[3], message)
                            send_notifications_movie(movie[3], message)
                    else:
                        logging.info('BAZARR Search is not active for movie ' + movie[0] + ' Language: ' + attempt[i][0])


def wanted_search_missing_subtitles():
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    db.create_function("path_substitution_movie", 1, path_replace_movie)
    c = db.cursor()

    if get_general_settings()[24] is True:
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""

    c.execute("SELECT path_substitution(path) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    episodes = c.fetchall()

    c.execute("SELECT path_substitution_movie(path) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    movies = c.fetchall()

    c.close()

    integration = get_general_settings()

    if integration[12] is True:
        for episode in episodes:
            wanted_download_subtitles(episode[0])

    if integration[13] is True:
        for movie in movies:
            wanted_download_subtitles_movie(movie[0])

    logging.info('BAZARR Finished searching for missing subtitles. Check histories for more information.')
  

def search_active(timestamp):
    if get_general_settings()[25] is True:
        search_deadline = timedelta(weeks=3)
        search_delta = timedelta(weeks=1)
        aa = datetime.fromtimestamp(float(timestamp))
        attempt_datetime = datetime.strptime(str(aa).split(".")[0], '%Y-%m-%d %H:%M:%S')
        attempt_search_deadline = attempt_datetime + search_deadline
        today = datetime.today()
        attempt_age_in_days = (today.date() - attempt_search_deadline.date()).days
        if today.date() <= attempt_search_deadline.date():
            return True
        elif attempt_age_in_days % search_delta.days == 0:
            return True
        else:
            return False
    else:
        return True
