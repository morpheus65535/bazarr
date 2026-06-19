from types import SimpleNamespace

import pytest

from languages import get_languages
import subtitles.manual as manual
import subtitles.utils as subtitle_utils


def _no_op(*args, **kwargs):
    return None


def _record_call(calls):
    def _inner(*args, **kwargs):
        calls.append((args, kwargs))
    return _inner


def _empty_message_result(*args, **kwargs):
    return SimpleNamespace()


@pytest.fixture
def manual_module(bind_wanted_database, monkeypatch):
    bind_wanted_database(manual, "movies")
    bind_wanted_database(manual, "series")
    monkeypatch.setattr(manual.path_mappings, "path_replace", _no_op)
    monkeypatch.setattr(manual.path_mappings, "path_replace_movie", _no_op)
    monkeypatch.setattr(manual, "store_subtitles", _no_op)
    monkeypatch.setattr(manual, "store_subtitles_movie", _no_op)
    monkeypatch.setattr(manual, "history_log", _no_op)
    monkeypatch.setattr(manual, "history_log_movie", _no_op)
    monkeypatch.setattr(manual, "send_notifications", _no_op)
    monkeypatch.setattr(manual, "send_notifications_movie", _no_op)
    monkeypatch.setattr(manual.jobs_queue, "update_job_name", _no_op)
    return manual


@pytest.fixture
def language_dictionary(monkeypatch):
    monkeypatch.setattr(
        get_languages,
        "languages_dict",
        [
            {"code2": "en", "code3": "eng", "code3b": None, "name": "English"},
            {"code2": "fr", "code3": "fra", "code3b": "fre", "name": "French"},
        ],
        raising=False,
    )


def test_get_language_obj_handles_missing_profile_payload(monkeypatch):
    monkeypatch.setattr(manual, "get_profiles_list", lambda profile_id: None)

    language_set, original_format = manual._get_language_obj(profile_id=44)

    assert language_set == set()
    assert original_format is False


def test_get_language_obj_handles_malformed_profile_items(language_dictionary, monkeypatch):
    monkeypatch.setattr(
        manual,
        "get_profiles_list",
        lambda profile_id: {
            "items": [
                None,
                {"bad": "shape"},
                {"language": None},
                {"language": "en", "forced": True, "hi": False},
                {"language": "fr", "forced": False, "hi": True},
            ],
            "originalFormat": 1,
        },
    )

    language_set, original_format = manual._get_language_obj(profile_id=44)

    assert len(language_set) == 2
    assert {language.basename for language in language_set} == {"en", "fr"}
    assert {language.forced for language in language_set} == {False, True}
    assert {language.hi for language in language_set} == {False, True}
    assert original_format == 1


def test_get_language_obj_handles_non_integer_profile_id(monkeypatch):
    monkeypatch.setattr(manual, "get_profiles_list", lambda profile_id: {"items": [], "originalFormat": 1})

    language_set, original_format = manual._get_language_obj(profile_id="not-an-int")

    assert language_set == set()
    assert original_format is False


def test_episode_manual_download_handles_none_audio_list_and_message_less_result(
    manual_module, show_row_factory, episode_row_factory, monkeypatch
):
    show_row_factory(sonarrSeriesId=5, title="Series", profileId=44)
    episode_row_factory(sonarrSeriesId=5, sonarrEpisodeId=11, title="Pilot", season=1, episode=2)
    notifications = []

    monkeypatch.setattr(manual_module.settings.general, "dont_notify_manual_actions", False)
    monkeypatch.setattr(manual_module, "get_audio_profile_languages", _no_op)
    monkeypatch.setattr(manual_module, "manual_download_subtitle", _empty_message_result)
    monkeypatch.setattr(manual_module, "send_notifications", _record_call(notifications))

    result = manual_module.episode_manually_download_specific_subtitle(
        sonarr_series_id=5,
        sonarr_episode_id=11,
        hi="False",
        forced="False",
        use_original_format="False",
        selected_provider="provider",
        subtitle="sub-id",
        job_id="job",
    )

    assert result == ("", 204)
    assert notifications == []


def test_movie_manual_download_handles_none_audio_list_and_message_less_result(
    manual_module, movie_row_factory, monkeypatch
):
    movie_row_factory(radarrId=7)
    notifications = []

    monkeypatch.setattr(manual_module.settings.general, "dont_notify_manual_actions", False)
    monkeypatch.setattr(manual_module, "get_audio_profile_languages", _no_op)
    monkeypatch.setattr(manual_module, "manual_download_subtitle", _empty_message_result)
    monkeypatch.setattr(manual_module, "send_notifications_movie", _record_call(notifications))

    result = manual_module.movie_manually_download_specific_subtitle(
        radarr_id=7,
        hi="False",
        forced="False",
        use_original_format="False",
        selected_provider="provider",
        subtitle="sub-id",
        job_id="job",
    )

    assert result == ("", 204)
    assert notifications == []
