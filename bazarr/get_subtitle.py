# coding=utf-8

import os
import sys
import sqlite3
import ast
import logging
import subprocess
import time
import cPickle as pickle
import codecs
import types
import re
import subliminal
import platform
from datetime import datetime, timedelta
from subzero.language import Language
from subzero.video import parse_video
from subliminal import region, score as subliminal_scores, \
    list_subtitles, Episode, Movie
from subliminal_patch.core import SZAsyncProviderPool, download_best_subtitles, save_subtitles, download_subtitles, \
    list_all_subtitles, get_subtitle_path
from subliminal_patch.score import compute_score
from subliminal.refiners.tvdb import series_re
from get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2, language_from_alpha2
from config import settings
from helper import path_replace, path_replace_movie, path_replace_reverse, \
    path_replace_reverse_movie, pp_replace, get_target_folder, force_unicode
from list_subtitles import store_subtitles, list_missing_subtitles, store_subtitles_movie, list_missing_subtitles_movies
from utils import history_log, history_log_movie, get_binary
from notifier import send_notifications, send_notifications_movie
from get_providers import get_providers, get_providers_auth, provider_throttle, provider_pool
from get_args import args
from queueconfig import notifications
from pymediainfo import MediaInfo


def get_video(path, title, sceneName, use_scenename, use_mediainfo, providers=None, media_type="movie"):
    """
    Construct `Video` instance
    :param path: path to video
    :param title: series/movie title
    :param sceneName: sceneName
    :param use_scenename: use sceneName
    :param use_mediainfo: use media info to refine the video
    :param providers: provider list for selective hashing
    :param media_type: movie/series
    :return: `Video` instance
    """
    hints = {"title": title, "type": "movie" if media_type == "movie" else "episode"}
    used_scene_name = False
    original_path = path
    original_name = os.path.basename(path)
    hash_from = None
    if sceneName != "None" and use_scenename:
        # use the sceneName but keep the folder structure for better guessing
        path = os.path.join(os.path.dirname(path), sceneName + os.path.splitext(path)[1])
        used_scene_name = True
        hash_from = original_path
    
    try:
        video = parse_video(path, hints=hints, providers=providers, dry_run=used_scene_name,
                            hash_from=hash_from)
        video.used_scene_name = used_scene_name
        video.original_name = original_name
        video.original_path = original_path
        refine_from_db(original_path, video)
        
        if platform.system() != "Linux" and use_mediainfo:
            refine_from_mediainfo(original_path, video)
        
        logging.debug('BAZARR is using those video object properties: %s', vars(video))
        return video
    
    except:
        logging.exception("BAZARR Error trying to get video information for this file: " + path)


def get_scores(video, media_type, min_score_movie_perc=60 * 100 / 120.0, min_score_series_perc=240 * 100 / 360.0,
               min_score_special_ep=180 * 100 / 360.0):
    """
    Get score range for a video.
    :param video: `Video` instance
    :param media_type: movie/series
    :param min_score_movie_perc: Percentage of max score for min score of movies
    :param min_score_series_perc: Percentage of max score for min score of series
    :param min_score_special_ep: Percentage of max score for min score of series special episode
    :return: tuple(min_score, max_score, set(scores))
    """
    max_score = 120.0
    min_score = max_score * min_score_movie_perc / 100.0
    scores = subliminal_scores.movie_scores.keys()
    if media_type == "series":
        max_score = 360.0
        min_score = max_score * min_score_series_perc / 100.0
        scores = subliminal_scores.episode_scores.keys()
        if video.is_special:
            min_score = max_score * min_score_special_ep / 100.0
    
    return min_score, max_score, set(scores)


