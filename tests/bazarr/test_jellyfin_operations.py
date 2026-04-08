"""Tests for Jellyfin operations using FakeJellyfinClient.

All test data is validated against Jellyfin's OpenAPI spec via the fake client.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

# Mock app.config before importing operations
mock_config = MagicMock()
sys.modules.setdefault("app", MagicMock())
sys.modules.setdefault("app.config", mock_config)
mock_config.settings = MagicMock()

from bazarr.jellyfin.operations import (
    jellyfin_test_connection,
    jellyfin_get_libraries,
    jellyfin_refresh_item,
    jellyfin_update_library,
)
from fake_jellyfin import FakeJellyfinClient, make_movie, make_series, make_episode



@pytest.fixture
def fake():
    """Provide a FakeJellyfinClient and patch get_jellyfin_client to return it."""
    client = FakeJellyfinClient()
    with patch("bazarr.jellyfin.operations.get_jellyfin_client", return_value=client):
        yield client


@pytest.fixture
def settings():
    return mock_config.settings



def test_test_connection_success():
    with patch("bazarr.jellyfin.operations.get_jellyfin_client") as mock_get:
        client = FakeJellyfinClient()
        mock_get.return_value = client
        result = jellyfin_test_connection()
    assert result["success"] is True
    assert result["server_name"] == "TestServer"
    assert result["version"] == "10.12.0"


def test_test_connection_failure():
    with patch("bazarr.jellyfin.operations.get_jellyfin_client", side_effect=Exception("refused")):
        result = jellyfin_test_connection()
    assert result["success"] is False
    assert "refused" in result["error"]


def test_test_connection_with_explicit_params():
    with patch("bazarr.jellyfin.operations.get_jellyfin_client") as mock_get:
        mock_get.return_value = FakeJellyfinClient()
        jellyfin_test_connection(url="http://custom:8096", apikey="key")
        mock_get.assert_called_once_with("http://custom:8096", "key")



def test_get_libraries_filters_by_collection_type():
    with patch("bazarr.jellyfin.operations.get_jellyfin_client") as mock_get:
        client = FakeJellyfinClient()
        client.libraries.append({
            "Name": "Music", "Locations": [], "CollectionType": "music", "ItemId": "lib-music",
        })
        mock_get.return_value = client
        libs = jellyfin_get_libraries()
    assert len(libs) == 2
    assert libs[0]["name"] == "Movies"
    assert libs[1]["name"] == "Shows"



def test_get_libraries_handles_null_collection_type():
    with patch("bazarr.jellyfin.operations.get_jellyfin_client") as mock_get:
        client = FakeJellyfinClient()
        client.libraries = [{"Name": "Misc", "Locations": [], "CollectionType": None, "ItemId": "x"}]
        mock_get.return_value = client
        libs = jellyfin_get_libraries()
    assert len(libs) == 0


def test_get_libraries_returns_empty_on_error():
    with patch("bazarr.jellyfin.operations.get_jellyfin_client", side_effect=Exception("fail")):
        libs = jellyfin_get_libraries()
    assert libs == []



def test_refresh_movie_immediate(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_movie(id="m1", imdb_id="tt123")]

    jellyfin_refresh_item(imdb_id="tt123", is_movie=True)

    assert fake.refresh_item_calls == ["m1"]
    assert fake.report_media_updated_calls == []


def test_refresh_movie_async(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "async"
    fake.items = [make_movie(id="m1", imdb_id="tt123", path="/media/movie.mkv")]

    jellyfin_refresh_item(imdb_id="tt123", is_movie=True)

    assert fake.report_media_updated_calls == ["/media/movie.mkv"]
    assert fake.refresh_item_calls == []


def test_refresh_movie_by_tmdb(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_movie(id="m1", imdb_id=None, tmdb_id="999")]

    jellyfin_refresh_item(imdb_id=None, tmdb_id="999", is_movie=True)

    assert fake.refresh_item_calls == ["m1"]


def test_refresh_movie_by_title(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_movie(id="m1", imdb_id=None, tmdb_id=None)]

    jellyfin_refresh_item(imdb_id=None, is_movie=True, title="Test Movie")

    assert fake.refresh_item_calls == ["m1"]


def test_refresh_movie_title_case_insensitive(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_movie(id="m1", name="The Matrix", imdb_id=None, tmdb_id=None)]

    jellyfin_refresh_item(imdb_id=None, is_movie=True, title="the matrix")

    assert fake.refresh_item_calls == ["m1"]


def test_refresh_episode_immediate(fake, settings):
    settings.jellyfin.series_library_ids = ["lib-shows"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_series(id="s1", imdb_id="tt456")]
    fake.episodes = {"s1": {2: [make_episode(id="ep5", index=5), make_episode(id="ep6", index=6)]}}

    jellyfin_refresh_item(imdb_id="tt456", is_movie=False, season=2, episode=6)

    assert fake.refresh_item_calls == ["ep6"]


def test_refresh_episode_async(fake, settings):
    settings.jellyfin.series_library_ids = ["lib-shows"]
    settings.jellyfin.get.return_value = "async"
    fake.items = [make_series(id="s1", imdb_id="tt456", path="/media/shows/Show")]

    jellyfin_refresh_item(imdb_id="tt456", is_movie=False, season=1, episode=1)

    assert fake.report_media_updated_calls == ["/media/shows/Show"]


def test_refresh_episode_by_tvdb(fake, settings):
    settings.jellyfin.series_library_ids = ["lib-shows"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_series(id="s1", imdb_id=None, tvdb_id="789")]
    fake.episodes = {"s1": {1: [make_episode(id="ep1", index=1)]}}

    jellyfin_refresh_item(imdb_id=None, tvdb_id=789, is_movie=False, season=1, episode=1)

    assert fake.refresh_item_calls == ["ep1"]


def test_refresh_falls_back_to_library_update(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = []  # nothing to find

    jellyfin_refresh_item(imdb_id="tt999", is_movie=True)

    # Falls back to refreshing the library ID
    assert fake.refresh_item_calls == ["lib-movies"]


def test_refresh_skips_when_no_libraries(fake, settings):
    settings.jellyfin.movie_library_ids = []

    jellyfin_refresh_item(imdb_id="tt123", is_movie=True)

    assert fake.refresh_item_calls == []
    assert fake.report_media_updated_calls == []



def test_refresh_with_no_ids_and_no_title_falls_back(fake, settings):
    """No IDs, no title — should fall back to library update."""
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_movie()]

    jellyfin_refresh_item(imdb_id=None, tmdb_id=None, tvdb_id=None, title=None, is_movie=True)

    # Falls back to library refresh
    assert fake.refresh_item_calls == ["lib-movies"]


def test_refresh_movie_not_found_falls_back(fake, settings):
    """Movie exists in library but with different IDs — falls back to library update."""
    settings.jellyfin.movie_library_ids = ["lib-movies"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_movie(imdb_id="tt999", tmdb_id="999")]

    jellyfin_refresh_item(imdb_id="tt000", tmdb_id="000", is_movie=True)

    assert fake.refresh_item_calls == ["lib-movies"]


def test_refresh_episode_not_found_in_season(fake, settings):
    """Series found but episode not in that season — falls back to library update."""
    settings.jellyfin.series_library_ids = ["lib-shows"]
    settings.jellyfin.get.return_value = "immediate"
    fake.items = [make_series(id="s1", imdb_id="tt456")]
    fake.episodes = {"s1": {1: [make_episode(id="ep1", index=1)]}}

    jellyfin_refresh_item(imdb_id="tt456", is_movie=False, season=1, episode=99)

    # Episode 99 not found, falls back
    assert fake.refresh_item_calls == ["lib-shows"]


def test_update_library_refreshes_each_configured(fake, settings):
    settings.jellyfin.movie_library_ids = ["lib1", "lib2"]
    jellyfin_update_library(fake, is_movie_library=True, library_ids=["lib1", "lib2"])
    assert fake.refresh_item_calls == ["lib1", "lib2"]


def test_update_library_skips_empty_ids(fake, settings):
    settings.jellyfin.series_library_ids = ["", "lib1"]
    jellyfin_update_library(fake, is_movie_library=False, library_ids=["", "lib1"])
    assert fake.refresh_item_calls == ["lib1"]
