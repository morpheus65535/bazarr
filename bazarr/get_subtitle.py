# coding=utf-8

import os
import sqlite3
import ast
import logging
import operator
import subprocess
import time
import cPickle as pickle
import codecs
import subliminal
import subliminal_patch
from datetime import datetime, timedelta
from subzero.language import Language
from subzero.video import parse_video
from subliminal import region, Video, download_best_subtitles, save_subtitles, score as subliminal_scores, \
    list_subtitles, download_subtitles
from subliminal_patch.core import SZAsyncProviderPool as AsyncProviderPool
from subliminal_patch.score import compute_score
from subliminal.subtitle import get_subtitle_path
from get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2
from bs4 import UnicodeDammit
from get_settings import get_general_settings, pp_replace, path_replace, path_replace_movie, path_replace_reverse, \
    path_replace_reverse_movie
from list_subtitles import store_subtitles, list_missing_subtitles, store_subtitles_movie, list_missing_subtitles_movies
from utils import history_log, history_log_movie
from notifier import send_notifications, send_notifications_movie
from get_providers import get_providers, get_providers_auth
from get_args import args
from subliminal.providers.legendastv import LegendasTVSubtitle

# configure the cache

# fixme: do this inside a setup routine
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

    # todo:
    """
    AsyncProviderPool:
    implement:
        blacklist=None, 
        throttle_callback=None,
        pre_download_hook=None, 
        post_download_hook=None, 
        language_hook=None
    """

    """
    throttle_callback:
    
    VALID_THROTTLE_EXCEPTIONS = (TooManyRequests, DownloadLimitExceeded, ServiceUnavailable, APIThrottled)
    
    PROVIDER_THROTTLE_MAP = {
        "default": {
            TooManyRequests: (datetime.timedelta(hours=1), "1 hour"),
            DownloadLimitExceeded: (datetime.timedelta(hours=3), "3 hours"),
            ServiceUnavailable: (datetime.timedelta(minutes=20), "20 minutes"),
            APIThrottled: (datetime.timedelta(minutes=10), "10 minutes"),
        },
        "opensubtitles": {
            TooManyRequests: (datetime.timedelta(hours=3), "3 hours"),
            DownloadLimitExceeded: (datetime.timedelta(hours=6), "6 hours"),
            APIThrottled: (datetime.timedelta(seconds=15), "15 seconds"),
        },
        "addic7ed": {
            DownloadLimitExceeded: (datetime.timedelta(hours=3), "3 hours"),
            TooManyRequests: (datetime.timedelta(minutes=5), "5 minutes"),
        }
    }
    
    throttle_callback gist:
        def provider_throttle(self, name, exception):
            cls = getattr(exception, "__class__")
            cls_name = getattr(cls, "__name__")
            if cls not in VALID_THROTTLE_EXCEPTIONS:
                for valid_cls in VALID_THROTTLE_EXCEPTIONS:
                    if isinstance(cls, valid_cls):
                        cls = valid_cls
    
            throttle_data = PROVIDER_THROTTLE_MAP.get(name, PROVIDER_THROTTLE_MAP["default"]).get(cls, None) or \
                PROVIDER_THROTTLE_MAP["default"].get(cls, None)
    
            if not throttle_data:
                return
    
            throttle_delta, throttle_description = throttle_data    
            throttle_until = datetime.datetime.now() + throttle_delta
            
            # save throttle_until together with provider name somewhere, then implement dynamic provider_list based on
            # that
            
    provider_configs=
                {'addic7ed': {'username': Prefs['provider.addic7ed.username'],
                              'password': Prefs['provider.addic7ed.password'],
                              'use_random_agents': cast_bool(Prefs['provider.addic7ed.use_random_agents1']),
                              },
                 'opensubtitles': {'username': Prefs['provider.opensubtitles.username'],
                                   'password': Prefs['provider.opensubtitles.password'],
                                   'use_tag_search': self.exact_filenames,
                                   'only_foreign': self.forced_only,
                                   'also_foreign': self.forced_also,
                                   'is_vip': cast_bool(Prefs['provider.opensubtitles.is_vip']),
                                   'use_ssl': os_use_https,
                                   'timeout': self.advanced.providers.opensubtitles.timeout or 15,
                                   'skip_wrong_fps': os_skip_wrong_fps,
                                   },
                 'podnapisi': {
                     'only_foreign': self.forced_only,
                     'also_foreign': self.forced_also,
                 },
                 'subscene': {
                     'only_foreign': self.forced_only,
                 },
                 'legendastv': {'username': Prefs['provider.legendastv.username'],
                                'password': Prefs['provider.legendastv.password'],
                                },
                 'assrt': {'token': Prefs['provider.assrt.token'], }
                 }

    """

    try:
        if sceneName == "None" or not use_scenename:
            used_sceneName = False
            video = parse_video(path, None, providers=providers)
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
                sorted_subtitles = sorted([(s, compute_score(s, video, hearing_impaired=hi)) for s in subtitles],
                                          key=operator.itemgetter(1), reverse=True)
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
                logging.debug(
                    'BAZARR ' + str(len(subtitles_list)) + " subtitles have been found for this file: " + path)
                if len(subtitles_list) > 0:
                    try:
                        download_result = False
                        for subtitle in subtitles_list:
                            download_result = p.download_subtitle(subtitle)
                            if download_result == True:
                                logging.debug('BAZARR Subtitles file downloaded from ' + str(
                                    subtitle.provider_name) + ' for this file: ' + path)
                                break
                            else:
                                logging.warning('BAZARR Subtitles file skipped from ' + str(
                                    subtitle.provider_name) + ' for this file: ' + path + ' because no content was returned by the provider (probably throttled).')
                                continue
                        if download_result == False:
                            logging.error(
                                'BAZARR Tried to download a subtitles for file: ' + path + " but we weren't able to do it this time (probably being throttled). Going to retry on next search.")
                            return None
                    except Exception as e:
                        logging.exception('BAZARR Error downloading subtitles for this file ' + path)
                        return None
                    else:
                        try:
                            calculated_score = round(
                                float(compute_score(subtitle, video, hearing_impaired=hi)) / max_score * 100, 2)
                            if used_sceneName == True:
                                video = parse_video(path, None, providers=providers)
                            single = get_general_settings()[7]
                            if single is True:
                                result = save_subtitles(video, [subtitle], single=True, encoding='utf-8')
                            else:
                                result = save_subtitles(video, [subtitle], encoding='utf-8')
                        except Exception as e:
                            logging.exception('BAZARR Error saving subtitles file to disk for this file:' + path)
                            pass
                        else:
                            downloaded_provider = result[0].provider_name
                            downloaded_language = language_from_alpha3(result[0].language.alpha3)
                            downloaded_language_code2 = alpha2_from_alpha3(result[0].language.alpha3)
                            downloaded_language_code3 = result[0].language.alpha3
                            downloaded_path = get_subtitle_path(path, downloaded_language_code2)
                            logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                            if used_sceneName == True:
                                message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(
                                    calculated_score) + "% using this scene name: " + sceneName
                            else:
                                message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(
                                    calculated_score) + "% using filename guessing."

                            if use_postprocessing is True:
                                command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                     downloaded_language_code2, downloaded_language_code3)
                                try:
                                    if os.name == 'nt':
                                        codepage = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE,
                                                                    stderr=subprocess.PIPE)
                                        # wait for the process to terminate
                                        out_codepage, err_codepage = codepage.communicate()
                                        encoding = out_codepage.split(':')[-1].strip()

                                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                                               stderr=subprocess.PIPE)
                                    # wait for the process to terminate
                                    out, err = process.communicate()

                                    if os.name == 'nt':
                                        out = out.decode(encoding)

                                except:
                                    if out == "":
                                        logging.error(
                                            'BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                                    else:
                                        logging.error('BAZARR Post-processing result for file ' + path + ' : ' + out)
                                else:
                                    if out == "":
                                        logging.info(
                                            'BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                                    else:
                                        logging.info('BAZARR Post-processing result for file ' + path + ' : ' + out)

                            return message
                else:
                    logging.debug('BAZARR No subtitles were found for this file: ' + path)
                    return None
    logging.debug('BAZARR Ended searching subtitles for file: ' + path)


def manual_search(path, language, hi, providers, providers_auth, sceneName, title, media_type):
    logging.debug('BAZARR Manually searching subtitles for this file: ' + path)

    final_subtitles = []

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

    hints = {"title": title}
    dont_use_actual_file = False
    if sceneName != "None" and use_scenename:
        # use the sceneName but keep the folder structure for better guessing
        path = os.path.join(os.path.dirname(path), sceneName + os.path.splitext(path)[1])
        dont_use_actual_file = True

    try:
        video = parse_video(path, hints=hints, providers=providers, dry_run=dont_use_actual_file)

    except:
        logging.exception("BAZARR Error trying to get video information for this file: " + path)
    else:
        min_score = 60.0
        max_score = 120.0
        scores = subliminal_scores.movie_scores.keys()
        if media_type == "series":
            min_score = 240.0
            max_score = 360.0
            scores = subliminal_scores.episode_scores.keys()
            if video.is_special:
                min_score = 180

        scores = set(scores)

        try:
            subtitles = list_subtitles([video], language_set,
                                       providers=providers,
                                       provider_configs=providers_auth,
                                       pool_class=AsyncProviderPool,  # fixme: make async optional
                                       throttle_callback=None,  # fixme
                                       language_hook=None)  # fixme
        except Exception as e:
            logging.exception("BAZARR Error trying to get subtitle list from provider for this file: " + path)
        else:
            subtitles_list = []

            for s in subtitles[video]:
                try:
                    matches = s.get_matches(video)
                except AttributeError:
                    continue

                # skip wrong season/episodes
                if media_type == "series":
                    can_verify_series = True
                    if not s.hash_verifiable and "hash" in matches:
                        can_verify_series = False

                    if can_verify_series and not {"series", "season", "episode"}.issubset(matches):
                        logging.debug(u"BAZARR Skipping %s, because it doesn't match our series/episode", s)
                        continue

                not_matched = scores - matches
                score = compute_score(matches, s, video, hearing_impaired=hi)
                if score < min_score:
                    continue

                subtitles_list.append(
                    dict(score=round((score / max_score * 100), 2),
                         language=alpha2_from_alpha3(s.language.alpha3), hearing_impaired=str(s.hearing_impaired),
                         provider=s.provider_name,
                         subtitle=codecs.encode(pickle.dumps(s.make_picklable()), "base64").decode(),
                         url=s.page_link, matches=list(matches), dont_matches=list(not_matched)))

            final_subtitles = sorted(subtitles_list, key=lambda x: x['score'], reverse=True)
            logging.debug('BAZARR ' + str(len(final_subtitles)) + " subtitles have been found for this file: " + path)
            logging.debug('BAZARR Ended searching subtitles for this file: ' + path)
    return final_subtitles


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
        if sceneName is None or not use_scenename:
            used_sceneName = False
            video = parse_video(path, None, providers={provider})
        else:
            used_sceneName = True
            video = Video.fromname(sceneName)
    except Exception as e:
        logging.exception("BAZARR Error trying to get video information for this file: " + path)
        pass
    else:
        try:
            download_subtitles([subtitle], providers=provider, provider_configs=providers_auth)
            logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
        except Exception as e:
            logging.exception('BAZARR Error downloading subtitles for this file ' + path)
            return None
        else:
            single = get_general_settings()[7]
            try:
                score = round(float(compute_score(subtitle, video, hearing_impaired=hi)) / type_of_score * 100, 2)
                if used_sceneName == True:
                    video = parse_video(path, None, providers={provider})
                if single is True:
                    result = save_subtitles(video, [subtitle], single=True, encoding='utf-8')
                else:
                    result = save_subtitles(video, [subtitle], encoding='utf-8')
            except Exception as e:
                logging.exception('BAZARR Error saving subtitles file to disk for this file:' + path)
                return None
            else:
                if len(result) > 0:
                    downloaded_provider = result[0].provider_name
                    downloaded_language = language_from_alpha3(result[0].language.alpha3)
                    downloaded_language_code2 = alpha2_from_alpha3(result[0].language.alpha3)
                    downloaded_language_code3 = result[0].language.alpha3
                    downloaded_path = get_subtitle_path(path, downloaded_language_code2)
                    logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                    message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(
                        score) + "% using manual search."

                    if use_postprocessing is True:
                        command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                             downloaded_language_code2, downloaded_language_code3)
                        try:
                            if os.name == 'nt':
                                codepage = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE,
                                                            stderr=subprocess.PIPE)
                                # wait for the process to terminate
                                out_codepage, err_codepage = codepage.communicate()
                                encoding = out_codepage.split(':')[-1].strip()

                            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE)
                            # wait for the process to terminate
                            out, err = process.communicate()

                            if os.name == 'nt':
                                out = out.decode(encoding)

                        except:
                            if out == "":
                                logging.error(
                                    'BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                            else:
                                logging.error('BAZARR Post-processing result for file ' + path + ' : ' + out)
                        else:
                            if out == "":
                                logging.info(
                                    'BAZARR Post-processing result for file ' + path + ' : Nothing returned from command execution')
                            else:
                                logging.info('BAZARR Post-processing result for file ' + path + ' : ' + out)

                    return message
                else:
                    logging.error(
                        'BAZARR Tried to manually download a subtitles for file: ' + path + " but we weren't able to do (probably throttled by ' + str(subtitle.provider_name) + '. Please retry later or select a subtitles from another provider.")
                    return None
    logging.debug('BAZARR Ended manually downloading subtitles for file: ' + path)


def series_download_subtitles(no):
    if get_general_settings()[24] is True:
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""

    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute(
        'SELECT path, missing_subtitles, sonarrEpisodeId, scene_name FROM table_episodes WHERE sonarrSeriesId = ? AND missing_subtitles != "[]"' + monitored_only_query_string,
        (no,)).fetchall()
    series_details = c_db.execute("SELECT hearing_impaired FROM table_shows WHERE sonarrSeriesId = ?", (no,)).fetchone()
    c_db.close()

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for episode in episodes_details:
        for language in ast.literal_eval(episode[1]):
            if language is not None:
                message = download_subtitle(path_replace(episode[0]), str(alpha3_from_alpha2(language)),
                                            series_details[0], providers_list, providers_auth, str(episode[3]),
                                            'series')
                if message is not None:
                    store_subtitles(path_replace(episode[0]))
                    history_log(1, no, episode[2], message)
                    send_notifications(no, episode[2], message)
    list_missing_subtitles(no)


def movies_download_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movie = c_db.execute(
        "SELECT path, missing_subtitles, radarrId, sceneName, hearing_impaired FROM table_movies WHERE radarrId = ?",
        (no,)).fetchone()
    c_db.close()

    providers_list = get_providers()
    providers_auth = get_providers_auth()

    for language in ast.literal_eval(movie[1]):
        if language is not None:
            message = download_subtitle(path_replace_movie(movie[0]), str(alpha3_from_alpha2(language)), movie[4],
                                        providers_list, providers_auth, str(movie[3]), 'movie')
            if message is not None:
                store_subtitles_movie(path_replace_movie(movie[0]))
                history_log_movie(1, no, message)
                send_notifications_movie(no, message)
    list_missing_subtitles_movies(no)


def wanted_download_subtitles(path):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute(
        "SELECT table_episodes.path, table_episodes.missing_subtitles, table_episodes.sonarrEpisodeId, table_episodes.sonarrSeriesId, table_shows.hearing_impaired, table_episodes.scene_name, table_episodes.failedAttempts FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.path = ? AND missing_subtitles != '[]'",
        (path_replace_reverse(path),)).fetchall()
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

            conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c_db = conn_db.cursor()
            c_db.execute('UPDATE table_episodes SET failedAttempts = ? WHERE sonarrEpisodeId = ?',
                         (unicode(attempt), episode[2]))
            conn_db.commit()
            c_db.close()

            for i in range(len(attempt)):
                if attempt[i][0] == language:
                    if search_active(attempt[i][1]) is True:
                        message = download_subtitle(path_replace(episode[0]), str(alpha3_from_alpha2(language)),
                                                    episode[4], providers_list, providers_auth, str(episode[5]),
                                                    'series')
                        if message is not None:
                            store_subtitles(path_replace(episode[0]))
                            list_missing_subtitles(episode[3])
                            history_log(1, episode[3], episode[2], message)
                            send_notifications(episode[3], episode[2], message)
                    else:
                        logging.debug(
                            'BAZARR Search is not active for episode ' + episode[0] + ' Language: ' + attempt[i][0])


def wanted_download_subtitles_movie(path):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movies_details = c_db.execute(
        "SELECT path, missing_subtitles, radarrId, radarrId, hearing_impaired, sceneName, failedAttempts FROM table_movies WHERE path = ? AND missing_subtitles != '[]'",
        (path_replace_reverse_movie(path),)).fetchall()
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

            conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
            c_db = conn_db.cursor()
            c_db.execute('UPDATE table_movies SET failedAttempts = ? WHERE radarrId = ?', (unicode(attempt), movie[2]))
            conn_db.commit()
            c_db.close()

            for i in range(len(attempt)):
                if attempt[i][0] == language:
                    if search_active(attempt[i][1]) is True:
                        message = download_subtitle(path_replace_movie(movie[0]), str(alpha3_from_alpha2(language)),
                                                    movie[4], providers_list, providers_auth, str(movie[5]), 'movie')
                        if message is not None:
                            store_subtitles_movie(path_replace_movie(movie[0]))
                            list_missing_subtitles_movies(movie[3])
                            history_log_movie(1, movie[3], message)
                            send_notifications_movie(movie[3], message)
                    else:
                        logging.info(
                            'BAZARR Search is not active for movie ' + movie[0] + ' Language: ' + attempt[i][0])


def wanted_search_missing_subtitles():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    db.create_function("path_substitution_movie", 1, path_replace_movie)
    c = db.cursor()

    if get_general_settings()[24] is True:
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""

    c.execute(
        "SELECT path_substitution(path) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string)
    episodes = c.fetchall()

    c.execute(
        "SELECT path_substitution_movie(path) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string)
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
