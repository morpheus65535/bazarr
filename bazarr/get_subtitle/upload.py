# coding=utf-8
# fmt: off

import sys
import logging

from subzero.language import Language
from subliminal_patch.core import save_subtitles
from subliminal_patch.subtitle import Subtitle

from get_languages import language_from_alpha3, alpha2_from_alpha3, alpha3_from_alpha2, \
    alpha2_from_language, alpha3_from_language
from config import settings, get_array_from
from helper import path_mappings, pp_replace, get_target_folder, force_unicode
from utils import notify_sonarr, notify_radarr
from custom_lang import CustomLanguage
from database import TableEpisodes, TableMovies
from event_handler import event_stream
from .sync import sync_subtitles
from .post_processing import postprocessing


def manual_upload_subtitle(path, language, forced, hi, title, scene_name, media_type, subtitle, audio_language):
    logging.debug('BAZARR Manually uploading subtitles for this file: ' + path)

    single = settings.general.getboolean('single_language')

    use_postprocessing = settings.general.getboolean('use_postprocessing')
    postprocessing_cmd = settings.general.postprocessing_cmd

    chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
        'win') and settings.general.getboolean('chmod_enabled') else None

    language = alpha3_from_alpha2(language)

    custom = CustomLanguage.from_value(language, "alpha3")
    if custom is None:
        lang_obj = Language(language)
    else:
        lang_obj = custom.subzero_language()

    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)

    sub = Subtitle(
        lang_obj,
        mods=get_array_from(settings.general.subzero_mods)
    )

    sub.content = subtitle.read()
    if not sub.is_valid():
        logging.exception('BAZARR Invalid subtitle file: ' + subtitle.filename)
        sub.mods = None

    if settings.general.getboolean('utf8_encode'):
        sub.set_encoding("utf-8")

    saved_subtitles = []
    try:
        saved_subtitles = save_subtitles(path,
                                         [sub],
                                         single=single,
                                         tags=None,  # fixme
                                         directory=get_target_folder(path),
                                         chmod=chmod,
                                         # formats=("srt", "vtt")
                                         path_decoder=force_unicode)
    except Exception:
        logging.exception('BAZARR Error saving Subtitles file to disk for this file:' + path)
        return

    if len(saved_subtitles) < 1:
        logging.exception('BAZARR Error saving Subtitles file to disk for this file:' + path)
        return

    subtitle_path = saved_subtitles[0].storage_path

    if hi:
        modifier_string = " HI"
    elif forced:
        modifier_string = " forced"
    else:
        modifier_string = ""
    message = language_from_alpha3(language) + modifier_string + " Subtitles manually uploaded."

    if hi:
        modifier_code = ":hi"
    elif forced:
        modifier_code = ":forced"
    else:
        modifier_code = ""
    uploaded_language_code3 = language + modifier_code
    uploaded_language = language_from_alpha3(language) + modifier_string
    uploaded_language_code2 = alpha2_from_alpha3(language) + modifier_code
    audio_language_code2 = alpha2_from_language(audio_language)
    audio_language_code3 = alpha3_from_language(audio_language)

    if media_type == 'series':
        episode_metadata = TableEpisodes.select(TableEpisodes.sonarrSeriesId, TableEpisodes.sonarrEpisodeId) \
            .where(TableEpisodes.path == path_mappings.path_replace_reverse(path)) \
            .dicts() \
            .get()
        series_id = episode_metadata['sonarrSeriesId']
        episode_id = episode_metadata['sonarrEpisodeId']
        sync_subtitles(video_path=path, srt_path=subtitle_path, srt_lang=uploaded_language_code2, media_type=media_type,
                       percent_score=100, sonarr_series_id=episode_metadata['sonarrSeriesId'], forced=forced,
                       sonarr_episode_id=episode_metadata['sonarrEpisodeId'])
    else:
        movie_metadata = TableMovies.select(TableMovies.radarrId) \
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path)) \
            .dicts() \
            .get()
        series_id = ""
        episode_id = movie_metadata['radarrId']
        sync_subtitles(video_path=path, srt_path=subtitle_path, srt_lang=uploaded_language_code2, media_type=media_type,
                       percent_score=100, radarr_id=movie_metadata['radarrId'], forced=forced)

    if use_postprocessing:
        command = pp_replace(postprocessing_cmd, path, subtitle_path, uploaded_language,
                             uploaded_language_code2, uploaded_language_code3, audio_language,
                             audio_language_code2, audio_language_code3, forced, 100, "1", "manual", series_id,
                             episode_id, hi=hi)
        postprocessing(command, path)

    if media_type == 'series':
        reversed_path = path_mappings.path_replace_reverse(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse(subtitle_path)
        notify_sonarr(episode_metadata['sonarrSeriesId'])
        event_stream(type='series', action='update', payload=episode_metadata['sonarrSeriesId'])
        event_stream(type='episode-wanted', action='delete', payload=episode_metadata['sonarrEpisodeId'])
    else:
        reversed_path = path_mappings.path_replace_reverse_movie(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse_movie(subtitle_path)
        notify_radarr(movie_metadata['radarrId'])
        event_stream(type='movie', action='update', payload=movie_metadata['radarrId'])
        event_stream(type='movie-wanted', action='delete', payload=movie_metadata['radarrId'])

    return message, reversed_path, reversed_subtitles_path
