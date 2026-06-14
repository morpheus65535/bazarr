# coding=utf-8
# fmt: off


def parse_language_token(language):
    if not isinstance(language, str):
        return None

    parts = [part.strip().lower() for part in language.split(":")]
    base_language = parts[0]
    if not base_language:
        return None

    flags = {part for part in parts[1:] if part}
    allowed_flags = {"hi", "forced"}
    if flags - allowed_flags:
        return None

    hi = "hi" in flags
    forced = "forced" in flags

    canonical_parts = [base_language]
    if forced:
        canonical_parts.append("forced")
    if hi:
        canonical_parts.append("hi")
    canonical = ":".join(canonical_parts)

    return canonical, (base_language, str(hi), str(forced))


def safe_missing_languages(missing_subtitles, context):
    from subtitles.serialization import parse_text_list_or_default

    missing = parse_text_list_or_default(missing_subtitles)

    safe = []
    for language in missing:
        parsed = parse_language_token(language)
        if not parsed:
            continue
        safe.append(parsed[0])
    return safe


def resolve_audio_language(audio_languages, fallback=None):
    if not isinstance(audio_languages, list) or not audio_languages:
        return fallback

    for language_item in audio_languages:
        if not isinstance(language_item, dict):
            continue
        name = language_item.get('name')
        if isinstance(name, str):
            normalized_name = name.strip()
            if normalized_name:
                return normalized_name

    return fallback


def format_episode_part(value):
    try:
        return f"{int(value):02d}"
    except (TypeError, ValueError):
        return str(value) if value is not None else "??"


def _is_unindexed_external_subtitle(subtitle):
    if not subtitle or not isinstance(subtitle, dict):
        return True
    if subtitle.get('path', True):
        return False
    return not subtitle.get('embedded_track_id')


def has_unindexed_external_subtitle(subtitles):
    return any(_is_unindexed_external_subtitle(subtitle) for subtitle in subtitles)


def build_search_payload(missing_subtitles, context, include_predicate=None):
    requests = []
    stamp_tokens = []
    seen_requests = set()
    seen_stamps = set()

    for canonical_language in safe_missing_languages(missing_subtitles, context):
        if include_predicate and not include_predicate(canonical_language):
            continue

        parsed = parse_language_token(canonical_language)
        if not parsed:
            continue

        canonical, language_request = parsed
        if language_request not in seen_requests:
            seen_requests.add(language_request)
            requests.append(language_request)

        if canonical not in seen_stamps:
            seen_stamps.add(canonical)
            stamp_tokens.append(canonical)

    return requests, stamp_tokens


def stamp_failed_attempts(stamp_languages, initial_attempt_string, update_fn, persist_fn):
    current_attempt_string = initial_attempt_string
    for language in stamp_languages:
        updated = update_fn(desired_language=language, attempt_string=current_attempt_string)
        if not updated:
            continue
        current_attempt_string = updated
        persist_fn(updated)

    return current_attempt_string