def download_subtitle(path, language, hi, forced, providers, providers_auth, sceneName, title, media_type,
                      forced_minimum_score=None, is_upgrade=False):
    # fixme: supply all missing languages, not only one, to hit providers only once who support multiple languages in
    #  one query
    
    if settings.general.getboolean('utf8_encode'):
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"
    
    logging.debug('BAZARR Searching subtitles for this file: ' + path)
    if hi == "True":
        hi = "force HI"
    else:
        hi = "force non-HI"
    language_set = set()
    
    if not isinstance(language, types.ListType):
        language = [language]
    
    if forced == "True":
        providers_auth['podnapisi']['only_foreign'] = True  ## fixme: This is also in get_providers_auth()
        providers_auth['subscene']['only_foreign'] = True  ## fixme: This is also in get_providers_auth()
        providers_auth['opensubtitles']['only_foreign'] = True  ## fixme: This is also in get_providers_auth()
    else:
        providers_auth['podnapisi']['only_foreign'] = False
        providers_auth['subscene']['only_foreign'] = False
        providers_auth['opensubtitles']['only_foreign'] = False
    
    for l in language:
        if l == 'pob':
            lang_obj = Language('por', 'BR')
            if forced == "True":
                lang_obj = Language.rebuild(lang_obj, forced=True)
        else:
            lang_obj = Language(l)
            if forced == "True":
                lang_obj = Language.rebuild(lang_obj, forced=True)
        language_set.add(lang_obj)
    
    use_scenename = settings.general.getboolean('use_scenename')
    use_mediainfo = settings.general.getboolean('use_mediainfo')
    minimum_score = settings.general.minimum_score
    minimum_score_movie = settings.general.minimum_score_movie
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd
    single = settings.general.getboolean('single_language')
    
    # todo:
    """
    AsyncProviderPool:
    implement:
        blacklist=None,
        pre_download_hook=None,
        post_download_hook=None,
        language_hook=None
    """
    video = get_video(force_unicode(path), title, sceneName, use_scenename, use_mediainfo, providers=providers,
                      media_type=media_type)
    if video:
        min_score, max_score, scores = get_scores(video, media_type, min_score_movie_perc=int(minimum_score_movie),
                                                  min_score_series_perc=int(minimum_score))
        
        if providers:
            if forced_minimum_score:
                min_score = int(forced_minimum_score) + 1
            downloaded_subtitles = download_best_subtitles({video}, language_set, int(min_score), hi,
                                                           providers=providers,
                                                           provider_configs=providers_auth,
                                                           pool_class=provider_pool(),
                                                           compute_score=compute_score,
                                                           throttle_time=None,  # fixme
                                                           blacklist=None,  # fixme
                                                           throttle_callback=provider_throttle,
                                                           pre_download_hook=None,  # fixme
                                                           post_download_hook=None,  # fixme
                                                           language_hook=None)  # fixme
        else:
            downloaded_subtitles = None
            logging.info("BAZARR All providers are throttled")
            return None
        
        saved_any = False
        if downloaded_subtitles:
            for video, subtitles in downloaded_subtitles.iteritems():
                if not subtitles:
                    continue
                
                try:
                    fld = get_target_folder(path)
                    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                        'win') and settings.general.getboolean('chmod_enabled') else None
                    saved_subtitles = save_subtitles(video.original_path, subtitles, single=single,
                                                     tags=None,  # fixme
                                                     directory=fld,
                                                     chmod=chmod,
                                                     # formats=("srt", "vtt")
                                                     path_decoder=force_unicode
                                                     )
                except Exception as e:
                    logging.exception('BAZARR Error saving subtitles file to disk for this file:' + path)
                    pass
                else:
                    saved_any = True
                    for subtitle in saved_subtitles:
                        downloaded_provider = subtitle.provider_name
                        if subtitle.language == 'pt-BR':
                            downloaded_language_code3 = 'pob'
                        else:
                            downloaded_language_code3 = subtitle.language.alpha3
                        downloaded_language = language_from_alpha3(downloaded_language_code3)
                        downloaded_language_code2 = alpha2_from_alpha3(downloaded_language_code3)
                        downloaded_path = subtitle.storage_path
                        is_forced_string = " forced" if subtitle.language.forced else ""
                        logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                        if is_upgrade:
                            action = "upgraded"
                        else:
                            action = "downloaded"
                        if video.used_scene_name:
                            message = downloaded_language + is_forced_string + " subtitles " + action + " from " + downloaded_provider + " with a score of " + unicode(
                                round(subtitle.score * 100 / max_score, 2)) + "% using this scene name: " + sceneName
                        else:
                            message = downloaded_language + is_forced_string + " subtitles " + action + " from " + downloaded_provider + " with a score of " + unicode(
                                round(subtitle.score * 100 / max_score, 2)) + "% using filename guessing."
                        
                        if use_postprocessing is True:
                            command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                 downloaded_language_code2, downloaded_language_code3,
                                                 subtitle.language.forced)
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
                        
                        # fixme: support multiple languages at once
                        if media_type == 'series':
                            reversed_path = path_replace_reverse(path)
                        else:
                            reversed_path = path_replace_reverse_movie(path)
                        
                        return message, reversed_path, downloaded_language_code2, downloaded_provider, subtitle.score, subtitle.language.forced
        
        if not saved_any:
            logging.debug('BAZARR No subtitles were found for this file: ' + path)
            return None
    
    subliminal.region.backend.sync()
    
    logging.debug('BAZARR Ended searching subtitles for file: ' + path)


