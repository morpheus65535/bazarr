# -*- coding: utf-8 -*-
"""
Tests for Plex authentication: token encryption, the PIN OAuth flow, token validation, logout,
and API key storage (api/plex/oauth.py and api/plex/security.py).
"""
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from api.plex import oauth
from api.plex.exceptions import InvalidTokenError, PlexConnectionError, PlexPinExpiredError, UnauthorizedError
from api.plex.security import TokenManager, pin_cache, sanitize_log_data, sanitize_server_url


class _Attrs(dict):
    """Dict that also allows attribute get and set, like the settings sections."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def plex_settings():
    plex = _Attrs(
        auth_method="apikey", apikey="", apikey_encrypted=False, encryption_key="", token="",
        ip="127.0.0.1", port=32400, ssl=False, username="", email="", user_id="", client_identifier="",
        server_name="", server_url="", server_machine_id="", server_local=False,
    )
    general = _Attrs(instance_name="Bazarr", use_plex=False)
    fake = SimpleNamespace(plex=plex, general=general)

    with mock.patch.object(oauth, "settings", fake), \
            mock.patch.object(oauth, "write_config") as write_config, \
            mock.patch("app.config.settings", fake), \
            mock.patch("app.config.write_config"):
        yield SimpleNamespace(settings=fake, write_config=write_config)


@pytest.fixture
def pins():
    """Seed and track PINs in the module-level cache so they are removed after each test."""
    tracked = []

    def add(pin_id, **data):
        data.setdefault("code", "ABCD")
        data.setdefault("client_id", "client-1")
        data.setdefault("state_token", "good-state")
        data.setdefault("created_at", datetime.now().isoformat())
        pin_cache.set(str(pin_id), data)
        tracked.append(str(pin_id))

    def track(pin_id):
        tracked.append(str(pin_id))

    helpers = SimpleNamespace(add=add, track=track)
    yield helpers
    for pin_id in tracked:
        pin_cache.delete(pin_id)


def _response(json_data=None, status_code=200):
    response = mock.Mock(status_code=status_code)
    response.json.return_value = json_data or {}
    response.raise_for_status.return_value = None
    return response


# Token encryption and state tokens

def test_token_manager_round_trips_token():
    manager = TokenManager("key-a")

    assert manager.decrypt(manager.encrypt("secret-token")) == "secret-token"


def test_token_manager_salts_each_ciphertext():
    manager = TokenManager("key-a")

    assert manager.encrypt("same") != manager.encrypt("same")


def test_token_manager_encrypt_empty_returns_none():
    assert TokenManager("key-a").encrypt("") is None


def test_token_manager_rejects_token_from_another_key():
    encrypted = TokenManager("key-a").encrypt("secret-token")

    with pytest.raises(InvalidTokenError):
        TokenManager("key-b").decrypt(encrypted)


def test_token_manager_rejects_tampered_ciphertext():
    encrypted = TokenManager("key-a").encrypt("secret-token")
    tampered = encrypted[:-1] + ("A" if encrypted[-1] != "A" else "B")

    with pytest.raises(InvalidTokenError):
        TokenManager("key-a").decrypt(tampered)


def test_token_manager_rejects_garbage():
    with pytest.raises(InvalidTokenError):
        TokenManager("key-a").decrypt("not-a-token")


def test_state_tokens_are_unique_and_validate_only_exact_match():
    manager = TokenManager("key-a")
    state = manager.generate_state_token()

    assert state != manager.generate_state_token()
    assert manager.validate_state_token(state, state) is True
    assert manager.validate_state_token(state, state + "x") is False
    assert manager.validate_state_token("", state) is False
    assert manager.validate_state_token(state, "") is False


def test_encrypt_and_decrypt_token_helpers_use_settings_key(plex_settings):
    encrypted = oauth.encrypt_token("plex-token")

    assert encrypted != "plex-token"
    assert oauth.decrypt_token(encrypted) == "plex-token"
    assert plex_settings.settings.plex.encryption_key  # generated and persisted on first use
    plex_settings.write_config.assert_called()


def test_decrypt_token_helper_wraps_failure_as_invalid_token(plex_settings):
    with pytest.raises(InvalidTokenError, match="Failed to decrypt"):
        oauth.decrypt_token("not-a-token")


# Sanitizers

@pytest.mark.parametrize("value", ["", "short", "12345678"])
def test_sanitize_log_data_hides_short_values(value):
    assert sanitize_log_data(value) == "***"


def test_sanitize_log_data_never_returns_full_value():
    token = "abcdefghijklmnop"

    sanitized = sanitize_log_data(token)

    assert sanitized == "abcd...mnop"
    assert token not in sanitized


@pytest.mark.parametrize(
    "url, expected",
    [
        ("plex.local:32400/", "https://plex.local:32400"),
        ("http://10.0.0.5:32400/", "http://10.0.0.5:32400"),
        ("", ""),
    ],
)
def test_sanitize_server_url(url, expected):
    assert sanitize_server_url(url) == expected


# get_decrypted_token

def test_get_decrypted_token_oauth_returns_decrypted_token(plex_settings):
    plex_settings.settings.plex.auth_method = "oauth"
    plex_settings.settings.plex.token = oauth.encrypt_token("plex-token")

    assert oauth.get_decrypted_token() == "plex-token"


def test_get_decrypted_token_oauth_without_token_is_none(plex_settings):
    plex_settings.settings.plex.auth_method = "oauth"

    assert oauth.get_decrypted_token() is None


def test_get_decrypted_token_apikey_unset_is_none(plex_settings):
    assert oauth.get_decrypted_token() is None


def test_get_decrypted_token_encrypts_plaintext_apikey_in_place(plex_settings):
    plex_settings.settings.plex.apikey = "plain-key"

    assert oauth.get_decrypted_token() == "plain-key"
    stored = plex_settings.settings.plex.apikey
    assert stored != "plain-key"
    assert plex_settings.settings.plex.apikey_encrypted is True
    assert oauth.decrypt_token(stored) == "plain-key"


# Token validation against plex.tv

@pytest.mark.parametrize(
    "status_code, error",
    [(401, InvalidTokenError), (403, UnauthorizedError)],
)
def test_validate_plex_token_maps_rejections(status_code, error):
    with mock.patch.object(oauth.requests, "get", return_value=_response(status_code=status_code)):
        with pytest.raises(error):
            oauth.validate_plex_token("token")


def test_validate_plex_token_maps_connection_failure():
    with mock.patch.object(oauth.requests, "get", side_effect=requests.exceptions.ConnectionError("down")):
        with pytest.raises(PlexConnectionError):
            oauth.validate_plex_token("token")


def test_validate_plex_token_requires_a_token():
    with pytest.raises(InvalidTokenError):
        oauth.validate_plex_token("")


# PIN creation

def test_pin_create_returns_pin_and_caches_state(api_client, api_key, plex_settings, pins):
    pins.track("99")

    with mock.patch.object(oauth.requests, "post",
                           return_value=_response({"id": 99, "code": "ABCD"})):
        response = api_client.post("/api/plex/oauth/pin", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    data = response.json["data"]
    assert data["pinId"] == 99
    assert data["code"] == "ABCD"
    assert data["clientId"]
    assert data["authUrl"].startswith("https://app.plex.tv/auth#?clientID=")
    assert "code=ABCD" in data["authUrl"]
    assert pin_cache.get("99")["state_token"] == data["state"]


def test_pin_create_reports_plex_outage(api_client, api_key, plex_settings):
    with mock.patch.object(oauth.requests, "post", side_effect=requests.exceptions.ConnectionError("down")):
        response = api_client.post("/api/plex/oauth/pin", headers={"X-API-KEY": api_key})

    assert response.status_code == 503
    assert response.json["code"] == "PLEX_CONNECTION_ERROR"


# PIN check

def _check(api_client, api_key, pin_id, state=None):
    url = f"/api/plex/oauth/pin/{pin_id}/check"
    if state is not None:
        url += f"?state={state}"
    return api_client.get(url, headers={"X-API-KEY": api_key})


def test_pin_check_before_authorization_changes_nothing(api_client, api_key, plex_settings, pins):
    pins.add("201")

    with mock.patch.object(oauth.requests, "get", return_value=_response({"authToken": None, "code": "ABCD"})):
        response = _check(api_client, api_key, "201", state="good-state")

    assert response.status_code == 200
    assert response.json["data"] == {"authenticated": False, "code": "ABCD"}
    assert plex_settings.settings.plex.token == ""
    assert plex_settings.settings.plex.auth_method == "apikey"


def test_pin_check_success_stores_encrypted_token_and_clears_pin(api_client, api_key, plex_settings, pins):
    pins.add("202")
    plex_response = _response({"authToken": "plex-token", "code": "ABCD"})
    user = {"id": 7, "username": "alice", "email": "alice@example.com"}

    with mock.patch.object(oauth.requests, "get", return_value=plex_response), \
            mock.patch.object(oauth, "validate_plex_token", return_value=user):
        response = _check(api_client, api_key, "202", state="good-state")

    assert response.status_code == 200
    assert response.json["data"] == {"authenticated": True, "username": "alice", "email": "alice@example.com"}
    settings = plex_settings.settings.plex
    assert settings.auth_method == "oauth"
    assert settings.token != "plex-token"
    assert oauth.decrypt_token(settings.token) == "plex-token"
    assert settings.user_id == "7"
    assert pin_cache.get("202") is None


def test_pin_check_rejects_mismatched_state(api_client, api_key, plex_settings, pins):
    pins.add("203", state_token="good-state")
    plex_response = _response({"authToken": "plex-token", "code": "ABCD"})

    with mock.patch.object(oauth.requests, "get", return_value=plex_response) as plex_get, \
            mock.patch.object(oauth, "validate_plex_token", return_value={"id": 7, "username": "alice"}):
        response = _check(api_client, api_key, "203", state="attacker-state")

    assert response.status_code == 403
    assert response.json["code"] == "CSRF_STATE_MISMATCH"
    plex_get.assert_not_called()
    assert plex_settings.settings.plex.token == ""


def test_pin_check_without_state_still_authenticates(api_client, api_key, plex_settings, pins):
    # The shipped frontend does not send the state parameter, so its absence must stay accepted.
    pins.add("205")
    plex_response = _response({"authToken": "plex-token", "code": "ABCD"})

    with mock.patch.object(oauth.requests, "get", return_value=plex_response), \
            mock.patch.object(oauth, "validate_plex_token", return_value={"id": 7, "username": "alice"}):
        response = _check(api_client, api_key, "205")

    assert response.status_code == 200
    assert response.json["data"]["authenticated"] is True


def test_pin_check_for_unknown_pin_makes_no_plex_call(api_client, api_key, plex_settings):
    with mock.patch.object(oauth.requests, "get") as plex_get, pytest.raises(PlexPinExpiredError):
        _check(api_client, api_key, "unknown")

    plex_get.assert_not_called()
    assert plex_settings.settings.plex.token == ""


def test_pin_check_expired_on_plex_clears_pin(api_client, api_key, plex_settings, pins):
    pins.add("204")

    with mock.patch.object(oauth.requests, "get", return_value=_response(status_code=404)), \
            pytest.raises(PlexPinExpiredError):
        _check(api_client, api_key, "204", state="good-state")

    assert pin_cache.get("204") is None


# Validate, logout, and API key

def test_validate_without_token_reports_invalid(api_client, api_key, plex_settings):
    response = api_client.get("/api/plex/oauth/validate", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    assert response.json["data"]["valid"] is False


def test_validate_reports_rejected_token(api_client, api_key, plex_settings):
    plex_settings.settings.plex.auth_method = "oauth"
    plex_settings.settings.plex.token = oauth.encrypt_token("plex-token")

    with mock.patch.object(oauth, "validate_plex_token", side_effect=InvalidTokenError("expired")):
        response = api_client.get("/api/plex/oauth/validate", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    assert response.json["data"]["valid"] is False
    assert response.json["data"]["code"] == "INVALID_TOKEN"


def test_logout_clears_plex_credentials(api_client, api_key, plex_settings):
    settings = plex_settings.settings.plex
    settings.auth_method = "oauth"
    settings.token = oauth.encrypt_token("plex-token")
    plex_settings.settings.general.use_plex = True

    response = api_client.post("/api/plex/oauth/logout", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    assert settings.token == ""
    assert settings.auth_method == "apikey"
    assert plex_settings.settings.general.use_plex is False
    plex_settings.write_config.assert_called()


def test_api_key_is_stored_encrypted(api_client, api_key, plex_settings):
    response = api_client.post("/api/plex/apikey", data={"apikey": "plain-key"},
                               headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    settings = plex_settings.settings.plex
    assert settings.apikey != "plain-key"
    assert settings.apikey_encrypted is True
    assert settings.auth_method == "apikey"
    assert oauth.decrypt_token(settings.apikey) == "plain-key"


def test_api_key_rejects_blank_value(api_client, api_key, plex_settings):
    response = api_client.post("/api/plex/apikey", data={"apikey": "   "}, headers={"X-API-KEY": api_key})

    assert response.status_code == 400
    assert plex_settings.settings.plex.apikey == ""
