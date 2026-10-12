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
def memory_session():
    """SQLAlchemy session on a fresh in-memory SQLite database with the application schema."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    from app.database import metadata

    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    metadata.create_all(engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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

    from app.config import settings as real_settings

    class _SettingsWithKey:
        # Only the API key is overridden; every other setting is read from the real configuration
        auth = SimpleNamespace(apikey=API_KEY)

        def __getattr__(self, name):
            return getattr(real_settings, name)

    with mock.patch("api.utils.settings", _SettingsWithKey()):
        yield app.test_client()
