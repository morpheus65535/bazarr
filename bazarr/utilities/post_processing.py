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
    values_matches = {
        'directory': os.path.dirname(episode),
        'episode': episode,
        'episode_name': os.path.splitext(os.path.basename(episode))[0],
        'subtitles': str(subtitles),
        'subtitles_language': str(language),
        'subtitles_language_code2': str(language_code2),
        'subtitles_language_code3': str(language_code3),
        'subtitles_language_code2_dot': str(language_code2).replace(':', '.'),
        'subtitles_language_code3_dot': str(language_code3).replace(':', '.'),
        'episode_language': str(episode_language),
        'episode_language_code2': str(episode_language_code2),
        'episode_language_code3': str(episode_language_code3),
        'score': str(score),
        'subtitle_id': str(subtitle_id),
        'provider': str(provider),
        'uploader': str(uploader),
        'release_info': str(release_info),
        'series_id': str(series_id),
        'episode_id': str(episode_id)
    }

    # Use lambda as replacement so re.sub never interprets backslashes in the
    # replacement string as escape sequences (fixes UNC paths on Windows, e.g. \\Server\y\...)
    def replace_placeholder(m):
        key = m.group(1)
        return _double_quotes(values_matches[key])

    pp_command = re.sub(r'[\'"]?{{(\w+)}}[\'"]?', replace_placeholder, pp_command)
    return pp_command


def set_chmod(subtitles_path):
    # apply chmod if required
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None
    if chmod:
        logging.debug(f"BAZARR setting permission to {chmod} on {subtitles_path} after custom post-processing.")
        os.chmod(subtitles_path, chmod)
