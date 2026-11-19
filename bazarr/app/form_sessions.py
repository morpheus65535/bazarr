# coding=utf-8

"""
Server-side registry for form login sessions.

The Flask session cookie is signed but stateless, so on its own it cannot be revoked. Each form login
stores a random token in the cookie and only the SHA-256 digest of that token in an in-memory registry.
Logout, password changes and expiry remove or reject the digest, which makes any saved copy of the
cookie stop working. The registry is process local and is cleared on restart, so users log in again
after a restart or upgrade.
"""

import hashlib
import secrets
import threading
import time

from flask import session

FORM_SESSION_MAX_AGE: int = 30 * 24 * 60 * 60
"""Absolute server-side lifetime of a form login session in seconds. The cookie itself is session-only."""

_SESSION_KEY: str = 'sid'
_registry: dict[str, float] = {}
_registry_lock = threading.Lock()


def _digest(token: str) -> str:
    """Return the SHA-256 hex digest used as the registry key for a session token.

    :param token: Raw session token stored in the client cookie.
    :returns: Hex digest of the token.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _purge_expired(now: float) -> None:
    """Remove registry entries whose expiry time has passed. The caller must hold the registry lock.

    :param now: Current time as a Unix timestamp.
    """
    for digest in [digest for digest, expires in _registry.items() if expires <= now]:
        del _registry[digest]


def _remove_token(token: str | None) -> None:
    """Remove a single session token from the registry if it is present.

    :param token: Raw session token, or ``None`` when the client has no session.
    """
    if not token:
        return
    with _registry_lock:
        _registry.pop(_digest(token), None)


def start_form_session() -> None:
    """Create a new form login session for the current request and bind it to the Flask session cookie.

    Any session token already held by this cookie is revoked first, so repeated logins do not accumulate
    live registry entries.
    """
    _remove_token(session.get(_SESSION_KEY))

    token = secrets.token_urlsafe(32)
    now = time.time()
    with _registry_lock:
        _purge_expired(now)
        _registry[_digest(token)] = now + FORM_SESSION_MAX_AGE

    session.clear()
    session[_SESSION_KEY] = token


def is_form_session_active() -> bool:
    """Check whether the current request carries a live form login session.

    Cookies without a registered token, including cookies issued before this registry existed, are
    rejected. Expired entries are treated as absent.

    :returns: ``True`` if the session token is registered and not expired, ``False`` otherwise.
    """
    token = session.get(_SESSION_KEY)
    if not token:
        return False
    with _registry_lock:
        expires = _registry.get(_digest(token))
        if expires is None or expires <= time.time():
            return False
    return True


def end_form_session() -> None:
    """Revoke the current request's form login session and clear the Flask session cookie."""
    _remove_token(session.get(_SESSION_KEY))
    session.clear()


def revoke_all_form_sessions() -> None:
    """Revoke every form login session, for example after the credentials or auth type change.

    Cookies held by other browsers become invalid as well, because their tokens are no longer registered.
    """
    with _registry_lock:
        _registry.clear()
