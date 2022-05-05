# coding=utf-8

import os


def pp_replace(pp_command, episode, subtitles, language, language_code2, language_code3, episode_language, episode_language_code2, episode_language_code3, forced, score, subtitle_id, provider, series_id, episode_id, hi):
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
