# coding=utf-8
from __future__ import absolute_import
import ast
import os
import re
import types
import logging
import operator

import libs

import chardet
from bs4 import UnicodeDammit
from collections import OrderedDict

from config import settings
from utils import get_sonarr_platform, get_radarr_platform


def sonarr_path_mapping_regex():
    global path_mapping
    global sonarr_regex
    global sonarr_use_path_mapping

    path_mapping = ast.literal_eval(settings.general.path_mappings)
    path_mapping = sorted(path_mapping, key=operator.itemgetter(0), reverse=True)
    path_mapping = OrderedDict((mapping[0], mapping[1]) for mapping in path_mapping if mapping[0] != '')
    if any(item for sublist in path_mapping for item in sublist):
        sonarr_use_path_mapping = True
        sonarr_regex = re.compile("|".join(path_mapping.keys()))
    else:
        sonarr_use_path_mapping = False


def sonarr_path_mapping_reverse_regex():
    global sonarr_platform
    global path_mapping_reverse
    global sonarr_reverse_regex
    global sonarr_use_path_mapping

    sonarr_platform = get_sonarr_platform()

    path_mapping_reverse = ast.literal_eval(settings.general.path_mappings)
    path_mapping_reverse = sorted(path_mapping_reverse, key=operator.itemgetter(0), reverse=True)
    path_mapping_reverse = OrderedDict((mapping[1], mapping[0]) for mapping in path_mapping_reverse if mapping[0] != '')
    if any(item for sublist in path_mapping_reverse for item in sublist):
        sonarr_use_path_mapping = True
        sonarr_reverse_regex = re.compile("|".join(map(re.escape, path_mapping_reverse.keys())))
    else:
        sonarr_use_path_mapping = False


def radarr_path_mapping_regex():
    global path_mapping_movie
    global radarr_regex
    global radarr_use_path_mapping

    path_mapping_movie = ast.literal_eval(settings.general.path_mappings_movie)
    path_mapping_movie = sorted(path_mapping_movie, key=operator.itemgetter(0), reverse=True)
    path_mapping_movie = OrderedDict((mapping[0], mapping[1]) for mapping in path_mapping_movie if mapping[0] != '')
    if any(item for sublist in path_mapping_movie for item in sublist):
        radarr_use_path_mapping = True
        radarr_regex = re.compile("|".join(path_mapping_movie.keys()))
    else:
        radarr_use_path_mapping = False


def radarr_path_mapping_reverse_regex():
    global radarr_platform
    global path_mapping_reverse_movie
    global radarr_reverse_regex
    global radarr_use_path_mapping

    radarr_platform = get_sonarr_platform()

    path_mapping_reverse_movie = ast.literal_eval(settings.general.path_mappings)
    path_mapping_reverse_movie = sorted(path_mapping_reverse_movie, key=operator.itemgetter(0), reverse=True)
    path_mapping_reverse_movie = OrderedDict((mapping[1], mapping[0]) for mapping in path_mapping_reverse_movie if mapping[0] != '')
    if any(item for sublist in path_mapping_reverse_movie for item in sublist):
        radarr_use_path_mapping = True
        radarr_reverse_regex = re.compile("|".join(map(re.escape, path_mapping_reverse_movie.keys())))
    else:
        radarr_use_path_mapping = False


def path_replace(path):
    if path is None or sonarr_use_path_mapping is False:
        return path

    reverted_path = sonarr_regex.sub(lambda match: path_mapping[match.group(0)], path, count=1)

    from os.path import normpath

    return normpath(reverted_path)


def path_replace_reverse(path):
    if path is None or sonarr_use_path_mapping is False:
        return path

    reverted_path_temp = sonarr_reverse_regex.sub(lambda match: path_mapping_reverse[match.group(0)], path, count=1)

    if sonarr_platform == 'posix':
        from posixpath import normpath
        reverted_path = reverted_path_temp.replace('\\', '/')
    elif sonarr_platform == 'nt':
        from ntpath import normpath
        reverted_path = reverted_path_temp.replace('/', '\\')

    return normpath(reverted_path)


def path_replace_movie(path):
    if path is None or radarr_use_path_mapping is False:
        return None

    reverted_path = radarr_regex.sub(lambda match: path_mapping_movie[match.group(0)], path, count=1)

    from os.path import normpath

    return normpath(reverted_path)


def path_replace_reverse_movie(path):
    if path is None or radarr_use_path_mapping is False:
        return path

    reverted_path_temp = radarr_reverse_regex.sub(lambda match: path_mapping_reverse_movie[match.group(0)], path, count=1)

    if radarr_platform == 'posix':
        from posixpath import normpath
        reverted_path = reverted_path_temp.replace('\\', '/')
    elif radarr_platform == 'nt':
        from ntpath import normpath
        reverted_path = reverted_path_temp.replace('/', '\\')

    return normpath(reverted_path)


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, forced):
    is_forced = ":forced" if forced else ""
    is_forced_string = " forced" if forced else ""
    pp_command = pp_command.replace('{{directory}}', os.path.dirname(episode))
    pp_command = pp_command.replace('{{episode}}', episode)
    pp_command = pp_command.replace('{{episode_name}}', os.path.splitext(os.path.basename(episode))[0])
    pp_command = pp_command.replace('{{subtitles}}', subtitles)
    pp_command = pp_command.replace('{{subtitles_language}}', language + is_forced_string)
    pp_command = pp_command.replace('{{subtitles_language_code2}}', language_code2 + is_forced)
    pp_command = pp_command.replace('{{subtitles_language_code3}}', language_code3 + is_forced)
    return pp_command


def get_subtitle_destination_folder():
    fld_custom = str(settings.general.subfolder_custom).strip() if settings.general.subfolder_custom else None
    return fld_custom


def get_target_folder(file_path):
    subfolder = settings.general.subfolder
    fld_custom = str(settings.general.subfolder_custom).strip() \
        if settings.general.subfolder_custom else None
    
    if subfolder != "current" and fld_custom:
        # specific subFolder requested, create it if it doesn't exist
        fld_base = os.path.split(file_path)[0]
        
        if subfolder == "absolute":
            # absolute folder
            fld = fld_custom
        elif subfolder == "relative":
            fld = os.path.join(fld_base, fld_custom)
        else:
            fld = None
        
        fld = force_unicode(fld)
        
        if not os.path.isdir(fld):
            try:
                os.makedirs(fld)
            except Exception as e:
                logging.error('BAZARR is unable to create directory to save subtitles: ' + fld)
                fld = None
    else:
        fld = None
    
    return fld


def force_unicode(s):
    """
    Ensure a string is unicode, not encoded; used for enforcing file paths to be unicode upon saving a subtitle,
    to prevent encoding issues when saving a subtitle to a non-ascii path.
    :param s: string
    :return: unicode string
    """
    if not isinstance(s, str):
        try:
            s = s.decode("utf-8")
        except UnicodeDecodeError:
            t = chardet.detect(s)
            try:
                s = s.decode(t["encoding"])
            except UnicodeDecodeError:
                s = UnicodeDammit(s).unicode_markup
    return s


sonarr_path_mapping_regex()
sonarr_path_mapping_reverse_regex()
radarr_path_mapping_regex()
radarr_path_mapping_reverse_regex()