def manual_search(path, language, hi, forced, providers, providers_auth, sceneName, title, media_type):
    logging.debug('BAZARR Manually searching subtitles for this file: ' + path)
    
    final_subtitles = []
    
    if hi == "True":
        hi = "force HI"
    else:
        hi = "force non-HI"
    language_set = set()
    
    if forced == "True":
        providers_auth['podnapisi']['only_foreign'] = True
        providers_auth['subscene']['only_foreign'] = True
        providers_auth['opensubtitles']['only_foreign'] = True
    else:
        providers_auth['podnapisi']['only_foreign'] = False
        providers_auth['subscene']['only_foreign'] = False
        providers_auth['opensubtitles']['only_foreign'] = False
    
    for lang in ast.literal_eval(language):
        lang = alpha3_from_alpha2(lang)
        if lang == 'pob':
            lang_obj = Language('por', 'BR')
            if forced == "True":
                lang_obj = Language.rebuild(lang_obj, forced=True)
        else:
            lang_obj = Language(lang)
            if forced == "True":
                lang_obj = Language.rebuild(lang_obj, forced=True)
        language_set.add(lang_obj)
    
    use_scenename = settings.general.getboolean('use_scenename')
    use_mediainfo = settings.general.getboolean('use_mediainfo')
    minimum_score = settings.general.minimum_score
    minimum_score_movie = settings.general.minimum_score_movie
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd
    if providers:
        video = get_video(force_unicode(path), title, sceneName, use_scenename, use_mediainfo, providers=providers,
                          media_type=media_type)
    else:
        logging.info("BAZARR All providers are throttled")
        return None
    if video:
        min_score, max_score, scores = get_scores(video, media_type, min_score_movie_perc=int(minimum_score_movie),
                                                  min_score_series_perc=int(minimum_score))
        
        try:
            if providers:
                subtitles = list_all_subtitles([video], language_set,
                                               providers=providers,
                                               provider_configs=providers_auth,
                                               throttle_callback=provider_throttle,
                                               language_hook=None)  # fixme
            else:
                subtitles = []
                logging.info("BAZARR All providers are throttled")
                return None
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
                
                score = compute_score(matches, s, video, hearing_impaired=hi)
                not_matched = scores - matches
                s.score = score
                
                subtitles_list.append(
                    dict(score=round((score / max_score * 100), 2),
                         language=str(s.language), hearing_impaired=str(s.hearing_impaired),
                         provider=s.provider_name,
                         subtitle=codecs.encode(pickle.dumps(s.make_picklable()), "base64").decode(),
                         url=s.page_link, matches=list(matches), dont_matches=list(not_matched)))
            
            final_subtitles = sorted(subtitles_list, key=lambda x: x['score'], reverse=True)
            logging.debug('BAZARR ' + str(len(final_subtitles)) + " subtitles have been found for this file: " + path)
            logging.debug('BAZARR Ended searching subtitles for this file: ' + path)
    
    subliminal.region.backend.sync()
    
    return final_subtitles


