"""
Tests for saving languages profiles through the system settings endpoint.

Invalid enhanced profiles must be rejected before anything is written, and valid enhanced
profiles must be stored with their profile type and groups.
"""
import copy
import json

import pytest

import api.system.settings as settings_api
from app.database import TableLanguagesProfiles, select


def _item(item_id, language, **overrides):
    item = {"id": item_id, "language": language, "hi": "False", "forced": "False",
            "audio_exclude": "False", "audio_only_include": "False"}
    item.update(overrides)
    return item


def _enhanced_profile(**overrides):
    profile = {
        "profileId": 9, "name": "Enhanced", "cutoff": 2, "profileType": "enhanced",
        "items": {"groups": [
            {"id": 1, "operator": "AND", "items": [_item(1, "en"), _item(2, "fr")]},
            {"id": 2, "operator": "OR", "items": [_item(3, "de")]},
        ]},
        "mustContain": [], "mustNotContain": [], "originalFormat": None, "tag": None,
    }
    profile.update(overrides)
    return profile


def _with_groups(mutate):
    profile = _enhanced_profile()
    mutate(profile["items"]["groups"])
    return profile


INVALID_PROFILES = {
    "no groups": _enhanced_profile(items={"groups": []}),
    "items not an object": _enhanced_profile(items=[_item(1, "en")]),
    "duplicate group id": _with_groups(lambda groups: groups[1].update(id=1)),
    "group id 65535 is reserved": _with_groups(lambda groups: groups[1].update(id=65535)),
    "group id is a bool": _with_groups(lambda groups: groups[1].update(id=True)),
    "invalid operator": _with_groups(lambda groups: groups[0].update(operator="XOR")),
    "empty group": _with_groups(lambda groups: groups[1].update(items=[])),
    "duplicate language id across groups": _with_groups(
        lambda groups: groups[1]["items"].append(_item(1, "it"))),
    "invalid hearing-impaired value": _with_groups(
        lambda groups: groups[0]["items"].append(_item(4, "es", hi="Maybe"))),
    "invalid forced value": _with_groups(
        lambda groups: groups[0]["items"].append(_item(4, "es", forced="yes"))),
    "missing language code": _with_groups(
        lambda groups: groups[0]["items"].append(_item(4, ""))),
    "cutoff does not match a group": _enhanced_profile(cutoff=7),
    "unknown profile type": _enhanced_profile(profileType="advanced"),
}


@pytest.fixture
def saved(memory_session, monkeypatch):
    """Route the endpoint to an in-memory database and record whether settings were written."""
    calls = {"save_settings": 0}
    monkeypatch.setattr(settings_api, "database", memory_session)
    monkeypatch.setattr(settings_api, "event_stream", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_api, "list_missing_subtitles", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_api, "list_missing_subtitles_movies", lambda *args, **kwargs: None)

    def record_save(*args, **kwargs):
        calls["save_settings"] += 1
    monkeypatch.setattr(settings_api, "save_settings", record_save)
    return memory_session, calls


def _post_profiles(client, api_key, profiles, **extra_form):
    form = {"languages-profiles": json.dumps(profiles), **extra_form}
    return client.post("/api/system/settings", data=form, headers={"X-API-KEY": api_key})


@pytest.mark.parametrize("profile", INVALID_PROFILES.values(), ids=INVALID_PROFILES.keys())
def test_invalid_enhanced_profile_is_rejected_before_any_write(saved, api_client, api_key, profile):
    session, calls = saved

    response = _post_profiles(api_client, api_key, [copy.deepcopy(profile)], **{"languages-enabled": ["en"]})

    assert response.status_code == 400
    assert session.execute(select(TableLanguagesProfiles)).all() == []
    assert calls["save_settings"] == 0


def test_valid_enhanced_profile_is_stored_with_type_and_groups(saved, api_client, api_key):
    session, calls = saved

    response = _post_profiles(api_client, api_key, [_enhanced_profile()])

    assert response.status_code != 400
    row = session.execute(select(TableLanguagesProfiles).where(TableLanguagesProfiles.profileId == 9)).scalar_one()
    assert row.profileType == "enhanced"
    assert row.cutoff == 2
    assert json.loads(row.items) == _enhanced_profile()["items"]
    assert calls["save_settings"] == 1


def test_enhanced_cutoff_accepts_any_and_no_cutoff(saved, api_client, api_key):
    session, _ = saved

    for cutoff in (65535, None):
        response = _post_profiles(api_client, api_key, [_enhanced_profile(cutoff=cutoff)])
        assert response.status_code != 400
        row = session.execute(select(TableLanguagesProfiles).where(TableLanguagesProfiles.profileId == 9)).scalar_one()
        assert row.cutoff == cutoff


def test_basic_profile_without_type_is_still_saved_as_basic(saved, api_client, api_key):
    session, _ = saved
    basic = {
        "profileId": 3, "name": "Basic", "cutoff": None,
        "items": [_item(1, "en")], "mustContain": [], "mustNotContain": [],
        "originalFormat": None, "tag": None,
    }

    response = _post_profiles(api_client, api_key, [basic])

    assert response.status_code != 400
    row = session.execute(select(TableLanguagesProfiles).where(TableLanguagesProfiles.profileId == 3)).scalar_one()
    assert row.profileType == "basic"
    assert json.loads(row.items) == [_item(1, "en")]
