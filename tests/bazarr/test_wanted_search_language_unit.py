from functools import partial

import pytest


def _english_audio_languages(audio_language):
    return [{"name": "English"}]


def _malformed_audio_languages(audio_language):
    return [None, {"bad": "shape"}]


def _capture_generate_subtitles(calls, *args, **kwargs):
    calls.append((args, kwargs))
    return iter(())


def _captured_languages(generate_calls):
    return generate_calls[0][0][1]


def _captured_audio_language(generate_calls):
    return generate_calls[0][0][2]


def _run_wanted_worker(wanted_module, kind, item, providers=None, **kwargs):
    if providers is None:
        providers = ["provider"]
    if kind == "movies":
        wanted_module._wanted_movie(item, providers, **kwargs)
    else:
        wanted_module._wanted_episode(item, providers, **kwargs)


def _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, providers=None, **kwargs):
    if providers is None:
        providers = ["provider"]
    if kind == "movies":
        return wanted_download_subtitles(
            row.radarrId,
            job_id="job",
            providers_list=providers,
            movie=row,
            **kwargs,
        )
    return wanted_download_subtitles(
        row.sonarrEpisodeId,
        job_id="job",
        providers_list=providers,
        episode_details=row,
        **kwargs,
    )


def _captured_scene_name(generate_calls):
    return generate_calls[0][0][3]


@pytest.mark.parametrize(
    "kind,missing_languages,expected",
    [
        ("movies", ["en", "fr:forced"], [("en", "False", "False"), ("fr", "False", "True")]),
        ("series", ["en", "fr:hi"], [("en", "False", "False"), ("fr", "True", "False")]),
    ],
)
def test_wanted_worker_uses_normalized_missing_languages(
    monkeypatch,
    wanted_module,
    row_factory,
    wanted_download_subtitles,
    kind,
    missing_languages,
    expected,
):
    row = row_factory(missing_languages=missing_languages, failed_attempts=[])
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row)

    assert _captured_languages(generate_calls) == expected


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_worker_converts_supplied_due_languages_to_search_tuples(
    monkeypatch,
    wanted_module,
    row_factory,
    wanted_download_subtitles,
    kind,
):
    row = row_factory(missing_languages=[], failed_attempts=[])
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    if kind == "movies":
        wanted_download_subtitles(
            row.radarrId,
            job_id="job",
            providers_list=["provider"],
            movie=row,
            due_languages=["en:hi:forced", "fr:forced"],
        )
    else:
        wanted_download_subtitles(
            row.sonarrEpisodeId,
            job_id="job",
            providers_list=["provider"],
            episode_details=row,
            due_languages=["en:hi:forced", "fr:forced"],
        )

    assert _captured_languages(generate_calls) == [
        ("en", "True", "True"),
        ("fr", "False", "True"),
    ]


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_worker_handles_malformed_audio_profile_languages(
    monkeypatch, wanted_module, row_factory, wanted_download_subtitles, kind
):
    row = row_factory(missing_languages=[], failed_attempts=[])
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _malformed_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, due_languages=["en"])

    assert _captured_audio_language(generate_calls) is None


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_worker_uses_none_for_missing_scene_name(
    monkeypatch, wanted_module, row_factory, wanted_download_subtitles, kind
):
    row = row_factory(missing_languages=[], failed_attempts=[], sceneName=None)
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, due_languages=["en"])

    assert _captured_scene_name(generate_calls) is None


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_wanted_worker_skips_search_when_path_missing(
    monkeypatch, wanted_module, row_factory, wanted_download_subtitles, kind
):
    row = row_factory(missing_languages=[], failed_attempts=[])
    row.path = None
    generate_calls = []

    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generate_calls))
    monkeypatch.setattr(wanted_module, "get_audio_profile_languages", _english_audio_languages)

    _run_wanted_download_subtitles(wanted_download_subtitles, kind, row, due_languages=["en"])

    assert generate_calls == []
