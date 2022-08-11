# coding=utf-8

import os
import logging
import re

from guess_language import guess_language
from subliminal_patch import core
from subzero.language import Language
from charamel import Detector

from app.config import settings
from constants import hi_regex
from utilities.path_mappings import path_mappings


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
            if [x for x in previously_indexed_subtitles_to_exclude
                if x[1] == reversed_subtitle_path and x[2] == os.stat(subtitle_path).st_size]:
                continue

        if not language:
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                logging.debug("BAZARR falling back to file content analysis to detect language.")
                detected_language = None

                # detect forced subtitles
                forced = True if os.path.splitext(os.path.splitext(subtitle)[0])[1] == '.forced' else False

                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > 1 * 1024 * 1024:
                    logging.debug("BAZARR subtitles file is too large to be text based. Skipping this file: " +
                                  subtitle_path)
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                try:
                    text = text.decode('utf-8')
                    detected_language = guess_language(text)
                    # add simplified and traditional chinese detection
                    if detected_language == 'zh':
                        traditional_chinese_fuzzy = [u"繁", u"雙語"]
                        traditional_chinese = [".cht", ".tc", ".zh-tw", ".zht", ".zh-hant", ".zhhant", ".zh_hant",
                                               ".hant", ".big5", ".traditional"]
                        if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(traditional_chinese)) or (str(subtitle_path).lower())[:-5] in traditional_chinese_fuzzy:
                            detected_language == 'zt'
                except UnicodeDecodeError:
                    detector = Detector()
                    try:
                        guess = detector.detect(text)
                    except Exception:
                        logging.debug("BAZARR skipping this subtitles because we can't guess the encoding. "
                                      "It's probably a binary file: " + subtitle_path)
                        continue
                    else:
                        logging.debug('BAZARR detected encoding %r', guess)
                        try:
                            text = text.decode(guess)
                        except Exception:
                            logging.debug(
                                "BAZARR skipping this subtitles because we can't decode the file using the "
                                "guessed encoding. It's probably a binary file: " + subtitle_path)
                            continue
                    detected_language = guess_language(text)
                except Exception:
                    logging.debug('BAZARR was unable to detect encoding for this subtitles file: %r', subtitle_path)
                finally:
                    if detected_language:
                        logging.debug("BAZARR external subtitles detected and guessed this language: " + str(
                            detected_language))
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
                if os.path.getsize(subtitle_path) > 1 * 1024 * 1024:
                    logging.debug("BAZARR subtitles file is too large to be text based. Skipping this file: " +
                                  subtitle_path)
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError:
                    detector = Detector()
                    try:
                        guess = detector.detect(text)
                    except Exception:
                        logging.debug("BAZARR skipping this subtitles because we can't guess the encoding. "
                                      "It's probably a binary file: " + subtitle_path)
                        continue
                    else:
                        logging.debug('BAZARR detected encoding %r', guess)
                        try:
                            text = text.decode(guess)
                        except Exception:
                            logging.debug("BAZARR skipping this subtitles because we can't decode the file using the "
                                          "guessed encoding. It's probably a binary file: " + subtitle_path)
                            continue

                if bool(re.search(hi_regex, text)):
                    subtitles[subtitle] = Language.rebuild(subtitles[subtitle], forced=False, hi=True)
    return subtitles
