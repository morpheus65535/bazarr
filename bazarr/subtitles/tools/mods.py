# coding=utf-8

import os
import logging

from subliminal_patch.subtitle import Subtitle
from subliminal_patch.core import get_subtitle_path
from subzero.language import Language

from app.config import settings
from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2
from subtitles.indexer.utils import get_external_subtitles_path


def subtitles_apply_mods(language, subtitle_path, mods, video_path):
    language = alpha3_from_alpha2(language)
    custom = CustomLanguage.from_value(language, "alpha3")
    if custom is None:
        lang_obj = Language(language)
    else:
        lang_obj = custom.subzero_language()
    single = settings.general.single_language

    sub = Subtitle(lang_obj, mods=mods, original_format=True)
    with open(subtitle_path, 'rb') as f:
        sub.content = f.read()

    if not sub.is_valid():
        logging.exception(f'BAZARR Invalid subtitle file: {subtitle_path}')
        return

    content = sub.get_modified_content(format=sub.format)
    if content:
        if hasattr(sub, 'mods') and isinstance(sub.mods, list) and 'remove_HI' in sub.mods:
            # get the modded subtitles path if the subtitles are alongside the video
            modded_subtitles_path_if_alongside_video = get_subtitle_path(
                video_path,
                language=None if single else sub.language,
                forced_tag=sub.language.forced,
                hi_tag=False,
                tags=[],
                extension=f".{sub.format}"
            )

            # get the real modded subtitles path taking into account if the user set up Bazarr to store external
            # subtitles in a custom folder or relative folder
            modded_subtitles_path = get_external_subtitles_path(
                file=video_path,
                subtitle=os.path.basename(modded_subtitles_path_if_alongside_video)
            )
        else:
            modded_subtitles_path = subtitle_path

        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)

        if os.path.exists(modded_subtitles_path):
            os.remove(modded_subtitles_path)

        with open(modded_subtitles_path, 'wb') as f:
            f.write(content)

        return modded_subtitles_path
