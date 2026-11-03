# -*- coding: utf-8 -*-
"""
Tests for server-side form login sessions.

A saved copy of a form session cookie must stop authenticating once the session is logged out,
re-issued, revoked, or expired. Cookies that only carry the legacy ``logged_in`` flag must be rejected.
"""
from types import SimpleNamespace

import pytest
from flask import Flask

from app import form_sessions
from app.form_sessions import (FORM_SESSION_MAX_AGE, end_form_session, is_form_session_active,
                               revoke_all_form_sessions, start_form_session)


@pytest.fixture(autouse=True)
def clear_registry():
    form_sessions._registry.clear()
    yield
    form_sessions._registry.clear()


@pytest.fixture
def app():
    flask_app = Flask("form-session-tests")
    flask_app.config["SECRET_KEY"] = "test-secret"
    flask_app.config["TESTING"] = True

    @flask_app.post("/login")
    def login():
        start_form_session()
        return "", 204

    @flask_app.post("/logout")
    def logout():
        end_form_session()
        return "", 204

    @flask_app.post("/legacy-login")
    def legacy_login():
        from flask import session
        session["logged_in"] = True
        return "", 204

    @flask_app.get("/token")
    def token():
        from flask import session
        return session.get("sid", "")

    @flask_app.get("/probe")
    def probe():
        return ("ok", 200) if is_form_session_active() else ("denied", 401)

    return flask_app


def _saved_cookie(client) -> str:
    return client.get_cookie("session").value


def _replay(app, cookie_value: str) -> int:
    fresh = app.test_client()
    fresh.set_cookie("session", cookie_value)
    return fresh.get("/probe").status_code


def test_login_session_is_active(app):
    client = app.test_client()
    assert client.post("/login").status_code == 204
    assert client.get("/probe").status_code == 200


def test_login_cookie_is_session_only(app):
    client = app.test_client()
    response = client.post("/login")

    set_cookie = response.headers.get("Set-Cookie", "")
    assert set_cookie.startswith("session=")
    assert "Expires=" not in set_cookie
    assert "Max-Age=" not in set_cookie


def test_no_cookie_is_denied(app):
    assert app.test_client().get("/probe").status_code == 401


def test_logout_invalidates_the_live_session(app):
    client = app.test_client()
    client.post("/login")
    client.post("/logout")
    assert client.get("/probe").status_code == 401


def test_saved_cookie_is_rejected_after_logout(app):
    client = app.test_client()
    client.post("/login")
    saved = _saved_cookie(client)

    client.post("/logout")

    assert _replay(app, saved) == 401


def test_saved_cookie_is_valid_before_logout(app):
    client = app.test_client()
    client.post("/login")
    saved = _saved_cookie(client)

    assert _replay(app, saved) == 200


def test_relogin_revokes_previous_token(app):
    client = app.test_client()
    client.post("/login")
    first = _saved_cookie(client)

    client.post("/login")

    assert _replay(app, first) == 401
    assert client.get("/probe").status_code == 200


def test_revoke_all_invalidates_every_browser(app):
    first = app.test_client()
    second = app.test_client()
    first.post("/login")
    second.post("/login")
    first_saved = _saved_cookie(first)
    second_saved = _saved_cookie(second)

    revoke_all_form_sessions()

    assert first.get("/probe").status_code == 401
    assert second.get("/probe").status_code == 401
    assert _replay(app, first_saved) == 401
    assert _replay(app, second_saved) == 401


def test_legacy_logged_in_cookie_is_rejected(app):
    client = app.test_client()
    assert client.post("/legacy-login").status_code == 204

    assert client.get("/probe").status_code == 401


def test_session_expires_on_the_server(app, monkeypatch):
    clock = [1_000_000.0]
    monkeypatch.setattr(form_sessions, "time", SimpleNamespace(time=lambda: clock[0]))

    client = app.test_client()
    client.post("/login")
    saved = _saved_cookie(client)

    clock[0] += FORM_SESSION_MAX_AGE + 1

    assert client.get("/probe").status_code == 401
    assert _replay(app, saved) == 401


def test_session_is_active_just_before_expiry(app, monkeypatch):
    clock = [1_000_000.0]
    monkeypatch.setattr(form_sessions, "time", SimpleNamespace(time=lambda: clock[0]))

    client = app.test_client()
    client.post("/login")

    clock[0] += FORM_SESSION_MAX_AGE - 1

    assert client.get("/probe").status_code == 200


def test_registry_stores_only_digests(app):
    client = app.test_client()
    client.post("/login")
    token = client.get("/token").text

    assert token
    assert token not in form_sessions._registry
    assert form_sessions._digest(token) in form_sessions._registry


@pytest.fixture
def auth_settings(monkeypatch, memory_session):
    """Run save_settings against the real settings object without touching config.yaml or the database."""
    import hashlib

    import app.config as config_module
    import app.database as app_database

    settings = config_module.settings
    saved = {key: settings.auth[key] for key in ("username", "password", "type")}
    monkeypatch.setattr(app_database, "database", memory_session)
    monkeypatch.setattr(config_module, "write_config", lambda: None)
    monkeypatch.setattr(settings.validators, "validate", lambda: None)
    settings.auth["username"] = "admin"
    settings.auth["password"] = hashlib.md5(b"old-password").hexdigest()
    settings.auth["type"] = "form"
    try:
        yield config_module
    finally:
        for key, value in saved.items():
            settings.auth[key] = value


def test_password_change_revokes_form_sessions(app, auth_settings):
    client = app.test_client()
    client.post("/login")
    saved = _saved_cookie(client)

    auth_settings.save_settings([("settings-auth-password", "new-password")])

    assert client.get("/probe").status_code == 401
    assert _replay(app, saved) == 401


def test_username_change_revokes_form_sessions(app, auth_settings):
    client = app.test_client()
    client.post("/login")

    auth_settings.save_settings([("settings-auth-username", "someone-else")])

    assert client.get("/probe").status_code == 401


def test_auth_type_change_revokes_form_sessions(app, auth_settings):
    client = app.test_client()
    client.post("/login")

    auth_settings.save_settings([("settings-auth-type", "basic")])

    assert client.get("/probe").status_code == 401


def test_resubmitting_unchanged_credentials_keeps_sessions(app, auth_settings):
    client = app.test_client()
    client.post("/login")
    stored_hash = auth_settings.settings.auth["password"]

    auth_settings.save_settings([("settings-auth-password", stored_hash),
                                 ("settings-auth-username", "admin"),
                                 ("settings-auth-type", "form")])

    assert client.get("/probe").status_code == 200


def test_unrelated_setting_change_keeps_sessions(app, auth_settings):
    client = app.test_client()
    client.post("/login")

    auth_settings.save_settings([("settings-general-instance_name", "Renamed")])

    assert client.get("/probe").status_code == 200
