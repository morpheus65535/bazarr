# coding=utf-8
# pylama:ignore=W0611
# TODO unignore and fix W0611

import ast
import os
import re
import logging

from charamel import Detector
from bs4 import UnicodeDammit

from config import settings, get_array_from


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, episode_language, episode_language_code2, episode_language_code3, forced, score, subtitle_id, provider, series_id, episode_id, hi):
    if hi:
        modifier_string = " HI"
    elif forced:
        modifier_string = " forced"
    else:
        modifier_string = ""

    if hi:
        modifier_code = ":hi"
        modifier_code_dot = ".hi"
    elif forced:
        modifier_code = ":forced"
        modifier_code_dot = ".forced"
    else:
        modifier_code = ""
        modifier_code_dot = ""

    pp_command = pp_command.replace('{{directory}}', os.path.dirname(episode))
    pp_command = pp_command.replace('{{episode}}', episode)
    pp_command = pp_command.replace('{{episode_name}}', os.path.splitext(os.path.basename(episode))[0])
    pp_command = pp_command.replace('{{subtitles}}', str(subtitles))
    pp_command = pp_command.replace('{{subtitles_language}}', str(language))
    pp_command = pp_command.replace('{{subtitles_language_code2}}', str(language_code2))
    pp_command = pp_command.replace('{{subtitles_language_code3}}', str(language_code3))
    pp_command = pp_command.replace('{{subtitles_language_code2_dot}}', str(language_code2).replace(':', '.'))
    pp_command = pp_command.replace('{{subtitles_language_code3_dot}}', str(language_code3).replace(':', '.'))
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
