# coding=utf-8

import os
import logging

from guess_language import guess_language
from subliminal_patch import core
from subzero.language import Language
from charset_normalizer import detect

from constants import MAXIMUM_SUBTITLE_SIZE
from app.config import settings
from utilities.path_mappings import path_mappings
from languages.custom_lang import CustomLanguage


def get_external_subtitles_path(file, subtitle):
    fld = os.path.dirname(file)

    if settings.general.subfolder == "current":
        path = os.path.join(fld, subtitle)
    elif settings.general.subfolder == "absolute":
        custom_fld = settings.general.subfolder_custom
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    elif settings.general.subfolder == "relative":
        custom_fld = os.path.join(fld, settings.general.subfolder_custom)
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    else:
        path = None

    return path


def guess_external_subtitles(dest_folder, subtitles, media_type, previously_indexed_subtitles_to_exclude=None):
    for subtitle, language in subtitles.items():
        subtitle_path = os.path.join(dest_folder, subtitle)
        reversed_subtitle_path = path_mappings.path_replace_reverse(subtitle_path) if media_type == "series" \
            else path_mappings.path_replace_reverse_movie(subtitle_path)

        if previously_indexed_subtitles_to_exclude:
            x_found_lang = None
            for x_lang, x_path, x_size in previously_indexed_subtitles_to_exclude:
                if x_path == reversed_subtitle_path and x_size == os.stat(subtitle_path).st_size:
                    x_found_lang = x_lang
                    break
            if x_found_lang:
                if not language:
                    subtitles[subtitle] = _get_lang_from_str(x_found_lang)
                continue

        if not language:
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                logging.debug("BAZARR falling back to file content analysis to detect language.")
                detected_language = None

                # detect forced subtitles
                forced = True if os.path.splitext(os.path.splitext(subtitle)[0])[1] == '.forced' else False

                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > MAXIMUM_SUBTITLE_SIZE:
                    logging.debug(f"BAZARR subtitles file is too large to be text based. Skipping this file: "
                                  f"{subtitle_path}")
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                encoding = detect(text)
                if encoding and 'encoding' in encoding and encoding['encoding']:
                    encoding = detect(text)['encoding']
                else:
                    logging.debug(f"BAZARR skipping this subtitles because we can't guess the encoding. "
                                  f"It's probably a binary file: {subtitle_path}")
                    continue
                text = text.decode(encoding)

                detected_language = guess_language(text)

                # add simplified and traditional chinese detection
                if detected_language == 'zh':
                    traditional_chinese_fuzzy = [u"繁", u"雙語"]
                    traditional_chinese = [".cht", ".tc", ".zh-tw", ".zht", ".zh-hant", ".zhhant", ".zh_hant",
                                           ".hant", ".big5", ".traditional"]
                    if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(traditional_chinese)) or \
                            (str(subtitle_path).lower())[:-5] in traditional_chinese_fuzzy:
                        detected_language = 'zt'

                if detected_language:
                    logging.debug(f"BAZARR external subtitles detected and guessed this language: {detected_language}")
                    try:
                        subtitles[subtitle] = Language.rebuild(Language.fromietf(detected_language), forced=forced,
                                                               hi=False)
                    except Exception:
                        pass

        # If language is still None (undetected), skip it
        if hasattr(subtitles[subtitle], 'basename') and not subtitles[subtitle].basename:
            continue

        # Skip HI detection if forced
        if hasattr(language, 'forced') and language.forced:
            continue

        # Detect hearing-impaired external subtitles not identified in filename
        if hasattr(subtitles[subtitle], 'hi') and not subtitles[subtitle].hi:
            subtitle_path = os.path.join(dest_folder, subtitle)

            # check if file exist:
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > MAXIMUM_SUBTITLE_SIZE:
                    logging.debug(f"BAZARR subtitles file is too large to be text based. Skipping this file: "
                                  f"{subtitle_path}")
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                encoding = detect(text)
                if encoding and 'encoding' in encoding and encoding['encoding']:
                    encoding = detect(text)['encoding']
                else:
                    logging.debug(f"BAZARR skipping this subtitles because we can't guess the encoding. "
                                  f"It's probably a binary file: {subtitle_path}")
                    continue
                text = text.decode(encoding)

                if os.path.splitext(subtitle_path)[1] == 'srt':
                    if core.parse_for_hi_regex(subtitle_text=text,
                                               alpha3_language=language.alpha3 if hasattr(language, 'alpha3') else
                                               None):
                        subtitles[subtitle] = Language.rebuild(subtitles[subtitle], forced=False, hi=True)
    return subtitles


def _get_lang_from_str(x_found_lang):
    x_found_lang_split = x_found_lang.split(':')[0]
    x_hi = ':hi' in x_found_lang.lower()
    x_forced = ':forced' in x_found_lang.lower()

    if len(x_found_lang_split) == 2:
        x_custom_lang_attr = "alpha2"
    elif len(x_found_lang_split) == 3:
        x_custom_lang_attr = "alpha3"
    else:
        x_custom_lang_attr = "language"

    x_custom_lang = CustomLanguage.from_value(x_found_lang_split, attr=x_custom_lang_attr)

    if x_custom_lang is not None:
        return Language.rebuild(x_custom_lang.subzero_language(), hi=x_hi, forced=x_forced)
    else:
        return Language.rebuild(Language.fromietf(x_found_lang), hi=x_hi, forced=x_forced)
