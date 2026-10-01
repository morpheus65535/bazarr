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
