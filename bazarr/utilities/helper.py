# coding=utf-8

import os
import logging
import hashlib
import hmac
from flask import Request
import math
import threading
import time

from charset_normalizer import detect
from bs4 import UnicodeDammit

from app.config import settings


bool_map = {"True": True, "False": False, "true": True, "false": False}


def _to_bytes(value):
    # Use surrogatepass to prevent UnicodeEncodeError on malformed input
    return str(value).encode('utf-8', 'surrogatepass')


def is_valid_apikey(*candidates, apikey_settings=None):
    """Check if any of the candidates matches the API key, an empty API key never matches.

    :param candidates: API keys submitted by the client (query string, form, header...), None if absent
    :param apikey_settings: configured API key to compare against, defaults to settings.auth.apikey
    :returns: True if one of the candidates matches the configured API key, False otherwise
    """
    if apikey_settings is None:
        apikey_settings = settings.auth.apikey
    apikey_settings = str(apikey_settings or '')
    if not apikey_settings:
        return False
    expected = _to_bytes(apikey_settings)
    valid = False
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            valid |= hmac.compare_digest(_to_bytes(candidate), expected)
    return valid


# Cache last verified credentials to avoid hashing the password on every basic auth request
_verified_credentials = {}
_verified_credentials_lock = threading.Lock()

# Run legacy hash upgrades and verified credentials cache writes one at a time
_password_update_lock = threading.Lock()

# Failed logins per (client address, username) to slow down brute force attempts. Keying on the username too
# prevents a client sharing the same address (e.g. behind a reverse proxy) from locking out other usernames.
_LOGIN_FAILURES_FREE = 5  # failures allowed before backing off
_LOGIN_FAILURES_WINDOW = 15 * 60  # seconds before failures are forgotten
_LOGIN_BACKOFF_MAX = 30  # maximum backoff in seconds
_login_failures = {}
_login_failures_lock = threading.Lock()

_dummy_password_hash = None


def _get_dummy_password_hash():
    # Hash used when username is wrong so response time doesn't reveal valid usernames
    global _dummy_password_hash
    if _dummy_password_hash is None:
        from app.config import hash_password
        _dummy_password_hash = hash_password(os.urandom(16).hex())
    return _dummy_password_hash


def _credentials_fingerprint(user, pw, stored_hash):
    key = _to_bytes(settings.general.flask_secret_key)
    message = _to_bytes('\0'.join([str(user), str(pw), str(stored_hash)]))
    return hmac.new(key, message, hashlib.sha256).digest()


def _is_cached_login(user, pw, stored_hash):
    fingerprint = _credentials_fingerprint(user, pw, stored_hash)
    with _verified_credentials_lock:
        cached = _verified_credentials.get(stored_hash)
    return cached is not None and hmac.compare_digest(cached, fingerprint)


def _cache_login(user, pw, stored_hash):
    fingerprint = _credentials_fingerprint(user, pw, stored_hash)
    with _verified_credentials_lock:
        _verified_credentials.clear()
        _verified_credentials[stored_hash] = fingerprint


def _login_failures_key(client, user):
    if client is None:
        return None
    return client, str(user)


def _login_backoff_remaining(key):
    if key is None:
        return 0
    now = time.monotonic()
    with _login_failures_lock:
        entry = _login_failures.get(key)
        if not entry:
            return 0
        count, last_failure = entry
        if now - last_failure > _LOGIN_FAILURES_WINDOW:
            del _login_failures[key]
            return 0
    if count < _LOGIN_FAILURES_FREE:
        return 0
    delay = min(2 ** (count - _LOGIN_FAILURES_FREE), _LOGIN_BACKOFF_MAX)
    return max(0.0, last_failure + delay - now)


def _record_login_result(key, success):
    if key is None:
        return
    with _login_failures_lock:
        if success:
            _login_failures.pop(key, None)
        else:
            count = _login_failures.get(key, (0, 0))[0]
            _login_failures[key] = (count + 1, time.monotonic())
            # Remove expired entries to keep memory bounded
            if len(_login_failures) > 10000:
                cutoff = time.monotonic() - _LOGIN_FAILURES_WINDOW
                for stale in [k for k, (_, t) in _login_failures.items() if t < cutoff]:
                    del _login_failures[stale]


def _verify_user_password(user, pw, client=None):
    """Check UI credentials.

    :param user: submitted username
    :param pw: submitted password
    :param client: caller identifier (e.g. remote address) used for brute force backoff
    :returns: True if credentials are valid, False otherwise
    """
    from app.config import verify_password, is_legacy_password_hash, hash_password, write_config

    username = settings.auth.username
    stored_hash = str(settings.auth.password or '')
    if not username or not stored_hash or user is None or pw is None:
        return False
    user_matches = hmac.compare_digest(_to_bytes(user), _to_bytes(username))

    # Credentials already verified against current stored hash
    if user_matches and _is_cached_login(user, pw, stored_hash):
        return True

    failures_key = _login_failures_key(client, user)
    if _login_backoff_remaining(failures_key) > 0:
        logging.info(f'Login attempt from {client} for user {user} refused: too many failed attempts, '
                     f'try again later')
        return False

    # Verify outside of any lock so slow failing attempts don't delay other logins
    if user_matches:
        valid = verify_password(pw, stored_hash)
        if is_legacy_password_hash(stored_hash):
            # Legacy MD5 check is instant, run the slow hash too so response time doesn't reveal valid usernames
            verify_password(pw, _get_dummy_password_hash())
    else:
        verify_password(pw, _get_dummy_password_hash())
        valid = False

    if valid:
        with _password_update_lock:
            current_hash = str(settings.auth.password or '')
            if current_hash != stored_hash:
                # Another thread may have upgraded the legacy hash while verifying, any other change is a new password
                valid = (is_legacy_password_hash(stored_hash) and
                         _is_cached_login(user, pw, current_hash))
            elif is_legacy_password_hash(stored_hash):
                # Upgrade legacy MD5 hash now that the password is known
                current_hash = hash_password(pw)
                settings.auth.password = current_hash
                try:
                    write_config()
                    logging.info('Upgraded stored UI password hash to a salted PBKDF2 hash.')
                except Exception:
                    logging.exception('Unable to save upgraded UI password hash.')

            if valid:
                _cache_login(user, pw, current_hash)

    _record_login_result(failures_key, valid)
    return valid


