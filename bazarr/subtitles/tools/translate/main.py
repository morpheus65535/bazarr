# coding=utf-8

import logging
import os


from subliminal_patch.core import get_subtitle_path
from subzero.language import Language

from .core.translator_utils import validate_translation_params, convert_language_codes
from .services.translator_factory import TranslatorFactory
from languages.get_languages import alpha3_from_alpha2
from app.config import settings
from app.jobs_queue import jobs_queue
from subtitles.indexer.utils import get_external_subtitles_path


def translate_subtitles_file(video_path, source_srt_file, from_lang, to_lang, forced, hi,
                             media_type, sonarr_series_id, sonarr_episode_id, radarr_id, metadata, job_id=None):
    if not job_id:
        jobs_queue.add_job_from_function(f'Translating from {from_lang.upper()} to {to_lang.upper()} using '
                                         f'{settings.translator.translator_type.replace("_", " ").title()}',
                                         is_progress=True)
        return

    try:
        logging.debug(f'Translation request: video={video_path}, source={source_srt_file}, from={from_lang}, to={to_lang}')

        validate_translation_params(video_path, source_srt_file, from_lang, to_lang)
        lang_obj, orig_to_lang = convert_language_codes(to_lang, forced, hi)

        logging.debug(f'BAZARR is translating in {lang_obj} this subtitles {source_srt_file}')

        # get the destination path if the subtitles are alongside the video
        dest_srt_file_if_alongside_video = get_subtitle_path(
            video_path,
            language=lang_obj if isinstance(lang_obj, Language) else lang_obj.subzero_language(),
            extension='.srt',
            forced_tag=forced,
            hi_tag=hi
        )

        # get the real destination path taking into account if the user set up Bazarr to store external subtitles in
        #  a custom folder or relative folder
        dest_srt_file = get_external_subtitles_path(
            file=video_path,
            subtitle=os.path.basename(dest_srt_file_if_alongside_video)
        )

        translator_type = settings.translator.translator_type or 'google'
        logging.debug(f'Using translator type: {translator_type}')

        translator = TranslatorFactory.create_translator(
            translator_type,
            source_srt_file=source_srt_file,
            dest_srt_file=dest_srt_file,
            lang_obj=lang_obj,
            from_lang=from_lang,
            to_lang=alpha3_from_alpha2(to_lang),
            media_type=media_type,
            video_path=video_path,
            orig_to_lang=orig_to_lang,
            forced=forced,
            hi=hi,
            sonarr_series_id=sonarr_series_id,
            sonarr_episode_id=sonarr_episode_id,
            radarr_id=radarr_id
        )

        logging.debug(f'Created translator instance: {translator.__class__.__name__}')
        result = translator.translate(job_id=job_id)
        logging.debug(f'BAZARR saved translated subtitles to {dest_srt_file}')
        from api.subtitles.subtitles import postprocess_subtitles
        # Call postprocess_subtitles after translation
        postprocess_subtitles(dest_srt_file, video_path, media_type, metadata, sonarr_episode_id if media_type == 'series' else radarr_id)
        return result

    except Exception as e:
        logging.error(f'Translation failed: {str(e)}', exc_info=True)
        return False

    finally:
        jobs_queue.update_job_name(job_id=job_id,
                                   new_job_name=f'Translated from {from_lang.upper()} to {to_lang.upper()} using '
                                                f'{settings.translator.translator_type.replace("_", " ").title()}')
