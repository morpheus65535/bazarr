# coding=utf-8

from functools import lru_cache

from subtitles.language_utils import parse_language_token
from utilities.text_list import parse_text_list, parse_text_list_or_default


@lru_cache(maxsize=128)
def _parse_missing_subtitles_text(value):
    return tuple(language for language in parse_text_list_or_default(value) if language is not None)


def parse_missing_subtitles(value):
    if isinstance(value, str):
        return list(_parse_missing_subtitles_text(value))

    return [language for language in parse_text_list_or_default(value) if language is not None]


def missing_subtitle_to_language_tuple(language):
    parsed = parse_language_token(language)
    if parsed is None:
        return (language, "False", "False")

    _, language_tuple = parsed
    return language_tuple
