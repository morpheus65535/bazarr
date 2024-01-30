# coding=utf-8

import os
import re
import sys
import logging

from app.config import settings


# Wraps the input string within quotes & escapes the string
def _escape(in_str):
    raw_map = {8: r'\\b', 7: r'\\a', 12: r'\\f', 10: r'\\n', 13: r'\\r', 9: r'\\t', 11: r'\\v', 34: r'\"', 92: r'\\'}
    raw_str = r''.join(raw_map.get(ord(i), i) for i in in_str)
    return f"\"{raw_str}\""


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, episode_language,
               episode_language_code2, episode_language_code3, score, subtitle_id, provider, uploader,
               release_info, series_id, episode_id):
    pp_command = re.sub(r'[\'"]?{{directory}}[\'"]?', _escape(os.path.dirname(episode)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode}}[\'"]?', _escape(episode), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_name}}[\'"]?', _escape(os.path.splitext(os.path.basename(episode))[0]),
                        pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles}}[\'"]?', _escape(str(subtitles)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language}}[\'"]?',  _escape(str(language)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code2}}[\'"]?', _escape(str(language_code2)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code3}}[\'"]?', _escape(str(language_code3)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code2_dot}}[\'"]?',
                        _escape(str(language_code2).replace(':', '.')), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code3_dot}}[\'"]?',
                        _escape(str(language_code3).replace(':', '.')), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_language}}[\'"]?', _escape(str(episode_language)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_language_code2}}[\'"]?', _escape(str(episode_language_code2)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_language_code3}}[\'"]?', _escape(str(episode_language_code3)), pp_command)
    pp_command = re.sub(r'[\'"]?{{score}}[\'"]?', _escape(str(score)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitle_id}}[\'"]?', _escape(str(subtitle_id)), pp_command)
    pp_command = re.sub(r'[\'"]?{{provider}}[\'"]?', _escape(str(provider)), pp_command)
    pp_command = re.sub(r'[\'"]?{{uploader}}[\'"]?', _escape(str(uploader)), pp_command)
    pp_command = re.sub(r'[\'"]?{{release_info}}[\'"]?', _escape(str(release_info)), pp_command)
    pp_command = re.sub(r'[\'"]?{{series_id}}[\'"]?', _escape(str(series_id)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_id}}[\'"]?', _escape(str(episode_id)), pp_command)
    return pp_command


def set_chmod(subtitles_path):
    # apply chmod if required
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None
    if chmod:
        logging.debug(f"BAZARR setting permission to {chmod} on {subtitles_path} after custom post-processing.")
        os.chmod(subtitles_path, chmod)
