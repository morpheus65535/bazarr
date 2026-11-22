# -*- coding: utf-8 -*-
"""
Tests for subtitle upgrade helpers and the minimum score rule in subtitles/upgrade.py.

The minimum score passed to the provider search is max(previous score, minimum_score
percentage of score_out_of). Commit 4fbed3043 replaced a hardcoded previous score + 1.
"""
from types import SimpleNamespace
from unittest import mock

import pytest
from subliminal_patch.score import MAX_SCORES

from constants import HI_EXCLUDED
from subtitles import upgrade


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


# parse_language_string

@pytest.mark.parametrize(
    "language_string, expected",
    [
        ("en", ["en", "False", "False"]),
        ("en:hi", ["en", "False", "True"]),
        ("en:forced", ["en", "True", "False"]),
        ("pt-BR", ["pt-BR", "False", "False"]),
    ],
)
def test_parse_language_string(language_string, expected):
    assert upgrade.parse_language_string(language_string) == expected


# _language_from_items

def test_language_from_items_forced_item_yields_forced_token():
    items = [{"language": "en", "forced": "True", "hi": "False"}]

    assert upgrade._language_from_items(items) == ["en:forced"]


def test_language_from_items_hi_item_yields_hi_token():
    items = [{"language": "fr", "forced": "False", "hi": "True"}]

    assert upgrade._language_from_items(items) == ["fr:hi"]


def test_language_from_items_hi_excluded_yields_plain_token():
    items = [{"language": "de", "forced": "False", "hi": HI_EXCLUDED}]

    assert upgrade._language_from_items(items) == ["de"]


def test_language_from_items_default_yields_plain_and_hi_tokens():
    items = [{"language": "es", "forced": "False", "hi": "False"}]

    assert upgrade._language_from_items(items) == ["es", "es:hi"]


# _language_still_desired and _is_hi_required

PROFILE = {
    "items": [
        {"language": "en", "forced": "False", "hi": "True"},
        {"language": "fr", "forced": "False", "hi": "False"},
    ]
}


def test_language_still_desired_false_without_profile():
    with mock.patch.object(upgrade, "get_profiles_list") as get_profile:
        assert upgrade._language_still_desired("en", None) is False

    get_profile.assert_not_called()


def test_language_still_desired_matches_profile_item():
    with mock.patch.object(upgrade, "get_profiles_list", return_value=PROFILE):
        assert upgrade._language_still_desired("fr", 1) is True
        assert upgrade._language_still_desired("de", 1) is False


def test_language_still_desired_false_when_profile_missing():
    with mock.patch.object(upgrade, "get_profiles_list", return_value=None):
        assert upgrade._language_still_desired("fr", 99) is False


def test_is_hi_required_true_only_for_hi_items():
    with mock.patch.object(upgrade, "get_profiles_list", return_value=PROFILE):
        assert upgrade._is_hi_required("en", 1) is True
        assert upgrade._is_hi_required("en:hi", 1) is True
        assert upgrade._is_hi_required("fr", 1) is False


# Minimum score in the upgrade jobs

MINIMUM_SCORE = 90


@pytest.fixture
def upgrade_settings():
    general = _Section(
        minimum_score=MINIMUM_SCORE,
        minimum_score_movie=MINIMUM_SCORE,
        upgrade_subs=True,
    )
    with mock.patch.object(upgrade, "settings", SimpleNamespace(general=general)):
        yield general


@pytest.fixture
def job_environment():
    """Patch every side effect of the upgrade jobs and expose the generate_subtitles mock."""
    job = mock.MagicMock()
    job.cancel_event.is_set.return_value = False
    jobs_queue = mock.MagicMock()
    jobs_queue.get_job.return_value = job

    patches = {
        "jobs_queue": mock.patch.object(upgrade, "jobs_queue", jobs_queue),
        "providers": mock.patch.object(upgrade, "get_providers", return_value=["opensubtitles"]),
        "audio": mock.patch.object(upgrade, "get_audio_profile_languages", return_value=[]),
        "hi": mock.patch.object(upgrade, "_is_hi_required", return_value=False),
        "generate": mock.patch.object(upgrade, "generate_subtitles", return_value=[]),
        "store": mock.patch.object(upgrade, "store_subtitles"),
        "store_movie": mock.patch.object(upgrade, "store_subtitles_movie"),
        "history": mock.patch.object(upgrade, "history_log"),
        "history_movie": mock.patch.object(upgrade, "history_log_movie"),
        "notify": mock.patch.object(upgrade, "send_notifications"),
        "notify_movie": mock.patch.object(upgrade, "send_notifications_movie"),
        "event": mock.patch.object(upgrade, "event_stream"),
        "mappings": mock.patch.object(upgrade, "path_mappings", mock.MagicMock(**{
            "path_replace.side_effect": lambda p: p,
            "path_replace_movie.side_effect": lambda p: p,
        })),
    }
    started = {name: p.start() for name, p in patches.items()}
    try:
        yield SimpleNamespace(generate=started["generate"], jobs_queue=jobs_queue)
    finally:
        for p in patches.values():
            p.stop()


