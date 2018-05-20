import sqlite3
import os
import ast

def get_general_settings():
    # Open database connection
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Get general settings from database table
    c.execute("SELECT * FROM table_settings_general")
    general_settings = c.fetchone()

    # Close database connection
    db.close()

    ip = general_settings[0]
    port = general_settings[1]
    base_url = general_settings[2]
    if base_url == (''):
        base_url = '/'
    if general_settings[3] is None:
       path_mappings = []
    else:
       path_mappings = ast.literal_eval(general_settings[3])
    log_level = general_settings[4]
    branch = general_settings[5]
    automatic = general_settings[6]
    single_language = general_settings[9]
    minimum_score = general_settings[10]
    use_scenename = general_settings[11]
    use_postprocessing = general_settings[12]
    postprocessing_cmd = general_settings[13]
    use_sonarr = general_settings[14]
    use_radarr = general_settings[15]

    return [ip, port, base_url, path_mappings, log_level, branch, automatic, single_language, minimum_score, use_scenename, use_postprocessing, postprocessing_cmd, use_sonarr, use_radarr]

def path_replace(path):
    for path_mapping in path_mappings:
        if path_mapping[0] in path:
            path = path.replace(path_mapping[0], path_mapping[1])
            if path.startswith('\\\\'):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

def path_replace_reverse(path):
    for path_mapping in path_mappings:
        if path_mapping[1] in path:
            path = path.replace(path_mapping[1], path_mapping[0])
            if path.startswith('\\\\'):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3):
    pp_command = pp_command.replace('{{directory}}', os.path.dirname(episode))
    pp_command = pp_command.replace('{{episode}}', episode)
    pp_command = pp_command.replace('{{episode_name}}', os.path.splitext(os.path.basename(episode))[0])
    pp_command = pp_command.replace('{{subtitles}}', subtitles)
    pp_command = pp_command.replace('{{subtitles_language}}', language)
    pp_command = pp_command.replace('{{subtitles_language_code2}}', language_code2)
    pp_command = pp_command.replace('{{subtitles_language_code3}}', language_code3)
    return pp_command

result = get_general_settings()
ip = result[0]
port = result[1]
base_url = result[2]
path_mappings = result[3]
log_level = result[4]
branch = result[5]
automatic = result[6]
single_language = result[7]
minimum_score = result[8]
use_scenename = result[9]
use_processing = result[10]
postprocessing_cmd = result[11]
use_sonarr = result[12]
use_radarr = result[13]