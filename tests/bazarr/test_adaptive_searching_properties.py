import ast
from datetime import datetime as real_datetime

import pytest

import subtitles.adaptive_searching as adaptive_searching


def _configure_adaptive_settings(monkeypatch, module, *, enabled=True, delay="1w", delta="1w"):
    monkeypatch.setattr(module.settings.general, "adaptive_searching", enabled)
    monkeypatch.setattr(module.settings.general, "adaptive_searching_delay", delay)
    monkeypatch.setattr(module.settings.general, "adaptive_searching_delta", delta)


def _freeze_datetime(monkeypatch, module, now):
    class FrozenDatetime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return now
            return now.astimezone(tz)

        @classmethod
        def fromtimestamp(cls, timestamp, tz=None):
            return real_datetime.fromtimestamp(timestamp, tz)

    monkeypatch.setattr(module, "datetime", FrozenDatetime)


@pytest.mark.parametrize(
    "attempt_string,expected",
    [
        ("", True),
        (" ", True),
        ("not_a_list", True),
        ("{'oops': 1}", True),
        ("None", True),
    ],
)
def test_is_search_active_fails_safe_for_malformed_attempt_strings(monkeypatch, attempt_string, expected):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay="3w", delta="1w")

    assert module.is_search_active("en", attempt_string) is expected


@pytest.mark.parametrize(
    "attempt_string",
    ["", " ", "[", "]", "not_a_list", "{'oops': 1}", "None", "[['en']]", "[['en', 'not-a-timestamp']]"],
)
def test_update_failed_attempts_fails_safe_for_malformed_attempt_strings(attempt_string):
    module = adaptive_searching

    updated = module.updateFailedAttempts("en", attempt_string)
    parsed = ast.literal_eval(updated)

    assert isinstance(parsed, list)
    assert any(item[0] == "en" for item in parsed)


def test_update_failed_attempts_compacts_and_preserves_initial_and_latest_attempts(monkeypatch):
    module = adaptive_searching
    now = real_datetime(2026, 1, 1, 12, 0, 0)
    _freeze_datetime(monkeypatch, module, now)
    current_ts = now.timestamp()

    updated = module.updateFailedAttempts(
        "en:forced",
        "[['en', 1], ['en:forced', 2], ['en', 3], ['fr:hi', 4], ['fr', 5], ['de', 6]]",
    )
    parsed = ast.literal_eval(updated)

    assert parsed == [
        ["de", 6],
        ["en", 1],
        ["en", current_ts],
        ["fr", 4],
        ["fr", 5],
    ]


@pytest.mark.parametrize(
    "desired_language,initial_days_ago,latest_days_ago,delay,delta,expected",
    [
        ("en", 10, 2, "3w", "1w", True),
        ("en", 30, 2, "3w", "1w", False),
        ("fr:forced", 10, 2, "3w", "1w", True),
    ],
)
def test_is_search_active_applies_delay_and_delta(
    monkeypatch, desired_language, initial_days_ago, latest_days_ago, delay, delta, expected
):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay=delay, delta=delta)
    now = real_datetime(2023, 11, 22, 0, 0, 0)
    _freeze_datetime(monkeypatch, module, now)
    now_ts = now.timestamp()
    base_language = desired_language.split(":", 1)[0]
    attempts = (
        f"[['{base_language}', {now_ts - (initial_days_ago * 24 * 3600)}], "
        f"['{desired_language}', {now_ts - (latest_days_ago * 24 * 3600)}]]"
    )

    assert module.is_search_active(desired_language, attempts) is expected


@pytest.mark.parametrize("bad_delay", ["aw", "xd", "--w", " w", "d", "w"])
def test_is_search_active_fails_safe_on_bad_delay_values(monkeypatch, bad_delay):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay="1w", delta="1w")
    monkeypatch.setattr(module.settings.general, "adaptive_searching_delay", bad_delay)

    assert module.is_search_active("en", "[['en', 1609459200]]") is True


@pytest.mark.parametrize("bad_delta", ["aw", "xd", "--w", " w", "d", "w"])
def test_is_search_active_fails_safe_on_bad_delta_values(monkeypatch, bad_delta):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay="1w", delta="1w")
    monkeypatch.setattr(module.settings.general, "adaptive_searching_delta", bad_delta)

    assert module.is_search_active("en", "[['en', 1609459200]]") is True


@pytest.mark.parametrize("value", [None, 0, 1, 3.14, [], {}, object()])
def test_adaptive_searching_handles_non_string_desired_language(monkeypatch, value):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay="3w", delta="1w")

    _freeze_datetime(monkeypatch, module, real_datetime(2026, 1, 1, 12, 0, 0))

    assert module.is_search_active(value, "[]") is True
    updated = module.updateFailedAttempts(value, "[]")
    parsed = ast.literal_eval(updated)
    assert isinstance(parsed, list)
    assert all(item[0] != "" for item in parsed)


def test_is_search_active_handles_multi_colon_language_codes(monkeypatch):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay="3w", delta="1w")
    _freeze_datetime(monkeypatch, module, real_datetime(2026, 1, 1, 12, 0, 0))

    attempts = "[['en:hi:forced', 1700600000], ['en:hi', 1700600000]]"

    assert module.is_search_active("en:hi:forced", attempts) is True
    assert module.is_search_active(":", attempts) is True


@pytest.mark.parametrize("flag_only", [":hi", ":forced", "::hi"])
def test_is_search_active_handles_only_flag_desired_language(monkeypatch, flag_only):
    module = adaptive_searching
    _configure_adaptive_settings(monkeypatch, module, delay="1w", delta="1w")
    _freeze_datetime(monkeypatch, module, real_datetime(2026, 1, 1, 12, 0, 0))

    assert module.is_search_active(flag_only, "[['en', 0]]") is True