def manual_download_subtitle(path, language, hi, forced, subtitle, provider, providers_auth, sceneName, title,
                             media_type):
    logging.debug('BAZARR Manually downloading subtitles for this file: ' + path)
    
    if settings.general.getboolean('utf8_encode'):
        os.environ["SZ_KEEP_ENCODING"] = ""
    else:
        os.environ["SZ_KEEP_ENCODING"] = "True"
    
    subtitle = pickle.loads(codecs.decode(subtitle.encode(), "base64"))
    use_scenename = settings.general.getboolean('use_scenename')
    use_mediainfo = settings.general.getboolean('use_mediainfo')
    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd
    single = settings.general.getboolean('single_language')
    video = get_video(force_unicode(path), title, sceneName, use_scenename, use_mediainfo, providers={provider},
                      media_type=media_type)
    if video:
        min_score, max_score, scores = get_scores(video, media_type)
        try:
            if provider:
                download_subtitles([subtitle], providers={provider}, provider_configs=providers_auth,
                                   pool_class=provider_pool(), throttle_callback=provider_throttle)
                logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
            else:
                logging.info("BAZARR All providers are throttled")
                return None
        except Exception as e:
            logging.exception('BAZARR Error downloading subtitles for this file ' + path)
            return None
        else:
            if not subtitle.is_valid():
                logging.exception('BAZARR No valid subtitles file found for this file: ' + path)
                return
            logging.debug('BAZARR Subtitles file downloaded for this file:' + path)
            try:
                score = round(subtitle.score / max_score * 100, 2)
                fld = get_target_folder(path)
                chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
                    'win') and settings.general.getboolean('chmod_enabled') else None
                saved_subtitles = save_subtitles(video.original_path, [subtitle], single=single,
                                                 tags=None,  # fixme
                                                 directory=fld,
                                                 chmod=chmod,
                                                 # formats=("srt", "vtt")
                                                 path_decoder=force_unicode)
            
            except Exception as e:
                logging.exception('BAZARR Error saving subtitles file to disk for this file:' + path)
                return
            else:
                if saved_subtitles:
                    for saved_subtitle in saved_subtitles:
                        downloaded_provider = saved_subtitle.provider_name
                        if saved_subtitle.language == 'pt-BR':
                            downloaded_language_code3 = 'pob'
                        else:
                            downloaded_language_code3 = subtitle.language.alpha3
                        downloaded_language = language_from_alpha3(downloaded_language_code3)
                        downloaded_language_code2 = alpha2_from_alpha3(downloaded_language_code3)
                        downloaded_path = saved_subtitle.storage_path
                        logging.debug('BAZARR Subtitles file saved to disk: ' + downloaded_path)
                        is_forced_string = " forced" if subtitle.language.forced else ""
                        message = downloaded_language + is_forced_string + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(
                            score) + "% using manual search."
                        
                        if use_postprocessing is True:
                            command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language,
                                                 downloaded_language_code2, downloaded_language_code3,
                                                 subtitle.language.forced)
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
                        
                        if media_type == 'series':
                            reversed_path = path_replace_reverse(path)
                        else:
                            reversed_path = path_replace_reverse_movie(path)
                        
                        return message, reversed_path, downloaded_language_code2, downloaded_provider, subtitle.score, subtitle.language.forced
                else:
                    logging.error(
                        "BAZARR Tried to manually download a subtitles for file: " + path + " but we weren't able to do (probably throttled by " + str(
                            subtitle.provider_name) + ". Please retry later or select a subtitles from another provider.")
                    return None
    
    subliminal.region.backend.sync()
    
    logging.debug('BAZARR Ended manually downloading subtitles for file: ' + path)


def manual_upload_subtitle(path, language, forced, title, scene_name, media_type, subtitle):
    logging.debug('BAZARR Manually uploading subtitles for this file: ' + path)
    
    single = settings.general.getboolean('single_language')
    
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.getboolean('chmod_enabled') else None

    _, ext = os.path.splitext(subtitle.filename)

    language = alpha3_from_alpha2(language)

    if language == 'pob':
        lang_obj = Language('por', 'BR')
    else:
        lang_obj = Language(language)
    
    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)
    
    subtitle_path = get_subtitle_path(video_path=force_unicode(path), 
                                      language=None if single else lang_obj,
                                      extension=ext,
                                      forced_tag=forced)

    subtitle_path = force_unicode(subtitle_path)

    if os.path.exists(subtitle_path):
        os.remove(subtitle_path)

    subtitle.save(subtitle_path)

    if chmod:
        os.chmod(subtitle_path, chmod)

    message = language_from_alpha3(language) + (" forced" if forced else "") + " subtitles manually uploaded."

    if media_type == 'series':
        reversed_path = path_replace_reverse(path)
    else:
        reversed_path = path_replace_reverse_movie(path)

    return message, reversed_path
    

