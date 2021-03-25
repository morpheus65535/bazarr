# coding=utf-8

import ast
import os
import re
import logging

from charamel import Detector
from bs4 import UnicodeDammit

from config import settings, get_array_from


class PathMappings:
    def __init__(self):
        self.path_mapping_series = []
        self.path_mapping_movies = []

    def update(self):
        self.path_mapping_series = [x for x in get_array_from(settings.general.path_mappings) if x[0] != x[1]]
        self.path_mapping_movies = [x for x in get_array_from(settings.general.path_mappings_movie) if x[0] != x[1]]

    def path_replace(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_series:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[0] in path:
                path = path.replace(path_mapping[0], path_mapping[1])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path

    def path_replace_reverse(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_series:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[1] in path:
                path = path.replace(path_mapping[1], path_mapping[0])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path

    def path_replace_movie(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_movies:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[0] in path:
                path = path.replace(path_mapping[0], path_mapping[1])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path

    def path_replace_reverse_movie(self, path):
        if path is None:
            return None

        for path_mapping in self.path_mapping_movies:
            if path_mapping[0] == path_mapping[1]:
                continue
            if '' in path_mapping:
                continue
            if path_mapping[1] in path:
                path = path.replace(path_mapping[1], path_mapping[0])
                if path.startswith('\\\\') or re.match(r'^[a-zA-Z]:\\', path):
                    path = path.replace('/', '\\')
                elif path.startswith('/'):
                    path = path.replace('\\', '/')
                break
        return path


path_mappings = PathMappings()


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, episode_language, episode_language_code2, episode_language_code3, forced, score, subtitle_id, provider, series_id, episode_id):
    is_forced = ":forced" if forced else ""
    is_forced_string = " forced" if forced else ""
    pp_command = pp_command.replace('{{directory}}', os.path.dirname(episode))
    pp_command = pp_command.replace('{{episode}}', episode)
    pp_command = pp_command.replace('{{episode_name}}', os.path.splitext(os.path.basename(episode))[0])
    pp_command = pp_command.replace('{{subtitles}}', str(subtitles))
    pp_command = pp_command.replace('{{subtitles_language}}', str(language) + is_forced_string)
    pp_command = pp_command.replace('{{subtitles_language_code2}}', str(language_code2) + is_forced)
    pp_command = pp_command.replace('{{subtitles_language_code3}}', str(language_code3) + is_forced)
    pp_command = pp_command.replace('{{episode_language}}', str(episode_language))
    pp_command = pp_command.replace('{{episode_language_code2}}', str(episode_language_code2))
    pp_command = pp_command.replace('{{episode_language_code3}}', str(episode_language_code3))
    pp_command = pp_command.replace('{{score}}', str(score))
    pp_command = pp_command.replace('{{subtitle_id}}', str(subtitle_id))
    pp_command = pp_command.replace('{{provider}}', str(provider))
    pp_command = pp_command.replace('{{series_id}}', str(series_id))
    pp_command = pp_command.replace('{{episode_id}}', str(episode_id))
    return pp_command


def get_subtitle_destination_folder():
    fld_custom = str(settings.general.subfolder_custom).strip() if (settings.general.subfolder_custom and
                                                                    settings.general.subfolder != 'current') else None
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
            detector = Detector()
            t = detector.detect(s)
            try:
                s = s.decode(t)
            except UnicodeDecodeError:
                s = UnicodeDammit(s).unicode_markup
    return s
