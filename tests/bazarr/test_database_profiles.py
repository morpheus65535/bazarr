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
    monkeypatch.setattr(database, "update_profile_id_list", lambda: [
        {"items": items, "extra": "metadata", "cutoff": cutoff, "profileId": 11},
    ])
    result = database.get_profile_cutoff("11")
    assert [item["id"] for item in result or []] == expected


def test_profile_cutoff_ignores_invalid_items(monkeypatch):
    monkeypatch.setattr(database, "update_profile_id_list", lambda: [
        {"profileId": 11, "cutoff": 65535, "items": [None, {"id": 1}]},
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


def test_parse_profile_items_basic_returns_flat_list():
    raw = json.dumps([_item(1, "en")])
    assert database.parse_profile_items("basic", raw) == ([_item(1, "en")], None)


def test_parse_profile_items_enhanced_flattens_groups():
    raw = json.dumps({"groups": ENHANCED_GROUPS})
    items, groups = database.parse_profile_items("enhanced", raw)
    assert [item["id"] for item in items] == [1, 2, 3]
    assert groups == ENHANCED_GROUPS


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
        profileId=1, name="Basic", cutoff=None, items=json.dumps([_item(1, "en")])))
    profiles_session.add(database.TableLanguagesProfiles(
        profileId=2, name="Enhanced", cutoff=2, items=json.dumps({"groups": ENHANCED_GROUPS}),
        profileType="enhanced"))
    profiles_session.commit()

    profiles = {profile["profileId"]: profile for profile in database.update_profile_id_list()}

    assert profiles[1]["profileType"] == "basic"
    assert "groups" not in profiles[1]
    assert [item["id"] for item in profiles[1]["items"]] == [1]
    assert profiles[2]["profileType"] == "enhanced"
    assert profiles[2]["groups"] == ENHANCED_GROUPS
    assert [item["id"] for item in profiles[2]["items"]] == [1, 2, 3]


def test_new_profile_defaults_to_basic_type(profiles_session):
    profiles_session.add(database.TableLanguagesProfiles(profileId=3, name="Default", items="[]"))
    profiles_session.commit()
    assert profiles_session.execute(
        database.select(database.TableLanguagesProfiles.profileType)
        .where(database.TableLanguagesProfiles.profileId == 3)).scalar_one() == "basic"


def test_raw_json_upgrade_helpers_skip_enhanced_profiles(profiles_session):
    basic_items = [{"id": 1, "language": "en", "hi": "only", "forced": "False"}]
    profiles_session.add(database.TableLanguagesProfiles(
        profileId=1, name="Basic", cutoff=None, items=json.dumps(basic_items)))
    profiles_session.add(database.TableLanguagesProfiles(
        profileId=2, name="Enhanced", cutoff=None, items=json.dumps({"groups": ENHANCED_GROUPS}),
        profileType="enhanced"))
    profiles_session.commit()

    database.upgrade_languages_profile_values()
    database.fix_languages_profiles_with_duplicate_ids()

    stored = {row.profileId: row.items for row in profiles_session.execute(
        database.select(database.TableLanguagesProfiles.profileId, database.TableLanguagesProfiles.items))}
    assert json.loads(stored[1])[0]["hi"] == "True"
    assert json.loads(stored[2]) == {"groups": ENHANCED_GROUPS}
