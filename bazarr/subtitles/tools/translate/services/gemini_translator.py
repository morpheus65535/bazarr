# coding=utf-8

import logging

import srt
import pysubs2

from retry.api import retry
from app.config import settings
from sonarr.history import history_log
from radarr.history import history_log_movie
from deep_translator import GoogleTranslator
from utilities.path_mappings import path_mappings
from subtitles.processing import ProcessSubtitlesResult
from app.event_handler import show_progress, hide_progress, show_message
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from ..core.translator_utils import add_translator_info, get_description
from ...translator_gemini import TranslatorGemini

class GeminiTranslatorService:

    def __init__(self, source_srt_file, dest_srt_file, to_lang, media_type,
                 sonarr_series_id=None, radarr_id=None, **kwargs):
        self.source_srt_file = source_srt_file
        self.dest_srt_file = dest_srt_file
        self.to_lang = to_lang
        self.media_type = media_type
        self.sonarr_series_id = sonarr_series_id
        self.radarr_id = radarr_id

    def translate(self):
        subs = pysubs2.load(self.source_srt_file, encoding='utf-8')
        subs.remove_miscellaneous_events()

        try:
            logging.debug(f'BAZARR is sending subtitle file to Gemini for translation')
            logging.info(f"BAZARR is sending subtitle file to Gemini for translation " + self.source_srt_file)

            params = {
                "gemini_api_key": settings.translator.gemini_key,
                "target_language": language_from_alpha3(self.to_lang),
                "input_file": self.source_srt_file,
                "output_file": self.dest_srt_file,
                "model_name": settings.translator.gemini_model,
                "description": get_description(self.media_type, self.radarr_id, self.sonarr_series_id),
            }

            try:
                filtered_params = {k: v for k, v in params.items() if v is not None}
                translator = TranslatorGemini(**filtered_params)
                translator.translate()
                add_translator_info(self.dest_srt_file, f"# Subtitles translated with {settings.translator.gemini_model} # ")
            except Exception as e:
                show_message(f'Gemini translation error: {str(e)}')

        except Exception as e:
            logging.error(f'BAZARR encountered an error translating with Gemini: {str(e)}')
            return False