def series_download_subtitles(no):
    if settings.sonarr.getboolean('only_monitored'):
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""
    
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute(
        'SELECT path, missing_subtitles, sonarrEpisodeId, scene_name FROM table_episodes WHERE sonarrSeriesId = ? AND missing_subtitles != "[]"' + monitored_only_query_string,
        (no,)).fetchall()
    series_details = c_db.execute("SELECT hearing_impaired, title, forced FROM table_shows WHERE sonarrSeriesId = ?",
                                  (no,)).fetchone()
    c_db.close()
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    count_episodes_details = len(episodes_details)
    
    for i, episode in enumerate(episodes_details, 1):
        if providers_list:
            for language in ast.literal_eval(episode[1]):
                if language is not None:
                    notifications.write(msg='Searching for series subtitles...', queue='get_subtitle', item=i,
                                        length=count_episodes_details)
                    result = download_subtitle(path_replace(episode[0]),
                                               str(alpha3_from_alpha2(language.split(':')[0])),
                                               series_details[0],
                                               "True" if len(language.split(':')) > 1 else "False",
                                               providers_list,
                                               providers_auth,
                                               str(episode[3]),
                                               series_details[1],
                                               'series')
                    if result is not None:
                        message = result[0]
                        path = result[1]
                        forced = result[5]
                        language_code = result[2] + ":forced" if forced else result[2]
                        provider = result[3]
                        score = result[4]
                        store_subtitles(path_replace(episode[0]))
                        history_log(1, no, episode[2], message, path, language_code, provider, score)
                        send_notifications(no, episode[2], message)
        else:
            notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
            logging.info("BAZARR All providers are throttled")
            break
    list_missing_subtitles(no)
    
    if count_episodes_details:
        notifications.write(msg='Searching completed. Please reload the page.', type='success', duration='permanent',
                            button='refresh', queue='get_subtitle')


def episode_download_subtitles(no):
    if settings.sonarr.getboolean('only_monitored'):
        monitored_only_query_string = ' AND monitored = "True"'
    else:
        monitored_only_query_string = ""
    
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute(
        'SELECT table_episodes.path, table_episodes.missing_subtitles, table_episodes.sonarrEpisodeId, table_episodes.scene_name, table_shows.hearing_impaired, table_shows.title, table_shows.sonarrSeriesId, table_shows.forced FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.sonarrEpisodeId = ?' + monitored_only_query_string,
        (no,)).fetchall()
    c_db.close()
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    for episode in episodes_details:
        if providers_list:
            for language in ast.literal_eval(episode[1]):
                if language is not None:
                    notifications.write(msg='Searching for ' + str(
                        language_from_alpha2(language)) + ' subtitles for this episode: ' + path_replace(episode[0]),
                                        queue='get_subtitle')
                    result = download_subtitle(path_replace(episode[0]),
                                               str(alpha3_from_alpha2(language.split(':')[0])),
                                               episode[4],
                                               "True" if len(language.split(':')) > 1 else "False",
                                               providers_list,
                                               providers_auth,
                                               str(episode[3]),
                                               episode[5],
                                               'series')
                    if result is not None:
                        message = result[0]
                        path = result[1]
                        forced = result[5]
                        language_code = result[2] + ":forced" if forced else result[2]
                        provider = result[3]
                        score = result[4]
                        store_subtitles(path_replace(episode[0]))
                        history_log(1, episode[6], episode[2], message, path, language_code, provider, score)
                        send_notifications(episode[6], episode[2], message)
                        list_missing_subtitles(episode[6])
        else:
            notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
            logging.info("BAZARR All providers are throttled")
            break


def movies_download_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movie = c_db.execute(
        "SELECT path, missing_subtitles, radarrId, sceneName, hearing_impaired, title, forced FROM table_movies WHERE radarrId = ?",
        (no,)).fetchone()
    c_db.close()
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    count_movie = len(ast.literal_eval(movie[1]))
    
    for i, language in enumerate(ast.literal_eval(movie[1]), 1):
        if providers_list:
            if language is not None:
                notifications.write(msg='Searching for movies subtitles', queue='get_subtitle', item=i,
                                    length=count_movie)
                result = download_subtitle(path_replace_movie(movie[0]),
                                           str(alpha3_from_alpha2(language.split(':')[0])),
                                           movie[4],
                                           "True" if len(language.split(':')) > 1 else "False",
                                           providers_list,
                                           providers_auth,
                                           str(movie[3]),
                                           movie[5],
                                           'movie')
                if result is not None:
                    message = result[0]
                    path = result[1]
                    forced = result[5]
                    language_code = result[2] + ":forced" if forced else result[2]
                    provider = result[3]
                    score = result[4]
                    store_subtitles_movie(path_replace_movie(movie[0]))
                    history_log_movie(1, no, message, path, language_code, provider, score)
                    send_notifications_movie(no, message)
        else:
            notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
            logging.info("BAZARR All providers are throttled")
            break
    list_missing_subtitles_movies(no)
    
    if count_movie:
        notifications.write(msg='Searching completed. Please reload the page.', type='success', duration='permanent',
                            button='refresh', queue='get_subtitle')


