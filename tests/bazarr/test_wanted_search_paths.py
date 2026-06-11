from functools import partial

import pytest


def _english_audio_languages(audio_language):
    return [{"name": "English"}]


def _search_always_active(desired_language, attempt_string):
    return True


def _search_never_active(desired_language, attempt_string):
    return False


def _malformed_audio_languages(audio_language):
    return [None, {"bad": "shape"}]


def _search_matches(active_language):
    def _is_search_active(desired_language, attempt_string):
        return desired_language == active_language

    return _is_search_active


def _capture_generate_subtitles(calls, *args, **kwargs):
    calls.append((args, kwargs))
    return iter(())


def _capture_update_failed_attempts(calls, desired_language, attempt_string):
    calls.append((desired_language, attempt_string))
    return f"{attempt_string}|{desired_language}"


def _captured_languages(generate_calls):
    return generate_calls[0][0][1]


def _captured_audio_language(generate_calls):
    return generate_calls[0][0][2]


def _captured_scene_name(generate_calls):
    return generate_calls[0][0][3]


def _run_wanted_worker(wanted_module, kind, row, providers=None):
    if providers is None:
        providers = ["provider"]
    if kind == "movies":
        wanted_module._wanted_movie(row, providers)
    else:
        wanted_module._wanted_episode(row, providers)


@pytest.mark.parametrize(
    "kind,active_language,expected",
    [
        ("movies", "fr:forced", [("fr", "False", "True")]),
        ("series", "fr:hi", [("fr", "True", "False")]),
    ],
)
def test_wanted_only_requests_due_languages(
    monkeypatch,
    wanted_module,
    row_factory,
    kind,
    active_language,
    expected,
):
    row = row_factory()
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "is_search_active", _search_matches(active_language))

    _run_wanted_worker(wanted_module, kind, row)

    assert _captured_languages(generate_calls) == expected


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_handles_malformed_audio_profile_languages(monkeypatch, wanted_module, row_factory, kind):
    row = row_factory()
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _malformed_audio_languages)
    monkeypatch.setattr(wanted_module, "is_search_active", _search_always_active)

    _run_wanted_worker(wanted_module, kind, row)

    assert _captured_audio_language(generate_calls) is None


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_uses_none_for_missing_scene_name(monkeypatch, wanted_module, row_factory, kind):
    row = row_factory(sceneName=None)
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "is_search_active", _search_always_active)

    _run_wanted_worker(wanted_module, kind, row)

    assert _captured_scene_name(generate_calls) is None


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_skips_generate_when_path_missing(monkeypatch, wanted_module, row_factory, kind):
    row = row_factory()
    row.path = None
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "is_search_active", _search_always_active)

    _run_wanted_worker(wanted_module, kind, row)

    assert generate_calls == []


def test_movie_wanted_search_falls_back_to_legacy_missing_text(monkeypatch, wanted_module, movie_row_factory):
    movie = movie_row_factory()
    generate_calls = []

    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "is_search_active", _search_always_active)

    wanted_module._wanted_movie(movie, ["provider"])

    assert _captured_languages(generate_calls) == [("en", "False", "False"), ("fr", "False", "True")]


def test_series_wanted_search_falls_back_to_legacy_missing_text(monkeypatch, wanted_module, episode_row_factory):
    episode = episode_row_factory()
    generate_calls = []

    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "is_search_active", _search_always_active)

    wanted_module._wanted_episode(episode, ["provider"])

    assert _captured_languages(generate_calls) == [("en", "False", "False"), ("fr", "True", "False")]


def test_wanted_movie_does_not_stamp_failed_attempts_when_no_providers(monkeypatch, wanted_module, movie_row_factory):
    movie = movie_row_factory()
    update_failed_attempts_calls = []

    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, []))
    monkeypatch.setattr(
        wanted_module,
        "updateFailedAttempts",
        partial(_capture_update_failed_attempts, update_failed_attempts_calls),
    )

    wanted_module._wanted_movie(movie, [])

    assert update_failed_attempts_calls == []


def test_wanted_episode_does_not_stamp_failed_attempts_when_no_providers(monkeypatch, wanted_module, episode_row_factory):
    episode = episode_row_factory()
    update_failed_attempts_calls = []

    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, []))
    monkeypatch.setattr(
        wanted_module,
        "updateFailedAttempts",
        partial(_capture_update_failed_attempts, update_failed_attempts_calls),
    )

    wanted_module._wanted_episode(episode, [])

    assert update_failed_attempts_calls == []


def test_wanted_movie_filters_out_inactive_languages_entirely(monkeypatch, wanted_module, movie_row_factory):
    movie = movie_row_factory()
    generate_calls = []

    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "is_search_active", _search_never_active)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))

    wanted_module._wanted_movie(movie, ["provider"])

    assert _captured_languages(generate_calls) == []


def test_wanted_episode_filters_out_inactive_languages_entirely(monkeypatch, wanted_module, episode_row_factory):
    episode = episode_row_factory()
    generate_calls = []

    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(wanted_module, "is_search_active", _search_never_active)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))

    wanted_module._wanted_episode(episode, ["provider"])

    assert _captured_languages(generate_calls) == []
