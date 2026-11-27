import json

import pytest

from app import database


@pytest.mark.parametrize("profile_id", [None, "null", "not-an-id", []])
def test_profile_cutoff_rejects_invalid_id_before_loading_profiles(monkeypatch, profile_id):
    def unexpected_load():
        pytest.fail("invalid IDs should not load profiles")
    monkeypatch.setattr(database, "update_profile_id_list", unexpected_load)
    assert database.get_profile_cutoff(profile_id) is None


@pytest.mark.parametrize("cutoff, expected", [(1, [1]), (65535, [1, 2]), (3, []), (None, [])])
def test_profile_cutoff_uses_named_fields(monkeypatch, cutoff, expected):
    items = [{"id": 1, "language": "en"}, {"id": 2, "language": "fr"}]
    # Reordered keys and additional metadata must not alter the profile contract.
    groups = [{"id": 1, "operator": "AND", "items": [items[0]]}, {"id": 2, "operator": "AND", "items": [items[1]]}]
    monkeypatch.setattr(database, "update_profile_id_list", lambda: [
        {"items": items, "groups": groups, "extra": "metadata", "cutoff": cutoff, "profileId": 11},
    ])
    result = database.get_profile_cutoff("11")
    assert [item["id"] for item in result or []] == expected


def test_profile_cutoff_ignores_invalid_items(monkeypatch):
    monkeypatch.setattr(database, "update_profile_id_list", lambda: [
        {"profileId": 11, "cutoff": 65535, "items": [None, {"id": 1}], "groups": []},
    ])
    assert database.get_profile_cutoff(11) == [{"id": 1}]


def _item(item_id, language):
    return {"id": item_id, "language": language, "hi": "False", "forced": "False",
            "audio_exclude": "False", "audio_only_include": "False"}


ENHANCED_GROUPS = [
    {"id": 1, "operator": "AND", "items": [_item(1, "en"), _item(2, "fr")]},
    {"id": 2, "operator": "OR", "items": [_item(3, "de")]},
]


def _enhanced_profile(profile_id, cutoff):
    return {
        "profileId": profile_id, "cutoff": cutoff, "profileType": "enhanced",
        "items": [item for group in ENHANCED_GROUPS for item in group["items"]],
        "groups": ENHANCED_GROUPS,
    }


def test_parse_profile_items_flattens_groups():
    raw = json.dumps({"groups": ENHANCED_GROUPS})
    items, groups = database.parse_profile_items(raw)
    assert [item["id"] for item in items] == [1, 2, 3]
    assert groups == ENHANCED_GROUPS


def test_parse_profile_items_without_groups_is_empty():
    assert database.parse_profile_items(json.dumps({"groups": []})) == ([], [])
    assert database.parse_profile_items(json.dumps([_item(1, "en")])) == ([], [])


@pytest.mark.parametrize("cutoff, expected", [(1, [1, 2]), (2, [3]), (65535, [1, 2, 3]), (9, None), (None, None)])
def test_profile_cutoff_for_enhanced_profile_uses_group_id(monkeypatch, cutoff, expected):
    monkeypatch.setattr(database, "update_profile_id_list", lambda: [_enhanced_profile(5, cutoff)])
    result = database.get_profile_cutoff(5)
    ids = None if result is None else [item["id"] for item in result]
    assert ids == expected


@pytest.fixture
def profiles_session(memory_session, monkeypatch):
    monkeypatch.setattr(database, "database", memory_session)
    database.update_profile_id_list.invalidate()
    yield memory_session
    database.update_profile_id_list.invalidate()


def test_update_profile_id_list_exposes_profile_type_and_groups(profiles_session):
    profiles_session.add(database.TableLanguagesProfiles(
        profileId=2, name="Enhanced", cutoff=2, items=json.dumps({"groups": ENHANCED_GROUPS}),
        profileType="enhanced"))
    profiles_session.commit()

    profiles = {profile["profileId"]: profile for profile in database.update_profile_id_list()}

    assert profiles[2]["profileType"] == "enhanced"
    assert profiles[2]["groups"] == ENHANCED_GROUPS
    assert [item["id"] for item in profiles[2]["items"]] == [1, 2, 3]


def test_new_profile_defaults_to_enhanced_type(profiles_session):
    profiles_session.add(database.TableLanguagesProfiles(profileId=3, name="Default", items="[]"))
    profiles_session.commit()
    assert profiles_session.execute(
        database.select(database.TableLanguagesProfiles.profileType)
        .where(database.TableLanguagesProfiles.profileId == 3)).scalar_one() == "enhanced"
