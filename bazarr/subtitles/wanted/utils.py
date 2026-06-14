# coding=utf-8

from subtitles.adaptive_searching import get_active_search_languages
from subtitles.serialization import parse_missing_subtitles, missing_subtitle_to_language_tuple


def get_due_missing_languages(missing_subtitles, failed_attempts, adaptive_search_policy=None):
    desired_languages = parse_missing_subtitles(missing_subtitles)
    if not desired_languages:
        return []

    return get_active_search_languages(
        desired_languages,
        failed_attempts,
        adaptive_search_policy=adaptive_search_policy,
    )


def get_language_search_items(missing_languages):
    return [missing_subtitle_to_language_tuple(language) for language in missing_languages]
