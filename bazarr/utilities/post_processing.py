# coding=utf-8

import os
import re
import sys
import logging

from app.config import settings


# Wraps the input string within double quotes
def _double_quotes(in_str):
    return f"\"{in_str}\""


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, episode_language,
               episode_language_code2, episode_language_code3, score, subtitle_id, provider, uploader,
               release_info, series_id, episode_id):
    pp_command = re.sub(r'[\'"]?{{directory}}[\'"]?', _double_quotes(os.path.dirname(episode)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode}}[\'"]?', _double_quotes(episode), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_name}}[\'"]?', _double_quotes(os.path.splitext(os.path.basename(episode))[0]),
                        pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles}}[\'"]?', _double_quotes(str(subtitles)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language}}[\'"]?',  _double_quotes(str(language)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code2}}[\'"]?', _double_quotes(str(language_code2)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code3}}[\'"]?', _double_quotes(str(language_code3)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code2_dot}}[\'"]?',
                        _double_quotes(str(language_code2).replace(':', '.')), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitles_language_code3_dot}}[\'"]?',
                        _double_quotes(str(language_code3).replace(':', '.')), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_language}}[\'"]?', _double_quotes(str(episode_language)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_language_code2}}[\'"]?', _double_quotes(str(episode_language_code2)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_language_code3}}[\'"]?', _double_quotes(str(episode_language_code3)), pp_command)
    pp_command = re.sub(r'[\'"]?{{score}}[\'"]?', _double_quotes(str(score)), pp_command)
    pp_command = re.sub(r'[\'"]?{{subtitle_id}}[\'"]?', _double_quotes(str(subtitle_id)), pp_command)
    pp_command = re.sub(r'[\'"]?{{provider}}[\'"]?', _double_quotes(str(provider)), pp_command)
    pp_command = re.sub(r'[\'"]?{{uploader}}[\'"]?', _double_quotes(str(uploader)), pp_command)
    pp_command = re.sub(r'[\'"]?{{release_info}}[\'"]?', _double_quotes(str(release_info)), pp_command)
    pp_command = re.sub(r'[\'"]?{{series_id}}[\'"]?', _double_quotes(str(series_id)), pp_command)
    pp_command = re.sub(r'[\'"]?{{episode_id}}[\'"]?', _double_quotes(str(episode_id)), pp_command)
    return pp_command


def set_chmod(subtitles_path):
    # apply chmod if required
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None
    if chmod:
        logging.debug(f"BAZARR setting permission to {chmod} on {subtitles_path} after custom post-processing.")
        os.chmod(subtitles_path, chmod)
