# coding=utf-8

import ast
import json

from functools import lru_cache
from json import JSONDecodeError


def parse_text_list(value):
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if not isinstance(value, str):
        raise ValueError

    try:
        parsed = json.loads(value)
    except JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ValueError from exc

    if not isinstance(parsed, list):
        raise ValueError

    return parsed


def parse_text_list_or_default(value, default=None):
    if default is None:
        default = []

    try:
        return parse_text_list(value)
    except ValueError:
        return list(default)


def dump_text_list(values):
    return json.dumps(list(values))


@lru_cache(maxsize=128)
def _parse_missing_subtitles_text(value):
    return tuple(language for language in parse_text_list_or_default(value) if language is not None)


def parse_missing_subtitles(value):
    if isinstance(value, str):
        return list(_parse_missing_subtitles_text(value))

    return [language for language in parse_text_list_or_default(value) if language is not None]


def missing_subtitle_to_language_tuple(language):
    return (
        language.split(":")[0],
        "True" if language.endswith(':hi') else "False",
        "True" if language.endswith(':forced') else "False",
    )
