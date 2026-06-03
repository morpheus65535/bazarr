# coding=utf-8
# fmt: off

import logging

from datetime import datetime, timedelta
from functools import lru_cache
from math import isfinite
from time import monotonic

from app.config import settings
from subtitles.language_utils import parse_language_token


_ADAPTIVE_POLICY_CACHE_TTL = 1.0
_adaptive_policy_cache = {
    "expires_at": 0.0,
    "settings_key": None,
    "policy_components": None,
}


def _parse_attempts_fast(attempt_string):
    if not attempt_string or not attempt_string.startswith("[[") or not attempt_string.endswith("]]"):
        return None

    attempts = []
    for attempt in attempt_string[2:-2].split("], ["):
        try:
            desired_language, timestamp_text = attempt.split(", ", 1)
            if desired_language[0] not in ("'", '"') or desired_language[-1] != desired_language[0]:
                return None
            timestamp = float(timestamp_text) if "." in timestamp_text else int(timestamp_text)
        except (IndexError, TypeError, ValueError):
            return None

        attempts.append([desired_language[1:-1], timestamp])
    return attempts


def _get_attempts(attempt_string):
    if isinstance(attempt_string, list):
        attempts = attempt_string
    else:
        attempts = _parse_attempts_fast(attempt_string)
        if attempts is None:
            raise ValueError

    if type(attempts) is not list:
        raise ValueError

    return attempts


def _get_attempt_windows(attempts):
    attempt_windows = {}

    for attempt in attempts:
        if not isinstance(attempt, (list, tuple)) or len(attempt) < 2:
            raise ValueError

        desired_language, timestamp = attempt[0], attempt[1]
        if not isinstance(desired_language, str):
            raise ValueError
        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError) as exc:
            raise ValueError from exc
        if not isfinite(timestamp):
            raise ValueError

        initial_timestamp, latest_timestamp = attempt_windows.get(desired_language, (timestamp, timestamp))
        if timestamp < initial_timestamp:
            initial_timestamp = timestamp
        if timestamp > latest_timestamp:
            latest_timestamp = timestamp
        attempt_windows[desired_language] = (initial_timestamp, latest_timestamp)

    return attempt_windows


def get_attempt_windows(attempt_string):
    try:
        attempts = _get_attempts(attempt_string)
    except (SyntaxError, ValueError, TypeError):
        return {}

    if not attempts:
        return {}

    try:
        return _get_attempt_windows(attempts)
    except ValueError:
        return {}


def _get_adaptive_timedelta(setting_name, setting_value):
    try:
        value = int(setting_value[:-1])
    except (TypeError, ValueError):
        logging.debug(f"Adaptive searching: cannot parse {setting_name} from config file: {setting_value}")
        return None

    if setting_value.endswith('d'):
        return timedelta(days=value)
    elif setting_value.endswith('w'):
        return timedelta(weeks=value)

    logging.debug(f"Adaptive searching: cannot parse {setting_name} from config file: {setting_value}")
    return None


@lru_cache(maxsize=32)
def _get_cached_policy_components(adaptive_searching_enabled, adaptive_searching_delay, adaptive_searching_delta):
    if not adaptive_searching_enabled:
        logging.debug("adaptive searching is disabled, search will run.")
        return None

    extended_search_delay = _get_adaptive_timedelta(
        'adaptive_searching_delay',
        adaptive_searching_delay,
    )
    if extended_search_delay is None:
        return None

    extended_search_delta = _get_adaptive_timedelta(
        'adaptive_searching_delta',
        adaptive_searching_delta,
    )
    if extended_search_delta is None:
        return None

    return extended_search_delay, extended_search_delta


