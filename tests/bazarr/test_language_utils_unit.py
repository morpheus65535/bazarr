import subtitles.language_utils as language_utils


def test_parse_language_token_canonicalizes_case_and_flag_order():
    module = language_utils

    canonical, language_tuple = module.parse_language_token(" EN : HI : Forced ")

    assert canonical == "en:forced:hi"
    assert language_tuple == ("en", "True", "True")


def test_parse_language_token_rejects_missing_base_language():
    module = language_utils

    assert module.parse_language_token(":hi") is None
    assert module.parse_language_token(None) is None


def test_safe_missing_languages_filters_invalid_and_normalizes_tokens():
    module = language_utils

    value = "[' EN ', ':hi', 'fr:HI', None, 'de:Forced:Hi', 'fr:hi']"
    result = module.safe_missing_languages(value, "unit test")

    assert result == ["en", "fr:hi", "de:forced:hi", "fr:hi"]


def test_resolve_audio_language_uses_first_non_empty_name_with_fallback():
    module = language_utils

    audio_languages = [{"name": "   "}, {"code": "eng"}, {"name": " English "}]
    result = module.resolve_audio_language(audio_languages, fallback="fallback")
    empty_result = module.resolve_audio_language([], fallback="fallback")

    assert result == "English"
    assert empty_result == "fallback"


def test_format_episode_part_handles_non_integer_values():
    module = language_utils

    assert module.format_episode_part(2) == "02"
    assert module.format_episode_part("3") == "03"
    assert module.format_episode_part("special") == "special"
    assert module.format_episode_part(None) == "??"


def test_has_unindexed_external_subtitle_detects_missing_external_track_ids():
    module = language_utils

    assert module.has_unindexed_external_subtitle([]) is False
    assert module.has_unindexed_external_subtitle([{"path": "/sub.srt", "embedded_track_id": 1}]) is False
    assert module.has_unindexed_external_subtitle([{"path": None, "embedded_track_id": None}]) is True
    assert module.has_unindexed_external_subtitle([None]) is True


def test_build_search_payload_deduplicates_and_normalizes():
    module = language_utils

    requests, stamps = module.build_search_payload(
        "[' EN ', 'en', 'fr:HI', 'fr:hi', 'de:Forced:Hi']",
        "unit test",
    )

    assert requests == [
        ("en", "False", "False"),
        ("fr", "True", "False"),
        ("de", "True", "True"),
    ]
    assert stamps == ["en", "fr:hi", "de:forced:hi"]


def test_stamp_failed_attempts_chains_updates():
    module = language_utils
    calls = []
    persisted = []

    def _update_fn(desired_language, attempt_string):
        calls.append((desired_language, attempt_string))
        return f"{attempt_string}|{desired_language}"

    def _persist_fn(updated):
        persisted.append(updated)

    final_attempts = module.stamp_failed_attempts(
        ["en", "fr:forced"],
        "seed",
        _update_fn,
        _persist_fn,
    )

    assert calls == [("en", "seed"), ("fr:forced", "seed|en")]
    assert persisted == ["seed|en", "seed|en|fr:forced"]
    assert final_attempts == "seed|en|fr:forced"
