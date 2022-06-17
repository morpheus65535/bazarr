# coding=utf-8

import os
import logging

from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2


def subtitles_apply_mods(language, subtitle_path, mods, use_original_format):
    language = alpha3_from_alpha2(language)
    custom = CustomLanguage.from_value(language, "alpha3")
    lang_obj = Language(language) if custom is None else custom.subzero_language()
    sub = Subtitle(lang_obj, mods=mods, original_format=use_original_format)
    with open(subtitle_path, 'rb') as f:
        sub.content = f.read()

    if not sub.is_valid():
        logging.exception(f'BAZARR Invalid subtitle file: {subtitle_path}')
        return

    if use_original_format:
        return

    content = sub.get_modified_content()
    if content:
        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)

        with open(subtitle_path, 'wb') as f:
            f.write(content)
