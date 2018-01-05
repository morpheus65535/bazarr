import os
import sqlite3
import ast
import logging
from babelfish import *
from subliminal import *
from pycountry import *
from get_general_settings import *
from list_subtitles import *
from utils import *

# configure the cache
if os.name == 'nt':
    region.configure('dogpile.cache.memory')
else:
    region.configure('dogpile.cache.dbm', arguments={'filename': os.path.join(os.path.dirname(__file__), 'data/cache/cachefile.dbm')})

def download_subtitle(path, language, hi, providers, providers_auth):
    try:
        video = scan_video(path)
    except Exception as e:
        logging.exception('Error trying to extract information from this filename: ' + path)
        return None
    else:
        try:
            best_subtitles = download_best_subtitles([video], {Language(language)}, providers=providers, hearing_impaired=hi, provider_configs=providers_auth)
        except Exception as e:
            logging.exception('Error trying to best subtitles for this file: ' + path)
            return None
        else:
            try:
            	best_subtitle = best_subtitles[video][0]
        	except:
        		return None
            
            else:
            	try:
            		result = save_subtitles(video, [best_subtitle], encoding='utf-8')
            	except:
            		logging.error('Error saving subtitles file to disk.')
            		return None
	            else:
	            	downloaded_provider = str(result[0]).strip('<>').split(' ')[0][:-8]
		            downloaded_language = pycountry.languages.lookup(str(str(result[0]).strip('<>').split(' ')[2].strip('[]'))).name
		            message = downloaded_language + " subtitles downloaded from " + downloaded_provider + "."
		        
		            return message

def series_download_subtitles(no):
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute("SELECT path, missing_subtitles, sonarrEpisodeId FROM table_episodes WHERE sonarrSeriesId = ?", (no,)).fetchall()
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
            message = download_subtitle(path_replace(episode[0]), str(pycountry.languages.lookup(language).alpha_3), series_details[0], providers_list, providers_auth)
            if message is not None:
                store_subtitles(path_replace(episode[0]))
                history_log(1, no, episode[2], message)
    list_missing_subtitles(no)

def wanted_download_subtitles(path):
    conn_db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c_db = conn_db.cursor()
    episodes_details = c_db.execute("SELECT table_episodes.path, table_episodes.missing_subtitles, table_episodes.sonarrEpisodeId, table_episodes.sonarrSeriesId, table_shows.hearing_impaired FROM table_episodes INNER JOIN table_shows on table_shows.sonarrSeriesId = table_episodes.sonarrSeriesId WHERE table_episodes.path = ? AND missing_subtitles != '[]'", (path_replace_reverse(path),)).fetchall()
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
            message = download_subtitle(path_replace(episode[0]), str(pycountry.languages.lookup(language).alpha_3), episode[4], providers_list, providers_auth)
            if message is not None:
                store_subtitles(path_replace(episode[0]))
                list_missing_subtitles(episode[3])
                history_log(1, episode[3], episode[2], message)

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
