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
def indexed_subtitles(memory_session, monkeypatch):
    """Point is_indexed_subtitle_path at the in-memory session. Call the returned function to index a path."""
    import app.database as app_database
    from app.database import TableEpisodes, TableEpisodesSubtitles, TableShows

    monkeypatch.setattr(app_database, "database", memory_session)
    memory_session.add(TableShows(path="/tv/show", sonarrSeriesId=1, title="Show"))
    memory_session.commit()  # the episode references the series, so it must be flushed first
    memory_session.add(TableEpisodes(sonarrEpisodeId=1, sonarrSeriesId=1, path="/tv/show/ep.mkv", season=1,
                                     episode=1, title="Pilot"))
    memory_session.commit()

    def index(path):
        memory_session.add(TableEpisodesSubtitles(language="en", hi=False, forced=False, path=path,
                                                  sonarrEpisodeId=1, sonarrSeriesId=1))
        memory_session.commit()
        return path

    return index


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