def get_adaptive_search_policy():
    settings_key = (
        settings.general.adaptive_searching,
        settings.general.adaptive_searching_delay,
        settings.general.adaptive_searching_delta,
    )

    if (
        _adaptive_policy_cache["expires_at"] > monotonic() and
        _adaptive_policy_cache["settings_key"] == settings_key
    ):
        policy_components = _adaptive_policy_cache["policy_components"]
    else:
        policy_components = _get_cached_policy_components(*settings_key)
        _adaptive_policy_cache["settings_key"] = settings_key
        _adaptive_policy_cache["policy_components"] = policy_components
        _adaptive_policy_cache["expires_at"] = monotonic() + _ADAPTIVE_POLICY_CACHE_TTL

    if policy_components is None:
        return None

    now = datetime.now()

    return {
        "delay": policy_components[0],
        "delta": policy_components[1],
        "delay_label": settings_key[1],
        "delta_label": settings_key[2],
        "now": now,
        "initial_search_cutoff": now.timestamp() - policy_components[0].total_seconds(),
        "latest_search_cutoff": now.timestamp() - policy_components[1].total_seconds(),
    }


def get_adaptive_search_policy_key(adaptive_search_policy=None):
    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    if adaptive_search_policy is None:
        return None

    return f"{adaptive_search_policy['delay_label']}|{adaptive_search_policy['delta_label']}"


def get_active_search_languages(desired_languages, attempt_string, adaptive_search_policy=None):
    if isinstance(desired_languages, str):
        desired_languages = [desired_languages]
    else:
        desired_languages = list(desired_languages)

    if not desired_languages:
        return []

    if adaptive_search_policy is None:
        adaptive_search_policy = get_adaptive_search_policy()

    if adaptive_search_policy is None:
        return desired_languages

    debug_logging = logging.getLogger().isEnabledFor(logging.DEBUG)
    if debug_logging:
        logging.debug("Adaptive searching is enabled, we'll see if it's time to search again...")
    try:
        attempts = _get_attempts(attempt_string)
    except (SyntaxError, ValueError, TypeError):
        if debug_logging:
            logging.debug("Adaptive searching: attempts is malformed. As a failsafe, search will run.")
        return desired_languages

    if not len(attempts):
        if debug_logging:
            logging.debug("Adaptive searching: attempts list is empty, search will run.")
        return desired_languages

    try:
        attempt_windows = _get_attempt_windows(attempts)
    except ValueError:
        if debug_logging:
            logging.debug("Adaptive searching: attempts is malformed. As a failsafe, search will run.")
        return desired_languages

    active_languages = []
    for desired_language in desired_languages:
        if desired_language not in attempt_windows:
            if debug_logging:
                logging.debug("Adaptive searching: there's no attempts matching desired language, search will run.")
            active_languages.append(desired_language)
            continue

        initial_attempt_timestamp, latest_attempt_timestamp = attempt_windows[desired_language]
        delay = adaptive_search_policy["delay"]
        delta = adaptive_search_policy["delta"]
        try:
            initial_search_active = initial_attempt_timestamp > adaptive_search_policy["initial_search_cutoff"]
            latest_search_active = latest_attempt_timestamp <= adaptive_search_policy["latest_search_cutoff"]
        except (TypeError, OverflowError, ValueError, OSError):
            if debug_logging:
                logging.debug("Adaptive searching: unable to parse initial and latest search timestamps, search will run.")
            active_languages.append(desired_language)
            continue

        if debug_logging:
            try:
                initial_search_timestamp = datetime.fromtimestamp(initial_attempt_timestamp)
                latest_search_timestamp = datetime.fromtimestamp(latest_attempt_timestamp)
            except (OverflowError, ValueError, OSError):
                logging.debug("Adaptive searching: unable to parse initial and latest search timestamps, search will run.")
                active_languages.append(desired_language)
                continue

            logging.debug(f"Adaptive searching: initial search date for {desired_language} is {initial_search_timestamp}")
            logging.debug(f"Adaptive searching: latest search date for {desired_language} is {latest_search_timestamp}")
            logging.debug(f"Adaptive searching: delay after initial search value: {delay}")
            logging.debug(f"Adaptive searching: delta between latest search and now value: {delta}")

            delay_label = adaptive_search_policy.get("delay_label", delay)
            delta_label = adaptive_search_policy.get("delta_label", delta)

        if initial_search_active:
            if debug_logging:
                logging.debug(f"Adaptive searching: it's been less than {delay_label} since "
                              f"initial search, search will run.")
            active_languages.append(desired_language)
        elif latest_search_active:
            if debug_logging:
                logging.debug(
                    f"Adaptive searching: it's been more than {delta_label} since "
                    f"latest search, search will run.")
            active_languages.append(desired_language)
        else:
            if debug_logging:
                logging.debug(
                    f"Adaptive searching: it's been less than {delta_label} since "
                    f"latest search, we're not ready to search yet.")

    return active_languages


