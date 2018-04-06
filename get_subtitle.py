import os
import sqlite3
import ast
import logging
import subprocess
from babelfish import *
from subliminal import *
from pycountry import *
from bs4 import UnicodeDammit
from get_general_settings import *
from list_subtitles import *
from utils import *
from notifier import send_notifications

# configure the cache
region.configure('dogpile.cache.memory')

def download_subtitle(path, language, hi, providers, providers_auth, sceneName):
    minimum_score = float(get_general_settings()[8]) / 100 * 359
    use_scenename = get_general_settings()[9]
    use_postprocessing = get_general_settings()[10]
    postprocessing_cmd = get_general_settings()[11]
    try:
        if sceneName is None or use_scenename == "False":
            used_sceneName = False
            video = scan_video(path)
        else:
            used_sceneName = True
            video = Video.fromname(sceneName)
    except Exception as e:
        logging.exception('Error trying to extract information from this filename: ' + path)
        return None
    else:
        try:
            best_subtitles = download_best_subtitles([video], {Language(language)}, providers=providers, min_score=minimum_score, hearing_impaired=hi, provider_configs=providers_auth)
        except Exception as e:
            logging.exception('Error trying to get the best subtitles for this file: ' + path)
            return None
        else:
            try:
                best_subtitle = best_subtitles[video][0]
            except:
                logging.debug('No subtitles found for ' + path)
                return None
            else:
                single = get_general_settings()[7]
                try:
                    score = round(float(compute_score(best_subtitle, video)) / 359 * 100, 2)
                    if used_sceneName == True:
                        video = scan_video(path)
                    if single == 'True':
                        result = save_subtitles(video, [best_subtitle], single=True, encoding='utf-8')
                    else:
                        result = save_subtitles(video, [best_subtitle], encoding='utf-8')
                except:
                    logging.error('Error saving subtitles file to disk.')
                    return None
                else:
                    downloaded_provider = str(result[0][0]).strip('<>').split(' ')[0][:-8]
                    downloaded_language = pycountry.languages.lookup(str(str(result[0][0]).strip('<>').split(' ')[2].strip('[]'))).name
                    downloaded_language_code2 = pycountry.languages.lookup(downloaded_language).alpha_2
                    downloaded_language_code3 = pycountry.languages.lookup(downloaded_language).alpha_3
                    downloaded_path = result[1]
                    if used_sceneName == True:
                        message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(score) + "% using this scene name obtained from Sonarr: " + sceneName
                    else:
                        message = downloaded_language + " subtitles downloaded from " + downloaded_provider + " with a score of " + unicode(score) + "% using filename guessing."

                    if use_postprocessing == "True":
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
                                logging.error('Post-processing result for file ' + path + ' : Nothing returned from command execution')
                            else:
                                logging.error('Post-processing result for file ' + path + ' : ' + out)
                        else:
                            if out == "":
                                logging.info('Post-processing result for file ' + path + ' : Nothing returned from command execution')
                            else:
                                logging.info('Post-processing result for file ' + path + ' : ' + out)

                    return message

def series_download_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute("SELECT path, missing_subtitles, sonarrEpisodeId, scene_name FROM table_episodes WHERE sonarrSeriesId = ?", (no,)).fetchall()
    series_details = c_db.execute("SELECT hearing_impaired FROM table_shows WHERE sonarrSeriesId = ?", (no,)).fetchone()
    enabled_providers = c_db.execute("SELECT * FROM table_settings_providers WHERE enabled = 1").fetchall()
    c_db.close()
    
    providers_list = []
    providers_auth = {}
    if len(enabled_providers) > 0:
        for provider in enabled_providers:
            providers_list.append(provider[0])
            try:
                if provider[2] is not '' and provider[3] is not '':
                    provider_auth = providers_auth.append(provider[0])
                    provider_auth.update({'username':providers[2], 'password':providers[3]})
                else:
                    providers_auth = None
            except:
                providers_auth = None
    else:
        providers_list = None
        providers_auth = None
            
    for episode in episodes_details:
        for language in ast.literal_eval(episode[1]):
            message = download_subtitle(path_replace(episode[0]), str(pycountry.languages.lookup(language).alpha_3), series_details[0], providers_list, providers_auth, episode[3])
            if message is not None:
                store_subtitles(path_replace(episode[0]))
                history_log(1, no, episode[2], message)
                send_notifications(no, episode[2], message)
    list_missing_subtitles(no)

def wanted_download_subtitles(path):
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute("SELECT table_episodes.path, table_episodes.missing_subtitles, table_episodes.sonarrEpisodeId, table_episodes.sonarrSeriesId, table_shows.hearing_impaired, table_episodes.scene_name FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.path = ? AND missing_subtitles != '[]'", (path_replace_reverse(path),)).fetchall()
    enabled_providers = c_db.execute("SELECT * FROM table_settings_providers WHERE enabled = 1").fetchall()
    c_db.close()

    providers_list = []
    providers_auth = {}
    if len(enabled_providers) > 0:
        for provider in enabled_providers:
            providers_list.append(provider[0])
            try:
                if provider[2] is not '' and provider[3] is not '':
                    provider_auth = providers_auth.append(provider[0])
                    provider_auth.update({'username':providers[2], 'password':providers[3]})
                else:
                    providers_auth = None
            except:
                providers_auth = None
    else:
        providers_list = None
        providers_auth = None
        
    for episode in episodes_details:
        for language in ast.literal_eval(episode[1]):
            message = download_subtitle(path_replace(episode[0]), str(pycountry.languages.lookup(language).alpha_3), episode[4], providers_list, providers_auth, episode[5])
            if message is not None:
                store_subtitles(path_replace(episode[0]))
                list_missing_subtitles(episode[3])
                history_log(1, episode[3], episode[2], message)
                send_notifications(episode[3], episode[2], message)

def wanted_search_missing_subtitles():
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    db.create_function("path_substitution", 1, path_replace)
    c = db.cursor()

    c.execute("SELECT path_substitution(path) FROM table_episodes WHERE table_episodes.missing_subtitles != '[]'")
    data = c.fetchall()
    c.close()

    for episode in data:
        wanted_download_subtitles(episode[0])

    logging.info('Finished searching for missing subtitles. Check history for more information.')
