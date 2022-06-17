# coding=utf-8

import os
import logging

from app.event_handler import event_stream
from languages.get_languages import language_from_alpha2
from utilities.path_mappings import path_mappings
from subtitles.indexer.series import store_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from sonarr.history import history_log
from radarr.history import history_log_movie
from sonarr.notify import notify_sonarr
from radarr.notify import notify_radarr


def delete_subtitles(media_type, language, forced, hi, media_path, subtitles_path, sonarr_series_id=None,
                     sonarr_episode_id=None, radarr_id=None):
    if not subtitles_path.endswith('.srt'):
        logging.error('BAZARR can only delete .srt files.')
        return False

    language_log = language
    language_string = language_from_alpha2(language)
    if hi in [True, 'true', 'True']:
        language_log += ':hi'
        language_string += ' HI'
    elif forced in [True, 'true', 'True']:
        language_log += ':forced'
        language_string += ' forced'

    result = f"{language_string} subtitles deleted from disk."

    if media_type == 'series':
        try:
            os.remove(path_mappings.path_replace(subtitles_path))
        except OSError:
            logging.exception(f'BAZARR cannot delete subtitles file: {subtitles_path}')
            store_subtitles(path_mappings.path_replace_reverse(media_path), media_path)
            return False
        else:
            history_log(0, sonarr_series_id, sonarr_episode_id, result, language=language_log,
                        video_path=path_mappings.path_replace_reverse(media_path),
                        subtitles_path=path_mappings.path_replace_reverse(subtitles_path))
            store_subtitles(path_mappings.path_replace_reverse(media_path), media_path)
            notify_sonarr(sonarr_series_id)
            event_stream(type='series', action='update', payload=sonarr_series_id)
            event_stream(type='episode-wanted', action='update', payload=sonarr_episode_id)
            return True
    else:
        try:
            os.remove(path_mappings.path_replace_movie(subtitles_path))
        except OSError:
            logging.exception(f'BAZARR cannot delete subtitles file: {subtitles_path}')
            store_subtitles_movie(path_mappings.path_replace_reverse_movie(media_path), media_path)
            return False
        else:
            history_log_movie(0, radarr_id, result, language=language_log,
                              video_path=path_mappings.path_replace_reverse_movie(media_path),
                              subtitles_path=path_mappings.path_replace_reverse_movie(subtitles_path))
            store_subtitles_movie(path_mappings.path_replace_reverse_movie(media_path), media_path)
            notify_radarr(radarr_id)
            event_stream(type='movie-wanted', action='update', payload=radarr_id)
            return True