def wanted_download_subtitles(path, l, count_episodes):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute(
        "SELECT table_episodes.path, table_episodes.missing_subtitles, table_episodes.sonarrEpisodeId, table_episodes.sonarrSeriesId, table_shows.hearing_impaired, table_episodes.scene_name, table_episodes.failedAttempts, table_shows.title, table_shows.forced FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.path = ? AND missing_subtitles != '[]'",
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
                    if search_active(attempt[i][1]):
                        notifications.write(msg='Searching for series subtitles...', queue='get_subtitle', item=l,
                                            length=count_episodes)
                        result = download_subtitle(path_replace(episode[0]),
                                                   str(alpha3_from_alpha2(language.split(':')[0])),
                                                   episode[4],
                                                   "True" if len(language.split(':')) > 1 else "False",
                                                   providers_list,
                                                   providers_auth,
                                                   str(episode[5]),
                                                   episode[7],
                                                   'series')
                        if result is not None:
                            message = result[0]
                            path = result[1]
                            forced = result[5]
                            language_code = result[2] + ":forced" if forced else result[2]
                            provider = result[3]
                            score = result[4]
                            store_subtitles(path_replace(episode[0]))
                            list_missing_subtitles(episode[3])
                            history_log(1, episode[3], episode[2], message, path, language_code, provider, score)
                            send_notifications(episode[3], episode[2], message)
                    else:
                        logging.debug(
                            'BAZARR Search is not active for episode ' + episode[0] + ' Language: ' + attempt[i][0])


def wanted_download_subtitles_movie(path, l, count_movies):
    conn_db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    movies_details = c_db.execute(
        "SELECT path, missing_subtitles, radarrId, radarrId, hearing_impaired, sceneName, failedAttempts, title, forced FROM table_movies WHERE path = ? AND missing_subtitles != '[]'",
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
                        notifications.write(msg='Searching for movies subtitles...', queue='get_subtitle', item=l,
                                            length=count_movies)
                        result = download_subtitle(path_replace_movie(movie[0]),
                                                   str(alpha3_from_alpha2(language.split(':')[0])),
                                                   movie[4],
                                                   "True" if len(language.split(':')) > 1 else "False",
                                                   providers_list,
                                                   providers_auth,
                                                   str(movie[5]),
                                                   movie[7],
                                                   'movie')
                        if result is not None:
                            message = result[0]
                            path = result[1]
                            forced = result[5]
                            language_code = result[2] + ":forced" if forced else result[2]
                            provider = result[3]
                            score = result[4]
                            store_subtitles_movie(path_replace_movie(movie[0]))
                            list_missing_subtitles_movies(movie[3])
                            history_log_movie(1, movie[3], message, path, language_code, provider, score)
                            send_notifications_movie(movie[3], message)
                    else:
                        logging.info(
                            'BAZARR Search is not active for movie ' + movie[0] + ' Language: ' + attempt[i][0])


def wanted_search_missing_subtitles():
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    db.create_function("path_substitution_movie", 1, path_replace_movie)
    c = db.cursor()
    
    if settings.sonarr.getboolean('only_monitored'):
        monitored_only_query_string_sonarr = ' AND monitored = "True"'
    else:
        monitored_only_query_string_sonarr = ""
    
    if settings.radarr.getboolean('only_monitored'):
        monitored_only_query_string_radarr = ' AND monitored = "True"'
    else:
        monitored_only_query_string_radarr = ""
    
    c.execute(
        "SELECT path_substitution(path) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string_sonarr)
    episodes = c.fetchall()
    
    c.execute(
        "SELECT path_substitution_movie(path) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string_radarr)
    movies = c.fetchall()
    
    c.close()
    if settings.general.getboolean('use_sonarr'):
        
        count_episodes = len(episodes)
        for i, episode in enumerate(episodes, 1):
            providers = get_providers()
            if providers:
                wanted_download_subtitles(episode[0], i, count_episodes)
            else:
                notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
                logging.info("BAZARR All providers are throttled")
                return
    
    if settings.general.getboolean('use_radarr'):
        count_movies = len(movies)
        for i, movie in enumerate(movies, 1):
            providers = get_providers()
            if providers:
                wanted_download_subtitles_movie(movie[0], i, count_movies)
            else:
                notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
                logging.info("BAZARR All providers are throttled")
                return
    
    logging.info('BAZARR Finished searching for missing subtitles. Check histories for more information.')
    
    notifications.write(msg='Searching completed. Please reload the page.', type='success', duration='permanent',
                        button='refresh', queue='get_subtitle')


def search_active(timestamp):
    if settings.general.getboolean('adaptive_searching'):
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


def refine_from_db(path, video):
    if isinstance(video, Episode):
        db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
        c = db.cursor()
        data = c.execute(
            "SELECT table_shows.title, table_episodes.season, table_episodes.episode, table_episodes.title, table_shows.year, table_shows.tvdbId, table_shows.alternateTitles, table_episodes.format, table_episodes.resolution, table_episodes.video_codec, table_episodes.audio_codec FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.path = ?",
            (unicode(path_replace_reverse(path)),)).fetchone()
        db.close()
        if data:
            video.series, year, country = series_re.match(data[0]).groups()
            video.season = int(data[1])
            video.episode = int(data[2])
            video.title = data[3]
            if data[4]:
                if int(data[4]) > 0: video.year = int(data[4])
            video.series_tvdb_id = int(data[5])
            video.alternative_series = ast.literal_eval(data[6])
            if not video.format:
                video.format = str(data[7])
            if not video.resolution:
                video.resolution = str(data[8])
            if not video.video_codec:
                if data[9]: video.video_codec = data[9]
            if not video.audio_codec:
                if data[10]: video.audio_codec = data[10]
    elif isinstance(video, Movie):
        db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
        c = db.cursor()
        data = c.execute(
            "SELECT title, year, alternativeTitles, format, resolution, video_codec, audio_codec, imdbId FROM table_movies WHERE path = ?",
            (unicode(path_replace_reverse_movie(path)),)).fetchone()
        db.close()
        if data:
            video.title = re.sub(r'(\(\d\d\d\d\))', '', data[0])
            if data[1]:
                if int(data[1]) > 0: video.year = int(data[1])
            if data[7]: video.imdb_id = data[7]
            video.alternative_titles = ast.literal_eval(data[2])
            if not video.format:
                if data[3]: video.format = data[3]
            if not video.resolution:
                if data[4]: video.resolution = data[4]
            if not video.video_codec:
                if data[5]: video.video_codec = data[5]
            if not video.audio_codec:
                if data[6]: video.audio_codec = data[6]
    
    return video


def refine_from_mediainfo(path, video):
    if video.fps:
        return
    
    exe = get_binary('mediainfo')
    if not exe:
        logging.debug('BAZARR MediaInfo library not found!')
        return
    else:
        logging.debug('BAZARR MediaInfo library used is %s', exe)
    
    media_info = MediaInfo.parse(path, library_file=exe)
    
    video_track = next((t for t in media_info.tracks if t.track_type == 'Video'), None)
    if not video_track:
        logging.debug('BAZARR MediaInfo was unable to find video tracks in the file!')
        return
    
    logging.debug('MediaInfo found: %s', video_track.to_data())
    
    if not video.fps:
        if video_track.frame_rate:
            video.fps = float(video_track.frame_rate)
        elif video_track.framerate_num and video_track.framerate_den:
            video.fps = round(float(video_track.framerate_num) / float(video_track.framerate_den), 3)


def upgrade_subtitles():
    days_to_upgrade_subs = settings.general.days_to_upgrade_subs
    minimum_timestamp = ((datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                         datetime(1970, 1, 1)).total_seconds()
    
    if settings.general.getboolean('upgrade_manual'):
        query_actions = [1, 2, 3]
    else:
        query_actions = [1, 3]
    
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()
    episodes_list = c.execute("""SELECT table_history.video_path, table_history.language, table_history.score,
                                        table_shows.hearing_impaired, table_episodes.scene_name, table_episodes.title,
                                        table_episodes.sonarrSeriesId, table_episodes.sonarrEpisodeId,
                                        MAX(table_history.timestamp), table_shows.languages, table_shows.forced
                                   FROM table_history
                             INNER JOIN table_shows on table_shows.sonarrSeriesId = table_history.sonarrSeriesId
                             INNER JOIN table_episodes on table_episodes.sonarrEpisodeId = table_history.sonarrEpisodeId
                                  WHERE action IN (""" + ','.join(map(str, query_actions)) + """) AND timestamp > ? AND 
                                        score is not null
                               GROUP BY table_history.video_path, table_history.language""",
                              (minimum_timestamp,)).fetchall()
    movies_list = c.execute("""SELECT table_history_movie.video_path, table_history_movie.language,
                                      table_history_movie.score, table_movies.hearing_impaired, table_movies.sceneName,
                                      table_movies.title, table_movies.radarrId, MAX(table_history_movie.timestamp), 
                                      table_movies.languages, table_movies.forced
                                 FROM table_history_movie
                           INNER JOIN table_movies on table_movies.radarrId = table_history_movie.radarrId
                                WHERE action  IN (""" + ','.join(map(str, query_actions)) + """) AND timestamp > ? AND 
                                      score is not null
                             GROUP BY table_history_movie.video_path, table_history_movie.language""",
                            (minimum_timestamp,)).fetchall()
    db.close()
    
    episodes_to_upgrade = []
    if settings.general.getboolean('use_sonarr'):
        for episode in episodes_list:
            if os.path.exists(path_replace(episode[0])) and int(episode[2]) < 357:
                episodes_to_upgrade.append(episode)
    
    movies_to_upgrade = []
    if settings.general.getboolean('use_radarr'):
        for movie in movies_list:
            if os.path.exists(path_replace_movie(movie[0])) and int(movie[2]) < 117:
                movies_to_upgrade.append(movie)
    
    providers_list = get_providers()
    providers_auth = get_providers_auth()
    
    count_episode_to_upgrade = len(episodes_to_upgrade)
    count_movie_to_upgrade = len(movies_to_upgrade)
    
    if settings.general.getboolean('use_sonarr'):
        for i, episode in enumerate(episodes_to_upgrade, 1):
            providers = get_providers()
            if not providers:
                notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
                logging.info("BAZARR All providers are throttled")
                return
            if episode[9] != "None":
                desired_languages = ast.literal_eval(str(episode[9]))
                if episode[10] == "True":
                    forced_languages = [l + ":forced" for l in desired_languages]
                elif episode[10] == "Both":
                    forced_languages = [l + ":forced" for l in desired_languages] + desired_languages
                else:
                    forced_languages = desired_languages
                
                if episode[1] in forced_languages:
                    notifications.write(msg='Upgrading series subtitles...',
                                        queue='upgrade_subtitle', item=i, length=count_episode_to_upgrade)
                    
                    if episode[1].endswith('forced'):
                        language = episode[1].split(':')[0]
                        is_forced = "True"
                    else:
                        language = episode[1]
                        is_forced = "False"
                    
                    result = download_subtitle(path_replace(episode[0]), str(alpha3_from_alpha2(language)),
                                               episode[3], is_forced, providers_list, providers_auth, str(episode[4]),
                                               episode[5], 'series', forced_minimum_score=int(episode[2]),
                                               is_upgrade=True)
                    if result is not None:
                        message = result[0]
                        path = result[1]
                        forced = result[5]
                        language_code = result[2] + ":forced" if forced else result[2]
                        provider = result[3]
                        score = result[4]
                        store_subtitles(path_replace(episode[0]))
                        history_log(3, episode[6], episode[7], message, path, language_code, provider, score)
                        send_notifications(episode[6], episode[7], message)
    
    if settings.general.getboolean('use_radarr'):
        for i, movie in enumerate(movies_to_upgrade, 1):
            providers = get_providers()
            if not providers:
                notifications.write(msg='BAZARR All providers are throttled', queue='get_subtitle', duration='long')
                logging.info("BAZARR All providers are throttled")
                return
            if movie[8] != "None":
                desired_languages = ast.literal_eval(str(movie[8]))
                if movie[9] == "True":
                    forced_languages = [l + ":forced" for l in desired_languages]
                elif movie[9] == "Both":
                    forced_languages = [l + ":forced" for l in desired_languages] + desired_languages
                else:
                    forced_languages = desired_languages
                
                if movie[1] in forced_languages:
                    notifications.write(msg='Upgrading movie subtitles...',
                                        queue='upgrade_subtitle', item=i, length=count_movie_to_upgrade)
                    
                    if movie[1].endswith('forced'):
                        language = movie[1].split(':')[0]
                        is_forced = "True"
                    else:
                        language = movie[1]
                        is_forced = "False"
                    
                    result = download_subtitle(path_replace_movie(movie[0]), str(alpha3_from_alpha2(language)),
                                               movie[3], is_forced, providers_list, providers_auth, str(movie[4]),
                                               movie[5], 'movie', forced_minimum_score=int(movie[2]), is_upgrade=True)
                    if result is not None:
                        message = result[0]
                        path = result[1]
                        forced = result[5]
                        language_code = result[2] + ":forced" if forced else result[2]
                        provider = result[3]
                        score = result[4]
                        store_subtitles_movie(path_replace_movie(movie[0]))
                        history_log_movie(3, movie[6], message, path, language_code, provider, score)
                        send_notifications_movie(movie[6], message)
