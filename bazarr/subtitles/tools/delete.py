# coding=utf-8

import os
import logging

from subliminal.subtitle import SUBTITLE_EXTENSIONS

from app.event_handler import event_stream
from languages.get_languages import language_from_alpha2
from utilities.path_mappings import path_mappings
from utilities.autopulse_webhook import call_external_webhook
from subtitles.indexer.series import store_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from subtitles.processing import ProcessSubtitlesResult
from sonarr.history import history_log
from radarr.history import history_log_movie
from sonarr.notify import notify_sonarr
from radarr.notify import notify_radarr


def delete_subtitles(media_type, language, forced, hi, media_path, subtitles_path, sonarr_series_id=None,
                     sonarr_episode_id=None, radarr_id=None):
    if not subtitles_path:
        logging.error('No subtitles to delete.')
        return False

    if not os.path.splitext(subtitles_path)[1] in SUBTITLE_EXTENSIONS:
        logging.error('BAZARR can only delete subtitles files.')
        return False

    language_log = language
    language_string = language_from_alpha2(language)
    if hi in [True, 'true', 'True']:
        language_log += ':hi'
        language_string += ' HI'
    elif forced in [True, 'true', 'True']:
        language_log += ':forced'
        language_string += ' forced'

    if media_type == 'series':
        pr = path_mappings.path_replace
        prr = path_mappings.path_replace_reverse
    else:
        pr = path_mappings.path_replace_movie
        prr = path_mappings.path_replace_reverse_movie

    result = ProcessSubtitlesResult(message=f"{language_string} subtitles deleted from disk.",
                                    reversed_path=prr(media_path),
                                    downloaded_language_code2=language_log,
                                    downloaded_provider=None,
                                    score=None,
                                    forced=None,
                                    subtitle_id=None,
                                    reversed_subtitles_path=prr(subtitles_path),
                                    hearing_impaired=None)

    if media_type == 'series':
        try:
            os.remove(pr(subtitles_path))
        except OSError:
            logging.exception(f'BAZARR cannot delete subtitles file: {subtitles_path}')
            store_subtitles(prr(media_path), media_path)
            return False
        else:
            history_log(0, sonarr_series_id, sonarr_episode_id, result)
            store_subtitles(prr(media_path), media_path)
            notify_sonarr(sonarr_series_id)
            event_stream(type='series', action='update', payload=sonarr_series_id)
            event_stream(type='episode-wanted', action='update', payload=sonarr_episode_id)
            
            # Call external webhook after all processing is complete
            call_external_webhook(
                subtitle_path=subtitles_path,
                media_path=media_path,
                language=language_log,
                media_type=media_type
            )
            
            return True
    else:
        try:
            os.remove(pr(subtitles_path))
        except OSError:
            logging.exception(f'BAZARR cannot delete subtitles file: {subtitles_path}')
            store_subtitles_movie(prr(media_path), media_path)
            return False
        else:
            history_log_movie(0, radarr_id, result)
            store_subtitles_movie(prr(media_path), media_path)
            notify_radarr(radarr_id)
            event_stream(type='movie-wanted', action='update', payload=radarr_id)
            
            # Call external webhook after all processing is complete
            call_external_webhook(
                subtitle_path=subtitles_path,
                media_path=media_path,
                language=language_log,
                media_type=media_type
            )
            
            return True
