import datetime
import inspect

import pytest
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
    assert isinstance(item["timeout"], int)
    assert isinstance(item["unknown_as_fallback"], bool)
    assert isinstance(item["fallback_lang"], str)


def test_get_providers_auth_karagarga():
    item = get_providers.get_providers_auth()["karagarga"]
    assert item["username"] is not None
    assert item["password"] is not None
    assert item["f_username"] is not None
    assert item["f_password"] is not None


@pytest.fixture(autouse=True)
def _restore_language_equals():
    """Tests below mutate the process-wide settings object; restore it afterwards."""
    original = get_providers.settings.general.language_equals
    yield
    get_providers.settings.set("general.language_equals", original)


def test_get_language_equals_default_settings():
    assert isinstance(get_providers.get_language_equals(), list)


def test_get_language_equals_injected_settings_invalid():
    config = get_providers.settings
    config.set("general.language_equals", ["invalid"])
    assert not get_providers.get_language_equals(config)


def test_get_language_equals_injected_settings_valid():
    config = get_providers.settings
    config.set("general.language_equals", ["spa:spa-MX"])

    result = get_providers.get_language_equals(config)
    assert result == [(Language("spa"), Language("spa", "MX"))]


@pytest.mark.parametrize(
    "config_value,expected",
    [
        (["spa:spl"], (Language("spa"), Language("spa", "MX"))),
        (["por:pob"], (Language("por"), Language("por", "BR"))),
        (["zho:zht"], (Language("zho"), Language("zho", "TW"))),
    ],
)
def test_get_language_equals_injected_settings_custom_lang_alpha3(
    config_value, expected
):
    config = get_providers.settings

    config.set("general.language_equals", config_value)

    result = get_providers.get_language_equals(config)
    assert result == [expected]


def test_get_language_equals_injected_settings_multiple():
    config = get_providers.settings

    config.set("general.language_equals",
               ['eng@hi:eng', 'spa:spl', 'spa@hi:spl', 'spl@hi:spl'])

    result = get_providers.get_language_equals(config)
    assert len(result) == 4


def test_get_language_equals_injected_settings_valid_multiple():
    config = get_providers.settings
    config.set("general.language_equals", ["spa:spa-MX", "spa-MX:spa"])

    result = get_providers.get_language_equals(config)
    assert result == [
        (Language("spa"), Language("spa", "MX")),
        (Language("spa", "MX"), Language("spa")),
    ]


def test_get_language_equals_injected_settings_hi():
    config = get_providers.settings
    config.set("general.language_equals", ["eng@hi:eng"])

    result = get_providers.get_language_equals(config)
    assert result == [(Language("eng", hi=True), Language("eng"))]


def _get_error():
    try:
        raise ValueError("Some error" * 100)
    except ValueError as error:
        return error


def test_get_traceback_info():
    error_ = _get_error()

    if error_ is not None:
        msg = get_providers._get_traceback_info(error_)
        assert len(msg) == 100


@pytest.fixture
def _throttle_count(monkeypatch):
    """`throttle_count` is process-wide state and `throttled_count` sleeps between retries."""
    monkeypatch.setattr(get_providers.time, "sleep", lambda seconds: None)
    get_providers.throttle_count.clear()
    yield get_providers.throttle_count
    get_providers.throttle_count.clear()


def _strikes_until_throttled(name):
    for strike in range(1, 10):
        if get_providers.throttled_count(name):
            return strike
    return None


def test_throttled_count_grants_new_retries_after_throttling(_throttle_count):
    """A provider that reached the limit once must not be throttled on sight afterwards."""
    assert _strikes_until_throttled("provider") == 5
    assert _strikes_until_throttled("provider") == 5


def test_throttled_count_ignores_failures_older_than_the_window(_throttle_count):
    """Strikes the provider collected before it went quiet must not add up to a throttle."""
    for _ in range(4):
        get_providers.throttled_count("provider")

    _throttle_count["provider"]["time"] = datetime.datetime.now() - datetime.timedelta(seconds=1)

    assert get_providers.throttled_count("provider") is False
    assert _throttle_count["provider"]["count"] == 1


def test_throttled_count_tolerates_a_concurrent_removal(monkeypatch):
    """Providers are searched in parallel, so another thread may drop the entry first."""

    class _RacingCount(dict):
        def __delitem__(self, key):
            super().__delitem__(key)
            raise KeyError(key)

    racing = _RacingCount(
        {"provider": {"count": 5, "time": datetime.datetime.now() + datetime.timedelta(seconds=120)}}
    )
    monkeypatch.setattr(get_providers, "throttle_count", racing)

    assert get_providers.throttled_count("provider") is True
    assert "provider" not in racing


def test_reset_throttled_providers_also_resets_the_count(monkeypatch, _throttle_count):
    """Strikes not yet spent on a throttle would otherwise survive the reset."""
    monkeypatch.setattr(get_providers, "set_throttled_providers", lambda data: None)
    monkeypatch.setattr(get_providers, "update_throttled_provider", lambda: None)
    get_providers.tp["provider"] = ("TooManyRequests", datetime.datetime.now(), "1 hour")
    _throttle_count["provider"] = {"count": 3,
                                   "time": datetime.datetime.now() + datetime.timedelta(seconds=120)}

    get_providers.reset_throttled_providers()

    assert "provider" not in _throttle_count