def is_search_active(desired_language, attempt_string, adaptive_search_policy=None):
    """
    Function to test if it's time to search again after a previous attempt matching the desired language. For 3 weeks,
    we search on a scheduled basis but after 3 weeks we start searching only once a week.

    @param desired_language: 2 letters language to search for in attempts
    @type desired_language: str
    @param attempt_string: string representation of a list of lists from database column failedAttempts
    @type attempt_string: str

    @return: return True if it's time to search again and False if not
    @rtype: bool
    """

    return desired_language in get_active_search_languages(
        [desired_language],
        attempt_string,
        adaptive_search_policy=adaptive_search_policy,
    )


def update_failed_attempts(desired_languages, attempt_string):
    if isinstance(desired_languages, str):
        desired_languages = [desired_languages]
    else:
        desired_languages = list(desired_languages)

    normalized_desired_languages = []
    seen_desired_languages = set()
    for desired_language in desired_languages:
        parsed_language = parse_language_token(desired_language)
        if parsed_language is None:
            continue
        canonical_language = parsed_language[0]
        if canonical_language in seen_desired_languages:
            continue
        seen_desired_languages.add(canonical_language)
        normalized_desired_languages.append(canonical_language)

    desired_languages = normalized_desired_languages
    desired_languages_set = set(desired_languages)

    try:
        attempts = _get_attempts(attempt_string)
        logging.debug(f"Adaptive searching: current attempts value is {attempts}")
    except (SyntaxError, ValueError, TypeError):
        logging.debug("Adaptive searching: failed to parse attempts value, we'll use an empty list.")
        attempts = []

    if not desired_languages:
        return str(attempts)

    initial_attempts = {}
    filtered_attempts = []
    for attempt in attempts:
        if not isinstance(attempt, (list, tuple)) or len(attempt) < 2:
            continue

        desired_language, timestamp = attempt[0], attempt[1]
        if not isinstance(desired_language, str):
            continue
        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError):
            continue
        if not isfinite(timestamp):
            continue

        if desired_language in desired_languages_set:
            previous_attempt = initial_attempts.get(desired_language)
            if previous_attempt is None or timestamp < previous_attempt[1]:
                initial_attempts[desired_language] = [desired_language, timestamp]
        else:
            filtered_attempts.append([desired_language, timestamp])

    current_timestamp = datetime.timestamp(datetime.now())
    for desired_language in desired_languages:
        initial_attempt = initial_attempts.get(desired_language)
        if initial_attempt is not None:
            filtered_attempts.append(initial_attempt)
        filtered_attempts.append([desired_language, current_timestamp])

    updated_attempts = sorted(filtered_attempts, key=lambda x: x[0])
    logging.debug(f"Adaptive searching: updated attempts that will be saved to database is {updated_attempts}")

    return str(updated_attempts)


def updateFailedAttempts(desired_language, attempt_string):
    """
    Function to parse attempts and make sure we only keep initial and latest search timestamp for each language.

    @param desired_language: 2 letters language to search for in attempts
    @type desired_language: str
    @param attempt_string: string representation of a list of lists from database column failedAttempts
    @type attempt_string: str

    @return: return a string representation of a list of lists like [str(language_code), str(attempts)]
    @rtype: str
    """

    return update_failed_attempts([desired_language], attempt_string)
