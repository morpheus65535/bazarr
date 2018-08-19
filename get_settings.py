from get_argv import config_dir

import os
import re

import ast
from configparser import ConfigParser

config_file = os.path.normpath(os.path.join(config_dir, 'config/config.ini'))

def get_general_settings():
    cfg = ConfigParser()
    try:
        with open(config_file, 'r') as f:
            cfg.read_file(f)
    except Exception:
        pass

    if cfg.has_section('general'):
        if cfg.has_option('general', 'ip'):
            ip = cfg.get('general', 'ip')
        else:
            ip = '0.0.0.0'

        if cfg.has_option('general', 'port'):
            port = cfg.get('general', 'port')
        else:
            port = '6767'

        if cfg.has_option('general', 'base_url'):
            base_url = cfg.get('general', 'base_url')
        else:
            base_url = '/'

        if cfg.has_option('general', 'path_mappings'):
            path_mappings = cfg.get('general', 'path_mappings')
        else:
            path_mappings = []

        if cfg.has_option('general', 'log_level'):
            log_level = cfg.get('general', 'log_level')
        else:
            log_level = 'INFO'

        if cfg.has_option('general', 'branch'):
            branch = cfg.get('general', 'branch')
        else:
            branch = 'master'

        if cfg.has_option('general', 'auto_update'):
            auto_update = cfg.getboolean('general', 'auto_update')
        else:
            auto_update = True

        if cfg.has_option('general', 'single_language'):
            single_language = cfg.getboolean('general', 'single_language')
        else:
            single_language = False

        if cfg.has_option('general', 'minimum_score'):
            minimum_score = cfg.get('general', 'minimum_score')
        else:
            minimum_score = '0'

        if cfg.has_option('general', 'use_scenename'):
            use_scenename = cfg.getboolean('general', 'use_scenename')
        else:
            use_scenename = False

        if cfg.has_option('general', 'use_postprocessing'):
            use_postprocessing = cfg.getboolean('general', 'use_postprocessing')
        else:
            use_postprocessing = False

        if cfg.has_option('general', 'postprocessing_cmd'):
            postprocessing_cmd = cfg.get('general', 'postprocessing_cmd')
        else:
            postprocessing_cmd = ''

        if cfg.has_option('general', 'use_sonarr'):
            use_sonarr = cfg.getboolean('general', 'use_sonarr')
        else:
            use_sonarr = False

        if cfg.has_option('general', 'use_radarr'):
            use_radarr = cfg.getboolean('general', 'use_radarr')
        else:
            use_radarr = False

        if cfg.has_option('general', 'path_mappings_movie'):
            path_mappings_movie = cfg.get('general', 'path_mappings_movie')
        else:
            path_mappings_movie = []

        if cfg.has_option('general', 'serie_default_enabled'):
            serie_default_enabled = cfg.getboolean('general', 'serie_default_enabled')
        else:
            serie_default_enabled = False

        if cfg.has_option('general', 'serie_default_language'):
            serie_default_language = cfg.get('general', 'serie_default_language')
        else:
            serie_default_language = []

        if cfg.has_option('general', 'serie_default_hi'):
            serie_default_hi = cfg.getboolean('general', 'serie_default_hi')
        else:
            serie_default_hi = False

        if cfg.has_option('general', 'movie_default_enabled'):
                movie_default_enabled = cfg.getboolean('general', 'movie_default_enabled')
        else:
            movie_default_enabled = False

        if cfg.has_option('general', 'movie_default_language'):
            movie_default_language = cfg.get('general', 'movie_default_language')
        else:
            movie_default_language = []

        if cfg.has_option('general', 'movie_default_hi'):
            movie_default_hi = cfg.getboolean('general', 'movie_default_hi')
        else:
            movie_default_hi = False

        if cfg.has_option('general', 'page_size'):
            page_size = cfg.get('general', 'page_size')
        else:
            page_size = '25'

        if cfg.has_option('general', 'minimum_score_movie'):
            minimum_score_movie = cfg.get('general', 'minimum_score_movie')
        else:
            minimum_score_movie = '0'

        if cfg.has_option('general', 'use_embedded_subs'):
            use_embedded_subs = cfg.getboolean('general', 'use_embedded_subs')
        else:
            use_embedded_subs = False

        if cfg.has_option('general', 'only_monitored'):
            only_monitored = cfg.getboolean('general', 'only_monitored')
        else:
            only_monitored = False

        if cfg.has_option('general', 'configured'):
            configured = cfg.getboolean('general', 'configured')
        else:
            configured = '0'

        if cfg.has_option('general', 'updated'):
            updated = cfg.getboolean('general', 'updated')
        else:
            updated = '0'
    else:
        ip = '0.0.0.0'
        port = '6768'
        base_url = '/'
        path_mappings = []
        log_level = 'INFO'
        branch = 'master'
        auto_update = True
        single_language = False
        minimum_score = '0'
        use_scenename = False
        use_postprocessing = False
        postprocessing_cmd = False
        use_sonarr = False
        use_radarr = False
        path_mappings_movie = []
        serie_default_enabled = False
        serie_default_language = []
        serie_default_hi = False
        movie_default_enabled = False
        movie_default_language = []
        movie_default_hi = False
        page_size = '25'
        minimum_score_movie = '0'
        use_embedded_subs = False
        only_monitored = False
        configured = '0'
        updated = '0'

    return [ip, port, base_url, path_mappings, log_level, branch, auto_update, single_language, minimum_score, use_scenename, use_postprocessing, postprocessing_cmd, use_sonarr, use_radarr, path_mappings_movie, serie_default_enabled, serie_default_language, serie_default_hi, movie_default_enabled,movie_default_language, movie_default_hi, page_size, minimum_score_movie, use_embedded_subs, only_monitored, configured, updated]


