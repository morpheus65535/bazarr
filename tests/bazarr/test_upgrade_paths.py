from types import SimpleNamespace

import pytest

from subtitles.cache import _SubtitleCache
import subtitles.upgrade as upgrade


def _profile_with_language(language="en", forced="False", hi="False"):
    return {"items": [{"language": language, "forced": forced, "hi": hi}]}


@pytest.fixture
def upgrade_module(bind_wanted_database, monkeypatch):
    bind_wanted_database(upgrade, "movies")
    bind_wanted_database(upgrade, "series")
    monkeypatch.setattr(upgrade, "get_exclusion_clause", lambda media_type: [])
    monkeypatch.setattr(upgrade, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(upgrade.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(upgrade.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(upgrade.jobs_queue, "update_job_progress", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade.jobs_queue, "update_job_name", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade.jobs_queue, "add_job_from_function", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "event_stream", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "store_subtitles", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "store_subtitles_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "history_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "history_log_movie", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "send_notifications", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade, "send_notifications_movie", lambda *args, **kwargs: None)
    return upgrade


def test_subtitle_cache_store_purges_malformed_entries():
    cache = _SubtitleCache()
    cache._cache["bad"] = "not-a-cache-tuple"
    cache._cache["bad-expiry"] = (SimpleNamespace(id=2), object())

    key = cache.store(SimpleNamespace(id=1))

    assert "bad" not in cache._cache
    assert "bad-expiry" not in cache._cache
    assert cache.get(key).id == 1


def test_subtitle_cache_get_purges_malformed_expiry():
    cache = _SubtitleCache()
    cache._cache["bad-expiry"] = (SimpleNamespace(id=1), object())

    assert cache.get("bad-expiry") is None
    assert "bad-expiry" not in cache._cache


def test_parse_language_string_handles_non_string_input():
    assert upgrade.parse_language_string(None) == ["", "False", "False"]
    assert upgrade.parse_language_string(123) == ["", "False", "False"]
    assert upgrade.parse_language_string("  ") == ["", "False", "False"]


def test_language_profile_helpers_handle_malformed_items(monkeypatch):
    monkeypatch.setattr(
        upgrade,
        "get_profiles_list",
        lambda *args, **kwargs: {"items": [None, {"bad": "shape"}, {"language": "en", "hi": "True"}]},
    )

    assert upgrade._language_still_desired("en:hi", 10) is True
    assert upgrade._is_hi_required("en:forced", 10) is True
    assert upgrade._language_from_items([None, {"language": None}, {"language": "fr", "forced": "True"}]) == [
        "fr:forced"
    ]


def test_upgrade_movies_subtitles_handles_none_audio_list_and_result_without_message(
    upgrade_module,
    movie_row_factory,
    movie_history_row_factory,
    movie_subtitle_row_factory,
    monkeypatch,
):
    movie_row_factory(radarrId=7, path="/movies/movie.mkv", profileId=44)
    movie_history_row_factory(
        id=10,
        language="en",
        score=None,
        video_path="/movies/movie.mkv",
        subtitles_path="/movies/sub.srt",
        radarrId=7,
    )
    movie_subtitle_row_factory(radarrId=7, path="/movies/sub.srt")
    stored = []
    history_calls = []
    notifications = []
    generate_calls = []

    monkeypatch.setattr(upgrade_module, "get_upgradable_movies_subtitles", lambda history_id_list=None: {10: None})
    monkeypatch.setattr(upgrade_module, "get_profiles_list", lambda *args, **kwargs: _profile_with_language())
    monkeypatch.setattr(upgrade_module, "get_audio_profile_languages", lambda audio_language: None)
    monkeypatch.setattr(
        upgrade_module,
        "generate_subtitles",
        lambda *args, **kwargs: generate_calls.append((args, kwargs)) or [SimpleNamespace()],
    )
    monkeypatch.setattr(upgrade_module, "store_subtitles_movie", lambda movie_id: stored.append(movie_id))
    monkeypatch.setattr(
        upgrade_module,
        "history_log_movie",
        lambda *args, **kwargs: history_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        upgrade_module,
        "send_notifications_movie",
        lambda *args, **kwargs: notifications.append(args),
    )

    upgrade_module.upgrade_movies_subtitles(job_id="job")

    assert stored == [7]
    assert len(history_calls) == 1
    assert notifications == []
    assert generate_calls[0][1]["forced_minimum_score"] is None


def test_upgrade_episodes_subtitles_handles_none_score(
    upgrade_module,
    show_row_factory,
    episode_row_factory,
    episode_history_row_factory,
    episode_subtitle_row_factory,
    monkeypatch,
):
    show_row_factory(sonarrSeriesId=3, title="Series", profileId=44)
    episode_row_factory(
        sonarrSeriesId=3,
        sonarrEpisodeId=17,
        path="/series/e01.mkv",
        profileId=44,
        season="special",
        episode=None,
    )
    episode_history_row_factory(
        id=10,
        language="en",
        score=None,
        video_path="/series/e01.mkv",
        subtitles_path="/series/sub.srt",
        sonarrSeriesId=3,
        sonarrEpisodeId=17,
    )
    episode_subtitle_row_factory(sonarrEpisodeId=17, path="/series/sub.srt")
    stored = []
    history_calls = []
    notifications = []
    generate_calls = []
    progress_messages = []

    monkeypatch.setattr(upgrade_module, "get_upgradable_episode_subtitles", lambda history_id_list=None: {10: None})
    monkeypatch.setattr(upgrade_module, "get_profiles_list", lambda *args, **kwargs: _profile_with_language())
    monkeypatch.setattr(upgrade_module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(
        upgrade_module,
        "generate_subtitles",
        lambda *args, **kwargs: generate_calls.append((args, kwargs)) or [SimpleNamespace()],
    )
    monkeypatch.setattr(upgrade_module, "store_subtitles", lambda episode_id: stored.append(episode_id))
    monkeypatch.setattr(
        upgrade_module,
        "history_log",
        lambda *args, **kwargs: history_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        upgrade_module,
        "send_notifications",
        lambda *args, **kwargs: notifications.append(args),
    )
    monkeypatch.setattr(
        upgrade_module.jobs_queue,
        "update_job_progress",
        lambda *args, **kwargs: progress_messages.append(kwargs.get("progress_message")),
    )

    upgrade_module.upgrade_episodes_subtitles(job_id="job")

    assert stored == [17]
    assert len(history_calls) == 1
    assert notifications == []
    assert generate_calls[0][1]["forced_minimum_score"] is None
    assert "Series - SspecialE?? - Pilot" in progress_messages


def test_upgrade_movies_subtitles_skips_empty_parsed_language(
    upgrade_module,
    movie_row_factory,
    movie_history_row_factory,
    movie_subtitle_row_factory,
    monkeypatch,
):
    movie_row_factory(radarrId=7, path="/movies/movie.mkv", profileId=44)
    movie_history_row_factory(
        id=10,
        language="en",
        video_path="/movies/movie.mkv",
        subtitles_path="/movies/sub.srt",
        radarrId=7,
    )
    movie_subtitle_row_factory(radarrId=7, path="/movies/sub.srt")
    generate_calls = []

    monkeypatch.setattr(upgrade_module, "get_upgradable_movies_subtitles", lambda history_id_list=None: {10: None})
    monkeypatch.setattr(upgrade_module, "get_profiles_list", lambda *args, **kwargs: _profile_with_language())
    monkeypatch.setattr(upgrade_module, "get_audio_profile_languages", lambda audio_language: [{"name": "English"}])
    monkeypatch.setattr(upgrade_module, "parse_language_string", lambda value: ["", "False", "False"])
    monkeypatch.setattr(
        upgrade_module,
        "generate_subtitles",
        lambda *args, **kwargs: generate_calls.append((args, kwargs)) or [SimpleNamespace()],
    )

    upgrade_module.upgrade_movies_subtitles(job_id="job")

    assert generate_calls == []
