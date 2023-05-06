import inspect

from subliminal_patch.core import Language

from bazarr.app import get_providers


def test_get_providers_auth():
    for val in get_providers.get_providers_auth().values():
        assert isinstance(val, dict)


def test_get_providers_auth_with_provider_registry():
    """Make sure all providers will be properly initialized with bazarr
    configs"""
    from subliminal_patch.extensions import provider_registry

    auths = get_providers.get_providers_auth()
    for key, val in auths.items():
        provider = provider_registry[key]
        sign = inspect.signature(provider.__init__)
        for sub_key in val.keys():
            if sub_key not in sign.parameters:
                raise ValueError(f"'{sub_key}' parameter not present in {provider}")

            assert sign.parameters[sub_key] is not None


def test_get_providers_auth_embeddedsubtitles():
    item = get_providers.get_providers_auth()["embeddedsubtitles"]
    assert isinstance(item["included_codecs"], list)
    assert isinstance(item["hi_fallback"], bool)
    assert isinstance(item["cache_dir"], str)
    assert isinstance(item["ffprobe_path"], str)
    assert isinstance(item["ffmpeg_path"], str)
    assert isinstance(item["timeout"], str)
    assert isinstance(item["unknown_as_english"], bool)


def test_get_providers_auth_karagarga():
    item = get_providers.get_providers_auth()["karagarga"]
    assert item["username"] is not None
    assert item["password"] is not None
    assert item["f_username"] is not None
    assert item["f_password"] is not None


def test_get_language_equals_default_settings():
    assert isinstance(get_providers.get_language_equals(), list)


def test_get_language_equals_injected_settings_invalid():
    config = get_providers.settings
    config.set("general", "language_equals", '["invalid"]')
    assert not get_providers.get_language_equals(config)


def test_get_language_equals_injected_settings_valid():
    config = get_providers.settings
    config.set("general", "language_equals", '["spa:spa-MX"]')

    result = get_providers.get_language_equals(config)
    assert result == [(Language("spa"), Language("spa", "MX"))]


def test_get_language_equals_injected_settings_valid_multiple():
    config = get_providers.settings
    config.set("general", "language_equals", '["spa:spa-MX", "spa-MX:spa"]')

    result = get_providers.get_language_equals(config)
    assert result == [
        (Language("spa"), Language("spa", "MX")),
        (Language("spa", "MX"), Language("spa")),
    ]


def test_get_language_equals_injected_settings_hi():
    config = get_providers.settings
    config.set("general", "language_equals", '["eng@hi:eng"]')

    result = get_providers.get_language_equals(config)
    assert result == [(Language("eng", hi=True), Language("eng"))]
