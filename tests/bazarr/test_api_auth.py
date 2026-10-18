# -*- coding: utf-8 -*-
"""
Tests for API authentication across every route registered on the API blueprint.

Authentication is applied per method with the @authenticate decorator, not globally, so
these tests inventory the routes to catch a new route that is missing it.
"""
import os
from types import SimpleNamespace
from unittest import mock

import pytest
from flask import Flask

from api import api_bp
from api.utils import authenticate

# Routes that are intentionally reachable without an API key.
PUBLIC_ROUTES = {
    ("/api/swagger.json", "GET"),  # API documentation
    ("/api/system/ping", "GET"),  # health check
    ("/api/system/account", "POST"),  # login/logout, validates credentials itself
}

AUTH_CODE_FILE = os.path.join("api", "utils.py")


def _is_authenticated(method):
    code = getattr(method, "__code__", None)
    return code is not None and code.co_name == "wrapper" and code.co_filename.endswith(AUTH_CODE_FILE)


def _route_inventory():
    app = Flask("route-inventory")
    app.register_blueprint(api_bp, url_prefix="/api")

    routes = []
    for rule in app.url_map.iter_rules():
        view = app.view_functions[rule.endpoint]
        resource = getattr(view, "view_class", None)
        if resource is None:
            # The Swagger UI index is served by flask-restx's apidoc, not a Resource.
            continue
        for http_method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            method = getattr(resource, http_method.lower())
            routes.append((rule.rule, http_method, _is_authenticated(method)))
    return routes


INVENTORY = _route_inventory()
PROTECTED = [(path, method) for path, method, authed in INVENTORY if authed]
UNPROTECTED = {(path, method) for path, method, authed in INVENTORY if not authed}


def _concrete_path(path):
    return path.replace("<string:pin_id>", "123")


def test_only_documented_routes_skip_authentication():
    assert UNPROTECTED == PUBLIC_ROUTES


# A JSON body is sent so the webhook routes, which check the content type before authenticating,
# reach the key check. Without it they answer 415 and the key check is never exercised.
@pytest.mark.parametrize("path, method", PROTECTED, ids=[f"{m} {p}" for p, m in PROTECTED])
def test_protected_route_rejects_missing_key(api_client, path, method):
    response = api_client.open(_concrete_path(path), method=method, json={"eventType": "Test"})

    assert response.status_code == 401


@pytest.mark.parametrize("path, method", PROTECTED, ids=[f"{m} {p}" for p, m in PROTECTED])
def test_protected_route_rejects_wrong_key(api_client, path, method):
    response = api_client.open(_concrete_path(path), method=method, json={"eventType": "Test"},
                               headers={"X-API-KEY": "not-the-key"})

    assert response.status_code == 401


@pytest.fixture
def files_sonarr_browse():
    with mock.patch("api.files.files_sonarr.browse_sonarr_filesystem", return_value=None):
        yield


def test_key_in_header_is_accepted(api_client, api_key, files_sonarr_browse):
    response = api_client.get("/api/files/sonarr", headers={"X-API-KEY": api_key})

    assert response.status_code == 200


def test_key_in_query_string_is_accepted(api_client, api_key, files_sonarr_browse):
    response = api_client.get(f"/api/files/sonarr?apikey={api_key}")

    assert response.status_code == 200


@pytest.mark.parametrize("configured_key", [None, ""])
def test_unset_configured_key_does_not_admit_keyless_requests(configured_key):
    app = Flask("unset-key")
    app.config["TESTING"] = True

    @app.route("/probe")
    @authenticate
    def probe():
        return "admitted", 200

    with mock.patch("api.utils.settings", SimpleNamespace(auth=SimpleNamespace(apikey=configured_key))):
        client = app.test_client()
        keyless = client.get("/probe")
        empty_query_key = client.get("/probe?apikey=")

    assert keyless.status_code == 401
    assert empty_query_key.status_code == 401
