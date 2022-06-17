# coding=utf-8

import logging
import pysubs2

from subliminal_patch.core import get_subtitle_path
from subzero.language import Language
from deep_translator import GoogleTranslator

from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2, language_from_alpha2, language_from_alpha3
from radarr.history import history_log_movie
from sonarr.history import history_log


def translate_subtitles_file(video_path, source_srt_file, from_lang, to_lang, forced, hi, media_type, sonarr_series_id,
                             sonarr_episode_id, radarr_id):
    language_code_convert_dict = {
        'he': 'iw',
        'zt': 'zh-CN',
        'zh': 'zh-TW',
    }

    to_lang = alpha3_from_alpha2(to_lang)
    lang_obj = CustomLanguage.from_value(to_lang, "alpha3")
    if not lang_obj:
        lang_obj = Language(to_lang)
    if forced:
        lang_obj = Language.rebuild(lang_obj, forced=True)
    if hi:
        lang_obj = Language.rebuild(lang_obj, hi=True)

    logging.debug('BAZARR is translating in {0} this subtitles {1}'.format(lang_obj, source_srt_file))

    max_characters = 5000

    dest_srt_file = get_subtitle_path(video_path,
                                      language=lang_obj if isinstance(lang_obj, Language) else lang_obj.subzero_language(),
                                      extension='.srt',
                                      forced_tag=forced,
                                      hi_tag=hi)

    subs = pysubs2.load(source_srt_file, encoding='utf-8')
    subs.remove_miscellaneous_events()
    lines_list = [x.plaintext for x in subs]
    joined_lines_str = '\n\n\n'.join(lines_list)

    logging.debug(f'BAZARR splitting subtitles into {max_characters} characters blocks')

    lines_block_list = []
    translated_lines_list = []
    while len(joined_lines_str):
        partial_lines_str = joined_lines_str[:max_characters]

        if len(joined_lines_str) > max_characters:
            new_partial_lines_str = partial_lines_str.rsplit('\n\n\n', 1)[0]
        else:
            new_partial_lines_str = partial_lines_str

        lines_block_list.append(new_partial_lines_str)
        joined_lines_str = joined_lines_str.replace(new_partial_lines_str, '')

    logging.debug(f'BAZARR is sending {len(lines_block_list)} blocks to Google Translate')

    for block_str in lines_block_list:
        try:
            translated_partial_srt_text = GoogleTranslator(source='auto',
                                                           target=language_code_convert_dict.get(lang_obj.alpha2,
                                                                                                 lang_obj.alpha2)
                                                           ).translate(text=block_str)
        except Exception:
            logging.exception(f'BAZARR Unable to translate subtitles {source_srt_file}')
            return False
        else:
            translated_partial_srt_list = translated_partial_srt_text.split('\n\n\n')
            translated_lines_list += translated_partial_srt_list

    logging.debug(f'BAZARR saving translated subtitles to {dest_srt_file}')
    for i, line in enumerate(subs):
        try:
            line.plaintext = translated_lines_list[i]
        except IndexError:
            logging.error(f'BAZARR is unable to translate malformed subtitles: {source_srt_file}')
            return False
    subs.save(dest_srt_file)

    message = f"{language_from_alpha2(from_lang)} subtitles translated to {language_from_alpha3(to_lang)}."

    if media_type == 'series':
        history_log(action=6, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id,
                    description=message, video_path=video_path, language=to_lang, subtitles_path=dest_srt_file)
    else:
        history_log_movie(action=6, radarr_id=radarr_id, description=message,
                          video_path=video_path, language=to_lang, subtitles_path=dest_srt_file)

    return dest_srt_file
