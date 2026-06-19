# coding=utf-8
# fmt: off

import ast
import logging

from datetime import datetime, timedelta

from app.config import settings


def _safe_attempt_items(attempts):
    safe = []
    for item in attempts:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        if not isinstance(item[0], str):
            continue
        safe.append([item[0], item[1]])
    return safe


def _safe_timestamp(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_base_language(language):
    if not isinstance(language, str):
        return None

    base = language.split(":", 1)[0].strip().lower()
    return base or None


def _group_attempts_by_base_language(attempts):
    grouped = {}
    for language, timestamp in attempts:
        base_language = _normalize_base_language(language)
        if not base_language:
            continue
        grouped.setdefault(base_language, []).append([base_language, timestamp])
    return grouped


def _compact_attempts(attempts_by_language, exclude_language=None):
    compacted = []
    for language, language_attempts in attempts_by_language.items():
        if language == exclude_language:
            continue
        sorted_attempts = sorted(language_attempts, key=lambda x: _safe_timestamp(x[1]))
        compacted.append(sorted_attempts[0])
        if len(sorted_attempts) > 1 and sorted_attempts[-1] != sorted_attempts[0]:
            compacted.append(sorted_attempts[-1])
    return compacted


def is_search_active(desired_language, attempt_string):
    """
    Function to test if it's time to search again after a previous attempt matching the desired language. For 3 weeks,
    we search on a scheduled basis but after 3 weeks we start searching only once a week.

    @param desired_language: language code token with optional flags; non-string values are treated as invalid and fail-safe to True
    @type desired_language: object
    @param attempt_string: string representation of a list of lists from database column failedAttempts
    @type attempt_string: str

    @return: return True if it's time to search again and False if not
    @rtype: bool
    """

    if settings.general.adaptive_searching:
        logging.debug("Adaptive searching is enable, we'll see if it's time to search again...")
        try:
            # let's try to get a list of lists from the string representation in database
            attempts = ast.literal_eval(attempt_string or '[]')
            if not isinstance(attempts, list):
                # attempts should be a list if not, it's malformed or None
                raise ValueError
        except (ValueError, SyntaxError, TypeError):
            logging.debug("Adaptive searching: attempts is malformed. As a failsafe, search will run.")
            return True

        attempts = _safe_attempt_items(attempts)

        if not attempts:
            logging.debug("Adaptive searching: attempts list is empty, search will run.")
            return True

        # Extract base language code (handle "en", "en:forced", "en:hi", etc.)
        base_desired_language = _normalize_base_language(desired_language)
        if not base_desired_language:
            return True

        attempts_by_language = _group_attempts_by_base_language(attempts)
        matching_attempts = sorted(
            attempts_by_language.get(base_desired_language, []),
            key=lambda x: _safe_timestamp(x[1]),
        )

        if not matching_attempts:
            logging.debug("Adaptive searching: there's no attempts matching desired language, search will run.")
            return True
        else:
            logging.debug(f"Adaptive searching: attempts matching language {desired_language}: {matching_attempts}")

        # try to get the initial and latest search timestamp from matching attempts
        initial_search_attempt = matching_attempts[0]
        latest_search_attempt = matching_attempts[-1]

        # try to parse the timestamps for those attempts
        try:
            initial_search_timestamp = datetime.fromtimestamp(float(initial_search_attempt[1]))
            latest_search_timestamp = datetime.fromtimestamp(float(latest_search_attempt[1]))
        except (OverflowError, ValueError, OSError):
            logging.debug("Adaptive searching: unable to parse initial and latest search timestamps, search will run.")
            return True
        else:
            logging.debug(f"Adaptive searching: initial search date for {desired_language} is "
                          f"{initial_search_timestamp}")
            logging.debug(f"Adaptive searching: latest search date for {desired_language} is {latest_search_timestamp}")

        # defining basic calculation variables
        now = datetime.now()
        try:
            if settings.general.adaptive_searching_delay.endswith('d'):
                extended_search_delay = timedelta(days=int(settings.general.adaptive_searching_delay[:-1]))
            elif settings.general.adaptive_searching_delay.endswith('w'):
                extended_search_delay = timedelta(weeks=int(settings.general.adaptive_searching_delay[:-1]))
            else:
                logging.debug(f"Adaptive searching: cannot parse adaptive_searching_delay from config file: "
                              f"{settings.general.adaptive_searching_delay}")
                return True
        except ValueError:
            logging.debug(f"Adaptive searching: cannot parse adaptive_searching_delay from config file: "
                          f"{settings.general.adaptive_searching_delay}")
            return True
        logging.debug(f"Adaptive searching: delay after initial search value: {extended_search_delay}")

        try:
            if settings.general.adaptive_searching_delta.endswith('d'):
                extended_search_delta = timedelta(days=int(settings.general.adaptive_searching_delta[:-1]))
            elif settings.general.adaptive_searching_delta.endswith('w'):
                extended_search_delta = timedelta(weeks=int(settings.general.adaptive_searching_delta[:-1]))
            else:
                logging.debug(f"Adaptive searching: cannot parse adaptive_searching_delta from config file: "
                              f"{settings.general.adaptive_searching_delta}")
                return True
        except ValueError:
            logging.debug(f"Adaptive searching: cannot parse adaptive_searching_delta from config file: "
                          f"{settings.general.adaptive_searching_delta}")
            return True
        logging.debug(f"Adaptive searching: delta between latest search and now value: {extended_search_delta}")

        if initial_search_timestamp + extended_search_delay > now:
            logging.debug(f"Adaptive searching: it's been less than {settings.general.adaptive_searching_delay} since "
                          f"initial search, search will run.")
            return True
        else:
            logging.debug(f"Adaptive searching: it's been more than {settings.general.adaptive_searching_delay} since "
                          f"initial search, let's check if it's time to search again.")
            if latest_search_timestamp + extended_search_delta <= now:
                logging.debug(
                    f"Adaptive searching: it's been more than {settings.general.adaptive_searching_delta} since "
                    f"latest search, search will run.")
                return True
            else:
                logging.debug(
                    f"Adaptive searching: it's been less than {settings.general.adaptive_searching_delta} since "
                    f"latest search, we're not ready to search yet.")
                return False

    logging.debug("adaptive searching is disabled, search will run.")
    return True


def updateFailedAttempts(desired_language, attempt_string):
    """
    Function to parse attempts and make sure we only keep initial and latest search timestamp for each language.

    @param desired_language: language code token with optional flags; non-string values preserve compacted existing attempts
    @type desired_language: object
    @param attempt_string: string representation of a list of lists from database column failedAttempts
    @type attempt_string: str

    @return: return a string representation of a list of lists like [str(language_code), str(attempts)]
    @rtype: str
    """

    try:
        # let's try to get a list of lists from the string representation in database
        attempts = ast.literal_eval(attempt_string or '[]')
        logging.debug(f"Adaptive searching: current attempts value is {attempts}")
        if not isinstance(attempts, list):
            # attempts should be a list if not, it's malformed or None
            raise ValueError
    except (ValueError, SyntaxError, TypeError):
        logging.debug("Adaptive searching: failed to parse attempts value, we'll use an empty list.")
        attempts = []

    attempts = _safe_attempt_items(attempts)

    # Extract base language code (handle "en", "en:forced", "en:hi", etc.)
    base_desired_language = _normalize_base_language(desired_language)
    attempts_by_language = _group_attempts_by_base_language(attempts)

    if not base_desired_language:
        compacted = sorted(_compact_attempts(attempts_by_language), key=lambda x: x[0])
        logging.debug(f"Adaptive searching: malformed desired language; preserving compacted attempts {compacted}")
        return str(compacted)

    matching_attempts = sorted(
        attempts_by_language.get(base_desired_language, []),
        key=lambda x: _safe_timestamp(x[1]),
    )
    logging.debug(f"Adaptive searching: attempts matching language {base_desired_language}: {matching_attempts}")

    filtered_attempts = _compact_attempts(attempts_by_language, exclude_language=base_desired_language)
    logging.debug(f"Adaptive searching: compacted non-target attempts: {filtered_attempts}")

    # Keep initial search for target language if it exists.
    if matching_attempts:
        filtered_attempts.append(matching_attempts[0])

    # Append current attempt for target language as latest.
    filtered_attempts.append([base_desired_language, datetime.timestamp(datetime.now())])

    updated_attempts = sorted(filtered_attempts, key=lambda x: x[0])
    logging.debug(f"Adaptive searching: updated attempts that will be saved to database is {updated_attempts}")

    return str(updated_attempts)