def get_auth_settings():
    cfg = ConfigParser()
    try:
        with open(config_file, 'r') as f:
            cfg.read_file(f)
    except Exception:
        pass

    if cfg.has_section('auth'):
        if cfg.has_option('auth', 'enabled'):
            enabled = cfg.getboolean('auth', 'enabled')
        else:
            enabled = False

        if cfg.has_option('auth', 'username'):
            username = cfg.get('auth', 'username')
        else:
            username = ''

        if cfg.has_option('auth', 'password'):
            password = cfg.get('auth', 'password')
        else:
            password = ''
    else:
        enabled = False
        username = ''
        password = ''

    return [enabled, username, password]


def get_sonarr_settings():
    cfg = ConfigParser()
    try:
        with open(config_file, 'r') as f:
            cfg.read_file(f)
    except Exception:
        pass

    if cfg.has_section('sonarr'):
        if cfg.has_option('sonarr', 'ip'):
            ip = cfg.get('sonarr', 'ip')
        else:
            ip = '127.0.0.1'

        if cfg.has_option('sonarr', 'port'):
            port = cfg.get('sonarr', 'port')
        else:
            port = '8989'

        if cfg.has_option('sonarr', 'base_url'):
            base_url = cfg.get('sonarr', 'base_url')
        else:
            base_url = '/'

        if cfg.has_option('sonarr', 'ssl'):
            ssl = cfg.get('sonarr', 'ssl')
        else:
            ssl = False

        if cfg.has_option('sonarr', 'apikey'):
            apikey = cfg.get('sonarr', 'apikey')
        else:
            apikey = ''

        if cfg.has_option('sonarr', 'full_update'):
            full_update = cfg.get('sonarr', 'full_update')
        else:
            full_update = 'Dayly'
    else:
        ip = '127.0.0.1'
        port = '8989'
        base_url = '/'
        ssl = False
        apikey = ''
        full_update = 'Daily'

    if ssl == 1:
        protocol_sonarr = "https"
    else:
        protocol_sonarr = "http"

    if base_url == None:
        base_url = "/"
    if base_url.startswith("/") == False:
        base_url = "/" + base_url
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    url_sonarr = protocol_sonarr + "://" + ip + ":" + port + base_url
    url_sonarr_short = protocol_sonarr + "://" + ip + ":" + port



    return [ip, port, base_url, ssl, apikey, full_update, url_sonarr, url_sonarr_short]


def get_radarr_settings():
    cfg = ConfigParser()
    try:
        with open(config_file, 'r') as f:
            cfg.read_file(f)
    except Exception:
        pass

    if cfg.has_section('radarr'):
        if cfg.has_option('radarr', 'ip'):
            ip = cfg.get('radarr', 'ip')
        else:
            ip = '127.0.0.1'

        if cfg.has_option('radarr', 'port'):
            port = cfg.get('radarr', 'port')
        else:
            port = '7878'

        if cfg.has_option('radarr', 'base_url'):
            base_url = cfg.get('radarr', 'base_url')
        else:
            base_url = '/'

        if cfg.has_option('radarr', 'ssl'):
            ssl = cfg.get('radarr', 'ssl')
        else:
            ssl = False

        if cfg.has_option('radarr', 'apikey'):
            apikey = cfg.get('radarr', 'apikey')
        else:
            apikey = ''

        if cfg.has_option('radarr', 'full_update'):
            full_update = cfg.get('radarr', 'full_update')
        else:
            full_update = 'Dayly'
    else:
        ip = '127.0.0.1'
        port = '8989'
        base_url = '/'
        ssl = False
        apikey = ''
        full_update = 'Daily'

    if ssl == 1:
        protocol_radarr = "https"
    else:
        protocol_radarr = "http"

    if base_url is None:
        base_url = "/"
    if base_url.startswith("/") is False:
        base_url = "/" + base_url
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    url_radarr = protocol_radarr + "://" + ip + ":" + port + base_url
    url_radarr_short = protocol_radarr + "://" + ip + ":" + port

    return [ip, port, base_url, ssl, apikey, full_update, url_radarr , url_radarr_short]



def path_replace(path):
    for path_mapping in path_mappings:
        if path_mapping[0] in path:
            path = path.replace(path_mapping[0], path_mapping[1])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

def path_replace_reverse(path):
    for path_mapping in path_mappings:
        if path_mapping[1] in path:
            path = path.replace(path_mapping[1], path_mapping[0])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

def path_replace_movie(path):
    for path_mapping in path_mappings_movie:
        if path_mapping[0] in path:
            path = path.replace(path_mapping[0], path_mapping[1])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path

def path_replace_reverse_movie(path):
    for path_mapping in path_mappings_movie:
        if path_mapping[1] in path:
            path = path.replace(path_mapping[1], path_mapping[0])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
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
path_mappings = ast.literal_eval(result[3])
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
path_mappings_movie = ast.literal_eval(result[14])
serie_default_enabled = result[15]
serie_default_language = result[16]
serie_default_hi = result[17]
movie_default_enabled = result[18]
movie_default_language = result[19]
movie_default_hi = result[20]
page_size = result[21]
minimum_score_movie = result[22]
use_embedded_subs = result[23]
only_monitored = result[24]
configured = result[25]
updated = result[26]