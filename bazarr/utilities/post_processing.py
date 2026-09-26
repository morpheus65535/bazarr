# coding=utf-8

import os
import shlex
import sys
import logging

from app.config import settings


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, episode_language,
               episode_language_code2, episode_language_code3, score, subtitle_id, provider, uploader,
               release_info, series_id, episode_id):
    values_matches = {
        '{{directory}}': os.path.dirname(episode),
        '{{episode}}': episode,
        '{{episode_name}}': os.path.splitext(os.path.basename(episode))[0],
        '{{subtitles}}': str(subtitles),
        '{{subtitles_language}}': str(language),
        '{{subtitles_language_code2}}': str(language_code2),
        '{{subtitles_language_code3}}': str(language_code3),
        '{{subtitles_language_code2_dot}}': str(language_code2).replace(':', '.'),
        '{{subtitles_language_code3_dot}}': str(language_code3).replace(':', '.'),
        '{{episode_language}}': str(episode_language),
        '{{episode_language_code2}}': str(episode_language_code2),
        '{{episode_language_code3}}': str(episode_language_code3),
        '{{score}}': str(score),
        '{{subtitle_id}}': str(subtitle_id),
        '{{provider}}': str(provider),
        '{{uploader}}': str(uploader),
        '{{release_info}}': str(release_info),
        '{{series_id}}': str(series_id),
        '{{episode_id}}': str(episode_id)
    }

    args = shlex.split(pp_command, posix=False if os.name == 'nt' else True)

    pp_args = []
    for arg in args:
        arg = arg.strip('"')
        if arg.startswith('{{') and arg.endswith('}}'):
            matched_value = values_matches.get(arg)
            if matched_value:
                pp_args.append(matched_value)
        else:
            pp_args.append(arg)

    return pp_args


def set_chmod(subtitles_path):
    # apply chmod if required
    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None
    if chmod:
        logging.debug(f"BAZARR setting permission to {chmod} on {subtitles_path} after custom post-processing.")
        os.chmod(subtitles_path, chmod)
