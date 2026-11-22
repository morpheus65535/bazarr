import ast
from datetime import datetime as real_datetime, timedelta

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


@pytest.mark.parametrize(
    "attempt_string,expected",
    [
        ("[]", []),
        ("[['en',1]]", [["en", 1]]),
        ("[[ 'en',1]]", [["en", 1]]),
        ('[["fr", "1.25e+2"]]', [["fr", "1.25e+2"]]),
        ("[['de', 1e-3]]", [["de", 0.001]]),
    ],
)
def test_attempt_parser_preserves_legacy_numeric_literal_forms(attempt_string, expected):
    assert adaptive_searching._get_attempts(attempt_string) == expected


@pytest.mark.parametrize("attempt_string", [None, 1, {}])
def test_attempt_parser_rejects_non_string_values(attempt_string):
    with pytest.raises(ValueError):
        adaptive_searching._get_attempts(attempt_string)


def test_update_failed_attempts_preserves_other_languages_for_legacy_literal_forms(monkeypatch):
    module = adaptive_searching
    now = real_datetime(2026, 1, 1, 12, 0, 0)
    _freeze_datetime(monkeypatch, module, now)

    updated = module.update_failed_attempts("en", "[['en',1],['fr','2e3']]")

    assert ast.literal_eval(updated) == [
        ["en", 1.0],
        ["en", now.timestamp()],
        ["fr", 2000.0],
    ]


def test_update_failed_attempts_compacts_matching_canonical_language_attempts(monkeypatch):
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
        ["en", 3],
        ["en:forced", 2],
        ["en:forced", current_ts],
        ["fr", 5],
        ["fr:hi", 4],
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


@pytest.mark.parametrize(
    "latest_days_ago,expected",
    [
        (2, []),
        (10, ["EN:HI:FORCED"]),
    ],
)
def test_active_search_normalizes_retry_keys_but_returns_original_language(latest_days_ago, expected):
    module = adaptive_searching
    now = real_datetime(2026, 1, 1, 12, 0, 0)
    initial_timestamp = now.timestamp() - (30 * 24 * 3600)
    latest_timestamp = now.timestamp() - (latest_days_ago * 24 * 3600)
    policy = {
        "delay": timedelta(weeks=3),
        "delta": timedelta(weeks=1),
        "initial_search_cutoff": now.timestamp() - (21 * 24 * 3600),
        "latest_search_cutoff": now.timestamp() - (7 * 24 * 3600),
    }

    active_languages = module.get_active_search_languages(
        ["EN:HI:FORCED"],
        f"[['en:forced:hi', {initial_timestamp}], ['en:hi:forced', {latest_timestamp}]]",
        adaptive_search_policy=policy,
    )

    assert active_languages == expected
