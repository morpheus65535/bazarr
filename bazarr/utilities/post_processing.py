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
    """Replace placeholders in post-processing command with actual values.

    This function takes a post-processing command template and replaces various placeholders
    with their corresponding values. All values are properly escaped and quoted in the output.

    Args:
        pp_command (str): The post-processing command template containing placeholders
        episode (str): Path to the episode file
        subtitles (str): Path to the subtitles file
        language (str): Subtitle language name
        language_code2 (str): Two-letter language code for subtitles
        language_code3 (str): Three-letter language code for subtitles
        episode_language (str): Episode audio language name
        episode_language_code2 (str): Two-letter language code for episode audio
        episode_language_code3 (str): Three-letter language code for episode audio
        score (str): Subtitle match score
        subtitle_id (str): Unique identifier for the subtitle
        provider (str): Name of the subtitle provider
        uploader (str): Name of the subtitle uploader
        release_info (str): Release information
        series_id (str): Unique identifier for the series
        episode_id (str): Unique identifier for the episode

    Returns:
        str: The processed command with all placeholders replaced with properly escaped values
    """

    replacements = {
        r'[\'"]?{{directory}}[\'"]?': _escape(os.path.dirname(episode)),
        r'[\'"]?{{episode}}[\'"]?': _escape(episode),
        r'[\'"]?{{episode_name}}[\'"]?': _escape(os.path.splitext(os.path.basename(episode))[0]),
        r'[\'"]?{{subtitles}}[\'"]?': _escape(str(subtitles)),
        r'[\'"]?{{subtitles_language}}[\'"]?': _escape(str(language)),
        r'[\'"]?{{subtitles_language_code2}}[\'"]?': _escape(str(language_code2)),
        r'[\'"]?{{subtitles_language_code3}}[\'"]?': _escape(str(language_code3)),
        r'[\'"]?{{subtitles_language_code2_dot}}[\'"]?': _escape(str(language_code2).replace(':', '.')),
        r'[\'"]?{{subtitles_language_code3_dot}}[\'"]?': _escape(str(language_code3).replace(':', '.')),
        r'[\'"]?{{episode_language}}[\'"]?': _escape(str(episode_language)),
        r'[\'"]?{{episode_language_code2}}[\'"]?': _escape(str(episode_language_code2)),
        r'[\'"]?{{episode_language_code3}}[\'"]?': _escape(str(episode_language_code3)),
        r'[\'"]?{{score}}[\'"]?': _escape(str(score)),
        r'[\'"]?{{subtitle_id}}[\'"]?': _escape(str(subtitle_id)),
        r'[\'"]?{{provider}}[\'"]?': _escape(str(provider)),
        r'[\'"]?{{uploader}}[\'"]?': _escape(str(uploader)),
        r'[\'"]?{{release_info}}[\'"]?': _escape(str(release_info)),
        r'[\'"]?{{series_id}}[\'"]?': _escape(str(series_id)),
        r'[\'"]?{{episode_id}}[\'"]?': _escape(str(episode_id))
    }

    def replace_func(match):
        return replacements[match.group(0)]

    return re.sub('|'.join(replacements.keys()), replace_func, pp_command)


def set_chmod(subtitles_path):
    # apply chmod if required
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None
    if chmod:
        logging.debug(f"BAZARR setting permission to {chmod} on {subtitles_path} after custom post-processing.")
        os.chmod(subtitles_path, chmod)
