import os
import logging
from types import SimpleNamespace
from unittest import mock

import pytest

os.environ["NO_CLI"] = "true"
os.environ["SZ_USER_AGENT"] = "test"
os.environ["BAZARR_VERSION"] = "test" # fixme

logging.getLogger("rebulk").setLevel(logging.WARNING)

API_KEY = "test-api-key"


@pytest.fixture
def api_key():
    return API_KEY


@pytest.fixture
def api_client():
    """Test client for the API blueprint, mounted at /api as in app/server.py.

    The configured API key is pinned to API_KEY so authenticated and unauthenticated
    requests can be told apart.
    """
    from flask import Flask
    from api import api_bp

    app = Flask("api-tests")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.config["TESTING"] = True

    with mock.patch("api.utils.settings", SimpleNamespace(auth=SimpleNamespace(apikey=API_KEY))):
        yield app.test_client()
