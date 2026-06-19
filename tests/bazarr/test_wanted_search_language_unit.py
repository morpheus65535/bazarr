from functools import partial
from unittest.mock import Mock

import pytest


def _english_audio_languages(audio_language):
    return [{"name": "English"}]


def _search_always_active(desired_language, attempt_string):
    return True


def _capture_update_failed_attempts(calls, desired_language, attempt_string):
    calls.append((desired_language, attempt_string))
    return f"{attempt_string}|{desired_language}"


def _generated_languages(generate_subtitles):
    return generate_subtitles.call_args.args[1]


def _run_wanted_worker(wanted_module, kind, item, providers=None):
    if providers is None:
        providers = ["provider"]
    if kind == "movies":
        wanted_module._wanted_movie(item, providers)
    else:
        wanted_module._wanted_episode(item, providers)


def _malformed_missing_subtitles_cases():
    malformed_values = [
        "",
        " ",
        "[",
        "]",
        "not_a_list",
        "None",
        "{'en': 1}",
        "[1, 2, 3]",
        "[None, 1, {'x': 1}]",
        "[':', ':hi', ':forced']",
        "'en'",
        "42",
        "['en:unknown']",
        "['fr:hi:bogus']",
    ]
    return [pytest.param(value, id=f"malformed-{idx}") for idx, value in enumerate(malformed_values)]


@pytest.mark.parametrize("malformed", _malformed_missing_subtitles_cases())
def test_wanted_movie_malformed_missing_subtitles_fails_safe(
    monkeypatch, malformed, wanted_module, movie_row_factory
):
    module = wanted_module
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    movie = movie_row_factory()
    movie.missing_subtitles = malformed
    generate_subtitles = Mock(return_value=iter(()))
    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)

    module._wanted_movie(movie, ["provider"])

    assert _generated_languages(generate_subtitles) == []


@pytest.mark.parametrize("malformed", _malformed_missing_subtitles_cases())
def test_wanted_episode_malformed_missing_subtitles_fails_safe(
    monkeypatch, malformed, wanted_module, episode_row_factory
):
    module = wanted_module
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    episode = episode_row_factory()
    episode.missing_subtitles = malformed
    generate_subtitles = Mock(return_value=iter(()))
    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)

    module._wanted_episode(episode, ["provider"])

    assert _generated_languages(generate_subtitles) == []


def test_wanted_movie_ignores_empty_base_language_tokens(monkeypatch, wanted_module, movie_row_factory):
    module = wanted_module
    movie = movie_row_factory()
    movie.missing_subtitles = "[':hi', '', ':forced', 'en', 'fr:forced']"
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    module._wanted_movie(movie, ["provider"])

    assert _generated_languages(generate_subtitles) == [("en", "False", "False"), ("fr", "False", "True")]


def test_wanted_episode_ignores_empty_base_language_tokens(monkeypatch, wanted_module, episode_row_factory):
    module = wanted_module
    episode = episode_row_factory()
    episode.missing_subtitles = "[':hi', '', ':forced', 'en:hi', 'fr']"
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    module._wanted_episode(episode, ["provider"])

    assert _generated_languages(generate_subtitles) == [("en", "True", "False"), ("fr", "False", "False")]


def test_wanted_movie_normalizes_whitespace_in_language_tokens(monkeypatch, wanted_module, movie_row_factory):
    module = wanted_module
    movie = movie_row_factory()
    movie.missing_subtitles = "[' en ', ' fr:forced ', ' de:hi  ']"
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    module._wanted_movie(movie, ["provider"])

    assert _generated_languages(generate_subtitles) == [
        ("en", "False", "False"),
        ("fr", "False", "True"),
        ("de", "True", "False"),
    ]


def test_wanted_episode_normalizes_whitespace_in_language_tokens(monkeypatch, wanted_module, episode_row_factory):
    module = wanted_module
    episode = episode_row_factory()
    episode.missing_subtitles = "[' en:hi ', ' fr ', ' de:forced  ']"
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    module._wanted_episode(episode, ["provider"])

    assert _generated_languages(generate_subtitles) == [
        ("en", "True", "False"),
        ("fr", "False", "False"),
        ("de", "False", "True"),
    ]


