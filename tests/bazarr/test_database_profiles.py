from app.database import _normalize_profile_items


def test_normalize_profile_items_converts_legacy_boolean_strings():
    items = [
        {
            "id": 1,
            "language": "en",
            "forced": "True",
            "hi": "False",
            "audio_exclude": True,
            "audio_only_include": False,
        },
    ]

    assert _normalize_profile_items(items) == [
        {
            "id": 1,
            "language": "en",
            "forced": True,
            "hi": False,
            "audio_exclude": True,
            "audio_only_include": False,
        },
    ]


def test_normalize_profile_items_ignores_invalid_items():
    assert _normalize_profile_items(None) == []
    assert _normalize_profile_items([None, "en", {"language": "fr"}]) == [{"language": "fr"}]
