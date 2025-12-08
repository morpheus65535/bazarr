# coding=utf-8
# fmt: off

import os
import sys
import logging

from subzero.language import Language
from subliminal_patch.core import save_subtitles
from subliminal_patch.subtitle import Subtitle
from pysubs2.formats import get_format_identifier

from languages.get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2
from app.config import settings, get_array_from
from utilities.helper import get_target_folder, force_unicode
from utilities.post_processing import pp_replace, set_chmod
from utilities.path_mappings import path_mappings
from radarr.history import history_log_movie
from radarr.notify import notify_radarr
from sonarr.history import history_log
from sonarr.notify import notify_sonarr
from languages.custom_lang import CustomLanguage
from app.database import (TableEpisodes, TableMovies, TableShows, get_profiles_list, get_audio_profile_languages,
                          database, select)
from app.jobs_queue import jobs_queue
from app.event_handler import event_stream
from app.notifier import send_notifications
from app.notifier import send_notifications_movie
from subtitles.indexer.series import store_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from subtitles.processing import ProcessSubtitlesResult

from .sync import sync_subtitles
from .post_processing import postprocessing


def manual_upload_subtitle(path, language, forced, hi, media_type, subtitle, audio_language, job_id=None,
                           sonarrSeriesId=None, sonarrEpisodeId=None, radarrId=None):
    if not job_id:
        return jobs_queue.add_job_from_function(f"Uploading {subtitle.filename}", is_progress=False)

    logging.debug(f'BAZARR Manually uploading subtitles: {subtitle.filename}')

    single = settings.general.single_language

    use_postprocessing = settings.general.use_postprocessing
    postprocessing_cmd = settings.general.postprocessing_cmd

    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.chmod_enabled else None

    language = alpha3_from_alpha2(language)

    custom = CustomLanguage.from_value(language, "alpha3")
    if custom is None:
        lang_obj = Language(language)
    else:
        lang_obj = custom.subzero_language()

    if hi:
        lang_obj = Language.rebuild(lang_obj, hi=True)

    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)

    if media_type == 'series':
        episode_metadata = database.execute(
            select(TableEpisodes.sonarrSeriesId,
                   TableEpisodes.sonarrEpisodeId,
                   TableShows.profileId)
            .select_from(TableEpisodes)
            .join(TableShows)
            .where(TableEpisodes.sonarrEpisodeId == sonarrEpisodeId)) \
            .first()

        if episode_metadata:
            use_original_format = bool(get_profiles_list(episode_metadata.profileId)["originalFormat"])
        else:
            return
    else:
        movie_metadata = database.execute(
            select(TableMovies.radarrId, TableMovies.profileId)
            .where(TableMovies.radarrId == radarrId)) \
            .first()

        if movie_metadata:
            use_original_format = bool(get_profiles_list(movie_metadata.profileId)["originalFormat"])
        else:
            return

    audio_language = get_audio_profile_languages(audio_language)
    if len(audio_language) and isinstance(audio_language[0], dict):
        audio_language = audio_language[0]
    else:
        audio_language = {'name': '', 'code2': '', 'code3': ''}

    sub = Subtitle(
        lang_obj,
        mods=get_array_from(settings.general.subzero_mods),
        original_format=use_original_format
    )

    sub.content = subtitle.read()
    if not sub.is_valid():
        logging.exception(f'BAZARR Invalid subtitle file: {subtitle.filename}')
        sub.mods = None

    if settings.general.utf8_encode:
        sub.set_encoding("utf-8")

    try:
        sub.format = (get_format_identifier(os.path.splitext(subtitle.filename)[1]),)
    except Exception:
        pass

    saved_subtitles = []
    try:
        saved_subtitles = save_subtitles(path,
                                         [sub],
                                         single=single,
                                         tags=None,  # fixme
                                         directory=get_target_folder(path),
                                         chmod=chmod,
                                         formats=(sub.format,) if use_original_format else ("srt",),
                                         path_decoder=force_unicode)
    except Exception as e:
        logging.exception(f'BAZARR Error saving Subtitles file to disk for this file {path}: {repr(e)}')
        return

    if len(saved_subtitles) < 1:
        logging.exception(f'BAZARR Error saving Subtitles file to disk for this file: {path}')
        return

    subtitle_path = saved_subtitles[0].storage_path

    if hi:
        modifier_string = " HI"
    elif forced:
        modifier_string = " forced"
    else:
        modifier_string = ""

    if hi:
        modifier_code = ":hi"
    elif forced:
        modifier_code = ":forced"
    else:
        modifier_code = ""
    uploaded_language_code3 = language + modifier_code
    uploaded_language = language_from_alpha3(language) + modifier_string
    uploaded_language_code2 = alpha2_from_alpha3(language) + modifier_code

    if use_postprocessing:
        command = pp_replace(postprocessing_cmd, path, subtitle_path, uploaded_language, uploaded_language_code2,
                             uploaded_language_code3, audio_language['name'], audio_language['code2'],
                             audio_language['code3'], 100, "1", "manual", "user", "unknown", sonarrSeriesId,
                             sonarrEpisodeId or radarrId,)
        postprocessing(command, path)
        set_chmod(subtitles_path=subtitle_path)

    if media_type == 'series':
        sync_subtitles(video_path=path, srt_path=subtitle_path, srt_lang=uploaded_language_code2, percent_score=100,
                       sonarr_series_id=episode_metadata.sonarrSeriesId, forced=forced, hi=hi,
                       sonarr_episode_id=episode_metadata.sonarrEpisodeId, job_id=job_id, job_sub_function=True,)
        reversed_path = path_mappings.path_replace_reverse(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse(subtitle_path)
        notify_sonarr(episode_metadata.sonarrSeriesId)
        event_stream(type='series', action='update', payload=episode_metadata.sonarrSeriesId)
        event_stream(type='episode-wanted', action='delete', payload=episode_metadata.sonarrEpisodeId)
    else:
        sync_subtitles(video_path=path, srt_path=subtitle_path, srt_lang=uploaded_language_code2, percent_score=100,
                       radarr_id=movie_metadata.radarrId, forced=forced, hi=hi, job_id=job_id, job_sub_function=True,)
        reversed_path = path_mappings.path_replace_reverse_movie(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse_movie(subtitle_path)
        notify_radarr(movie_metadata.radarrId)
        event_stream(type='movie', action='update', payload=movie_metadata.radarrId)
        event_stream(type='movie-wanted', action='delete', payload=movie_metadata.radarrId)

    result = ProcessSubtitlesResult(message=f"{language_from_alpha3(language)}{modifier_string} Subtitles manually "
                                            "uploaded.",
                                    reversed_path=reversed_path,
                                    downloaded_language_code2=uploaded_language_code2,
                                    downloaded_provider=None,
                                    score=None,
                                    forced=None,
                                    subtitle_id=None,
                                    reversed_subtitles_path=reversed_subtitles_path,
                                    hearing_impaired=None)

    if not result:
        logging.debug(f"BAZARR unable to process subtitles for this {'episode' if media_type == 'series' else 'movie'}:"
                      f" {path}")
    else:
        if isinstance(result, tuple) and len(result):
            result = result[0]
        provider = "manual"
        if media_type == 'series':
            score = 360
            history_log(4, sonarrSeriesId, sonarrEpisodeId, result, fake_provider=provider, fake_score=score)
            if not settings.general.dont_notify_manual_actions:
                send_notifications(sonarrSeriesId, sonarrEpisodeId, result.message)
            store_subtitles(result.path, path)
        else:
            score = 120
            history_log_movie(4, radarrId, result, fake_provider=provider, fake_score=score)
            if not settings.general.dont_notify_manual_actions:
                send_notifications_movie(radarrId, result.message)
            store_subtitles_movie(result.path, path)

    return '', 204
