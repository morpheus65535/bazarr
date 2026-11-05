# -*- coding: utf-8 -*-
"""
Tests for the health checks in utilities/health.py, run against an in-memory database.
"""
import json
from types import SimpleNamespace
from unittest import mock

import pytest

from app.database import (TableLanguagesProfiles, TableMovies, TableMoviesRootfolder, TableShows,
                          TableShowsRootfolder)
from utilities import health


class _Section(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


@pytest.fixture
def health_settings(monkeypatch):
    fake = SimpleNamespace(general=_Section(
        use_sonarr=True, use_radarr=True,
        serie_default_enabled=False, serie_default_profile="",
        movie_default_enabled=False, movie_default_profile="",
    ))
    monkeypatch.setattr(health, "settings", fake)
    monkeypatch.setattr(health, "path_mappings", mock.MagicMock(
        path_replace=lambda p: p, path_replace_movie=lambda p: p))
    return fake


@pytest.fixture
def db(memory_session, monkeypatch):
    monkeypatch.setattr(health, "database", memory_session)
    return memory_session


def _profile(db, profile_id, name, items, cutoff=None):
    db.add(TableLanguagesProfiles(profileId=profile_id, name=name, cutoff=cutoff,
                                  items=json.dumps(items)))
    db.commit()


def _issues(issues):
    return {(issue["object"], issue["issue"]) for issue in issues}


# get_health_issues: rootfolders

def test_inaccessible_sonarr_rootfolder_is_reported(db, health_settings):
    health_settings.general["use_radarr"] = False
    _profile(db, 1, "Default", [{"id": 1, "language": "en", "forced": "False", "hi": "False"}])
    db.add(TableShowsRootfolder(id=1, path="/tv", accessible=0, error="offline"))
    db.commit()

    issues = health.get_health_issues()

    assert ("/tv", "offline") in _issues(issues)


def test_inaccessible_radarr_rootfolder_is_reported(db, health_settings):
    health_settings.general["use_sonarr"] = False
    _profile(db, 1, "Default", [{"id": 1, "language": "en", "forced": "False", "hi": "False"}])
    db.add(TableMoviesRootfolder(id=1, path="/movies", accessible=0, error="denied"))
    db.commit()

    assert ("/movies", "denied") in _issues(health.get_health_issues())


def test_rootfolder_of_disabled_integration_is_ignored(db, health_settings):
    health_settings.general["use_sonarr"] = False
    health_settings.general["use_radarr"] = False
    _profile(db, 1, "Default", [{"id": 1, "language": "en", "forced": "False", "hi": "False"}])
    db.add(TableShowsRootfolder(id=1, path="/tv", accessible=0, error="offline"))
    db.commit()

    assert health.get_health_issues() == []


# get_health_issues: languages profiles

def test_missing_languages_profile_is_reported(db, health_settings):
    health_settings.general["use_sonarr"] = False
    health_settings.general["use_radarr"] = False

    issues = health.get_health_issues()

    assert [issue["object"] for issue in issues] == ["Missing languages profile"]


def test_duplicate_profile_ids_with_cutoff_are_reported(db, health_settings):
    health_settings.general["use_sonarr"] = False
    health_settings.general["use_radarr"] = False
    items = [{"id": 1, "language": "en"}, {"id": 1, "language": "fr"}]
    _profile(db, 1, "Broken", items, cutoff=1)

    assert ("Broken", "This languages profile has duplicate IDs. You need to edit this profile and make sure "
                       "to select the proper cutoff if required.") in _issues(health.get_health_issues())


def test_duplicate_profile_ids_without_cutoff_are_ignored(db, health_settings):
    health_settings.general["use_sonarr"] = False
    health_settings.general["use_radarr"] = False
    items = [{"id": 1, "language": "en"}, {"id": 1, "language": "fr"}]
    _profile(db, 1, "Tolerated", items, cutoff=None)

    assert health.get_health_issues() == []


def test_unassigned_profile_is_reported_when_no_default_exists(db, health_settings):
    health_settings.general["use_radarr"] = False
    health_settings.general["serie_default_enabled"] = True
    health_settings.general["serie_default_profile"] = ""
    _profile(db, 1, "Default", [{"id": 1, "language": "en", "forced": "False", "hi": "False"}])

    issues = health.get_health_issues()

    assert [issue["object"] for issue in issues] == ["No assigned languages profile"]


def test_assigned_profile_clears_unassigned_warning(db, health_settings):
    health_settings.general["use_radarr"] = False
    health_settings.general["serie_default_enabled"] = True
    _profile(db, 1, "Default", [{"id": 1, "language": "en", "forced": "False", "hi": "False"}])
    db.add(TableShows(path="/tv/show", sonarrSeriesId=1, title="Show", profileId=1))
    db.commit()

    assert health.get_health_issues() == []


def test_healthy_install_reports_nothing(db, health_settings):
    health_settings.general["use_sonarr"] = False
    health_settings.general["use_radarr"] = False
    _profile(db, 1, "Default", [{"id": 1, "language": "en", "forced": "False", "hi": "False"}])

    assert health.get_health_issues() == []


# check_health

@pytest.fixture
def check_env(health_settings, monkeypatch):
    env = SimpleNamespace(
        jobs_queue=mock.MagicMock(), event_stream=mock.MagicMock(),
        sonarr=mock.MagicMock(), radarr=mock.MagicMock(), backup=mock.MagicMock(),
    )
    monkeypatch.setattr(health, "jobs_queue", env.jobs_queue)
    monkeypatch.setattr(health, "event_stream", env.event_stream)
    monkeypatch.setattr(health, "check_sonarr_rootfolder", env.sonarr)
    monkeypatch.setattr(health, "check_radarr_rootfolder", env.radarr)
    monkeypatch.setattr("utilities.backup.backup_rotation", env.backup)
    return env


def test_check_health_without_job_id_only_queues_a_job(check_env):
    health.check_health()

    check_env.jobs_queue.add_job_from_function.assert_called_once()
    check_env.sonarr.assert_not_called()
    check_env.backup.assert_not_called()


def test_check_health_runs_enabled_checks_and_rotates_backups(check_env, health_settings):
    health.check_health(job_id="job-1")

    check_env.sonarr.assert_called_once()
    check_env.radarr.assert_called_once()
    check_env.backup.assert_called_once()
    check_env.event_stream.assert_called_with(type="badges")
    check_env.jobs_queue.update_job_name.assert_called_once_with(job_id="job-1", new_job_name="Checked Health")


def test_check_health_skips_checks_for_disabled_integrations(check_env, health_settings):
    health_settings.general["use_sonarr"] = False
    health_settings.general["use_radarr"] = False

    health.check_health(job_id="job-1")

    check_env.sonarr.assert_not_called()
    check_env.radarr.assert_not_called()
    check_env.backup.assert_called_once()