def get_login_retry_after(user, request):
    """Seconds before the next login attempt for this user from this client is evaluated, 0 if not throttled."""
    remaining = _login_backoff_remaining(_login_failures_key(request.remote_addr, user))
    return math.ceil(remaining) if remaining > 0 else 0


def check_credentials(user: str, pw: str, request: Request, log_success: bool = True) -> bool:
    """
    Validate submitted credentials against the configured username and
    password.

    The client IP address used for logging is resolved from the
    ``HTTP_X_FORWARDED_FOR`` or ``HTTP_X_REAL_IP`` request headers,
    falling back to the remote address of the request. The password is
    verified against the stored salted hash (legacy MD5 hashes are
    upgraded on first successful login), and repeated failures from the
    same remote address for the same username are throttled. Both
    successful and failed authentication attempts are logged, with
    logging of successful attempts being optional.

    :param user: Username submitted by the client.
    :param pw: Plain-text password submitted by the client.
    :param request: Incoming request used to determine the client IP
        address for logging and throttling.
    :param log_success: Whether a successful authentication attempt
        should be written to the log.
    :return: ``True`` if the credentials match the configured ones,
        ``False`` otherwise.
    """
    forwarded_for_ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR')
    real_ip_addr = request.environ.get('HTTP_X_REAL_IP')
    ip_addr = forwarded_for_ip_addr or real_ip_addr or request.remote_addr
    if _verify_user_password(user, pw, client=request.remote_addr):
        if log_success:
            logging.info(f'Successful authentication from {ip_addr} for user {user}')
        return True
    else:
        logging.info(f'Failed authentication from {ip_addr} for user {user}')
        return False


def get_subtitle_destination_folder() -> str | None:
    """
    Determine the custom destination folder configured for subtitle files.

    Reads the application settings and returns the trimmed custom subfolder
    path when a custom subfolder has been configured and the subfolder mode
    is not set to ``'current'``. In any other case no custom destination is
    considered to be defined.

    :return: The stripped custom subfolder path, or ``None`` when no custom
        subfolder is configured or the subfolder mode is ``'current'``.
    """
    fld_custom = str(settings.general.subfolder_custom).strip() if (settings.general.subfolder_custom and
                                                                    settings.general.subfolder != 'current') else None
    return fld_custom


def get_target_folder(file_path: str) -> str | None:
    """
    Determine the directory in which subtitles for the given media file should
    be stored, based on the configured subfolder settings.

    When the subfolder setting is ``"current"`` or no custom subfolder is
    configured, no dedicated target folder is used and ``None`` is returned.
    Otherwise, the target folder is derived from the custom subfolder value:
    for the ``"absolute"`` mode the custom value is used as-is, and for the
    ``"relative"`` mode it is joined with the directory containing the media
    file. Any other mode yields ``None``. The resulting path is normalized to
    unicode and created on disk if it does not already exist; if creation
    fails, the error is logged and ``None`` is returned.

    :param file_path: Path to the media file for which the subtitle target
        folder should be resolved.
    :return: The resolved (and existing) target directory, or ``None`` if no
        dedicated subfolder applies, the subfolder mode is unknown, or the
        directory could not be created.
    """
    subfolder = settings.general.subfolder
    fld_custom = str(settings.general.subfolder_custom).strip() \
        if settings.general.subfolder_custom else None

    if subfolder != "current" and fld_custom:
        # specific subFolder requested, create it if it doesn't exist
        fld_base = os.path.split(file_path)[0]

        if subfolder == "absolute":
            # absolute folder
            fld = fld_custom
        elif subfolder == "relative":
            fld = os.path.join(fld_base, fld_custom)
        else:
            fld = None

        if fld is None:
            return None
        fld = force_unicode(fld)

        if not os.path.isdir(fld):
            try:
                os.makedirs(fld)
            except Exception:
                logging.error(f'BAZARR is unable to create directory to save subtitles: {fld}')
                fld = None
    else:
        fld = None

    return fld


def force_unicode(s: str | bytes) -> str:
    """
    Ensure a string is unicode, not encoded; used for enforcing file paths to be unicode upon saving a subtitle,
    to prevent encoding issues when saving a subtitle to a non-ascii path.
    :param s: string
    :return: unicode string
    """
    if isinstance(s, str):
        return s

    try:
        return s.decode("utf-8")
    except UnicodeDecodeError:
        encoding = detect(s).get('encoding') or 'utf-8'
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            return UnicodeDammit(s).unicode_markup or s.decode(encoding, errors='replace')