def _episode_row(**overrides):
    row = dict(
        id=10, seriesTitle="Show", season=1, episode=2, title="Pilot", language="en",
        audio_language="", video_path="/tv/show/ep.mkv", sceneName="ep", score=50,
        score_out_of=120, sonarrEpisodeId=5, sonarrSeriesId=3, subtitles_path="/tv/show/ep.en.srt",
        path="/tv/show/ep.mkv", profileId=1, external_subtitles="/tv/show/ep.en.srt",
    )
    row.update(overrides)
    return SimpleNamespace(**row)


def _movie_row(**overrides):
    row = dict(
        id=20, title="Movie", language="en", audio_language="", video_path="/movies/m.mkv",
        sceneName="m", score=50, score_out_of=120, radarrId=7, path="/movies/m.mkv", profileId=1,
        subtitles_path="/movies/m.en.srt", external_subtitles="/movies/m.en.srt",
    )
    row.update(overrides)
    return SimpleNamespace(**row)


def _run_job(rows, runner, upgradable_ids):
    """Run an upgrade job against the given rows, returning the forced_minimum_score it used."""
    with mock.patch.object(upgrade, "database") as database, \
            mock.patch.object(upgrade, "_language_still_desired", return_value=True), \
            mock.patch.object(upgrade, "get_upgradable_episode_subtitles", return_value=upgradable_ids), \
            mock.patch.object(upgrade, "get_upgradable_movies_subtitles", return_value=upgradable_ids):
        database.execute.return_value.all.return_value = rows
        runner(job_id="job-1")


def _used_minimum_score(environment):
    environment.generate.assert_called_once()
    return environment.generate.call_args.kwargs["forced_minimum_score"]


def test_episode_minimum_score_uses_out_of_when_higher(upgrade_settings, job_environment):
    _run_job([_episode_row(score=50, score_out_of=120)], upgrade.upgrade_episodes_subtitles, {10: None})

    assert _used_minimum_score(job_environment) == round(MINIMUM_SCORE * 120 / 100)


def test_episode_minimum_score_keeps_previous_score_when_higher(upgrade_settings, job_environment):
    _run_job([_episode_row(score=200, score_out_of=120)], upgrade.upgrade_episodes_subtitles, {10: None})

    assert _used_minimum_score(job_environment) == 200


def test_episode_minimum_score_falls_back_to_max_scores_without_out_of(upgrade_settings, job_environment):
    _run_job([_episode_row(score=1, score_out_of=None)], upgrade.upgrade_episodes_subtitles, {10: None})

    assert _used_minimum_score(job_environment) == round(MINIMUM_SCORE * MAX_SCORES["episode"] / 100)


def test_movie_minimum_score_uses_out_of_when_higher(upgrade_settings, job_environment):
    _run_job([_movie_row(score=50, score_out_of=120)], upgrade.upgrade_movies_subtitles, {20: None})

    assert _used_minimum_score(job_environment) == round(MINIMUM_SCORE * 120 / 100)


def test_movie_minimum_score_falls_back_to_max_scores_without_out_of(upgrade_settings, job_environment):
    _run_job([_movie_row(score=1, score_out_of=None)], upgrade.upgrade_movies_subtitles, {20: None})

    assert _used_minimum_score(job_environment) == round(MINIMUM_SCORE * MAX_SCORES["movie"] / 100)


def test_episode_job_skips_subtitles_no_longer_upgradable(upgrade_settings, job_environment):
    _run_job([_episode_row()], upgrade.upgrade_episodes_subtitles, {})

    job_environment.generate.assert_not_called()


def test_episode_job_skips_subtitles_missing_from_disk(upgrade_settings, job_environment):
    row = _episode_row(external_subtitles=None)

    _run_job([row], upgrade.upgrade_episodes_subtitles, {10: None})

    job_environment.generate.assert_not_called()
