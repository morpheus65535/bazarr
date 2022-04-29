# coding=utf-8

import logging
import pysubs2

from subliminal_patch.core import get_subtitle_path
from subzero.language import Language
from deep_translator import GoogleTranslator

from languages.custom_lang import CustomLanguage
from languages.get_languages import alpha3_from_alpha2


def translate_subtitles_file(video_path, source_srt_file, to_lang, forced, hi):
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

    logging.debug('BAZARR splitting subtitles into {} characters blocks'.format(max_characters))
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

    logging.debug('BAZARR is sending {} blocks to Google Translate'.format(len(lines_block_list)))
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

    logging.debug('BAZARR saving translated subtitles to {}'.format(dest_srt_file))
    for i, line in enumerate(subs):
        try:
            line.plaintext = translated_lines_list[i]
        except IndexError:
            logging.error(f'BAZARR is unable to translate malformed subtitles: {source_srt_file}')
            return False
    subs.save(dest_srt_file)

    return dest_srt_file
