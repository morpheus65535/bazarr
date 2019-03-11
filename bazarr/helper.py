# coding=utf-8
import ast
import os
import re
import types
import logging
import sqlite3

from config import settings
from get_args import args
from get_languages import alpha2_from_language


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


def get_subtitle_destination_folder():
    fld_custom = str(settings.general.subfolder_custom).strip() if settings.general.subfolder_custom else None
    return fld_custom or (
        settings.general.subfolder if settings.general.subfolder != "current" else None)


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


def upgrade_history():
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    data = c.execute('SELECT sonarrEpisodeId, video_path, description, ROWID FROM table_history WHERE action = 1').fetchall()

    for row in data:
        if row[1] is None:
            path = c.execute('SELECT path FROM table_episodes WHERE sonarrEpisodeId = ?', (row[0],)).fetchone()
            c.execute('UPDATE table_history SET video_path = ? WHERE sonarrEpisodeId = ?', (path[0], row[0]))

            values = re.split(r' subtitles downloaded from | with a score of | using', row[2])[:-1]
            language = alpha2_from_language(values[0])
            provider = values[1]
            score = int(round((float(values[2][:-1])/100 * 360) - 0.5))
            c.execute('UPDATE table_history SET language = ?, provider = ?, score = ? WHERE ROWID = ?', (language, provider, score, row[3]))
    db.commit()
    db.close()

def upgrade_history_movies():
    # Open database connection
    db = sqlite3.connect(os.path.join(args.config_dir, 'db', 'bazarr.db'), timeout=30)
    c = db.cursor()

    data = c.execute(
        'SELECT radarrId, video_path, description, ROWID FROM table_history_movie WHERE action = 1').fetchall()

    for row in data:
        if row[1] is None:
            path = c.execute('SELECT path FROM table_movies WHERE radarrId = ?', (row[0],)).fetchone()
            c.execute('UPDATE table_history_movie SET video_path = ? WHERE radarrId = ?', (path[0], row[0]))

            values = re.split(r' subtitles downloaded from | with a score of | using', row[2])[:-1]
            language = alpha2_from_language(values[0])
            provider = values[1]
            score = int(round((float(values[2][:-1]) / 100 * 120) - 0.5))
            c.execute('UPDATE table_history_movie SET language = ?, provider = ?, score = ? WHERE ROWID = ?', (language, provider, score, row[3]))
    db.commit()
    db.close()
