# coding=utf-8
import ast
import os
import re
import types
import logging
import chardet
from bs4 import UnicodeDammit

from config import settings


def path_replace(path):
    if path is None:
        return None

    for path_mapping in ast.literal_eval(settings.general.path_mappings):
        if path_mapping[0] in path:
            path = path.replace(path_mapping[0], path_mapping[1])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path


def path_replace_reverse(path):
    if path is None:
        return None

    for path_mapping in ast.literal_eval(settings.general.path_mappings):
        if path_mapping[1] in path:
            path = path.replace(path_mapping[1], path_mapping[0])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path


def path_replace_movie(path):
    if path is None:
        return None

    for path_mapping in ast.literal_eval(settings.general.path_mappings_movie):
        if path_mapping[0] in path:
            path = path.replace(path_mapping[0], path_mapping[1])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path


def path_replace_reverse_movie(path):
    if path is None:
        return None

    for path_mapping in ast.literal_eval(settings.general.path_mappings_movie):
        if path_mapping[1] in path:
            path = path.replace(path_mapping[1], path_mapping[0])
            if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                path = path.replace('/', '\\')
            elif path.startswith('/'):
                path = path.replace('\\', '/')
            break
    return path


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
    if not isinstance(s, types.UnicodeType):
        try:
            s = s.decode("utf-8")
        except UnicodeDecodeError:
            t = chardet.detect(s)
            try:
                s = s.decode(t["encoding"])
            except UnicodeDecodeError:
                s = UnicodeDammit(s).unicode_markup
    return s
