# coding=utf-8
import ast
import os
import re

from config import settings


def path_replace(path):
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
    for path_mapping in ast.literal_eval(settings.general.path_mappings_movie):
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