@pytest.mark.parametrize(
    "kind",
    ["movies", "series"],
)
def test_wanted_handles_multi_colon_language_codes(
    monkeypatch, kind, wanted_module, row_factory
):
    """Language codes with multiple colons should parse all trailing parts as flags"""
    module = wanted_module
    item = row_factory()
    item.missing_subtitles = "['en:hi:forced', 'fr:forced:hi']"
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    _run_wanted_worker(wanted_module, kind, item)

    assert _generated_languages(generate_subtitles) == [("en", "True", "True"), ("fr", "True", "True")]


def test_wanted_movie_handles_colon_only_language(monkeypatch, wanted_module, movie_row_factory):
    """Language code that is only a colon should fail safe"""
    module = wanted_module
    movie = movie_row_factory()
    movie.missing_subtitles = "[':', ':hi', ':forced']"
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    module._wanted_movie(movie, ["provider"])

    assert _generated_languages(generate_subtitles) == []


@pytest.mark.parametrize(
    "kind,missing_subtitles,expected",
    [
        (
            "movies",
            "['en', 'en', 'en:hi', 'en:hi', 'fr:forced', 'fr:forced']",
            [("en", "False", "False"), ("en", "True", "False"), ("fr", "False", "True")],
        ),
        (
            "series",
            "['en', 'en', 'en:hi', 'en:hi', 'fr:forced', 'fr:forced']",
            [("en", "False", "False"), ("en", "True", "False"), ("fr", "False", "True")],
        ),
        (
            "movies",
            "['en:HI', 'fr:FORCED', 'de:Hi:Forced']",
            [("en", "True", "False"), ("fr", "False", "True"), ("de", "True", "True")],
        ),
        (
            "series",
            "['en:HI', 'fr:FORCED', 'de:Hi:Forced']",
            [("en", "True", "False"), ("fr", "False", "True"), ("de", "True", "True")],
        ),
    ],
)
def test_wanted_normalizes_and_deduplicates_missing_languages(
    monkeypatch, kind, wanted_module, row_factory, missing_subtitles, expected
):
    module = wanted_module
    item = row_factory()
    item.missing_subtitles = missing_subtitles
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(module, "generate_subtitles", generate_subtitles)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)

    _run_wanted_worker(wanted_module, kind, item)

    assert _generated_languages(generate_subtitles) == expected


@pytest.mark.parametrize(
    "kind,missing_subtitles,expected_calls",
    [
        ("movies", "['en', 'fr:forced']", [("en", "seed"), ("fr:forced", "seed|en")]),
        ("series", "['en', 'fr:hi']", [("en", "seed"), ("fr:hi", "seed|en")]),
    ],
)
def test_wanted_chains_failed_attempt_updates_across_languages(
    monkeypatch, kind, wanted_module, row_factory, missing_subtitles, expected_calls
):
    module = wanted_module
    item = row_factory()
    item.missing_subtitles = missing_subtitles
    item.failedAttempts = "seed"
    update_failed_attempts_calls = []

    monkeypatch.setattr(module, "generate_subtitles", Mock(return_value=iter(())))
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)
    monkeypatch.setattr(module, "updateFailedAttempts", partial(_capture_update_failed_attempts, update_failed_attempts_calls))

    _run_wanted_worker(wanted_module, kind, item)

    assert update_failed_attempts_calls == expected_calls


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_stamps_canonical_language_tokens(monkeypatch, kind, wanted_module, row_factory):
    module = wanted_module
    item = row_factory()
    item.missing_subtitles = "[' EN : HI : Forced ', 'fr:FORCED']"
    update_failed_attempts_calls = []

    monkeypatch.setattr(module, "generate_subtitles", Mock(return_value=iter(())))
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "is_search_active", _search_always_active)
    monkeypatch.setattr(module, "updateFailedAttempts", partial(_capture_update_failed_attempts, update_failed_attempts_calls))
    _run_wanted_worker(wanted_module, kind, item)

    assert [item[0] for item in update_failed_attempts_calls] == ["en:forced:hi", "fr:forced"]
