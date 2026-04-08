"""Tests for the Jellyfin HTTP client.

Mock responses are validated against Jellyfin's OpenAPI spec via fake_jellyfin.
"""

import os
from unittest.mock import patch, MagicMock

import pytest
from bazarr.jellyfin.client import JellyfinClient
from fake_jellyfin import (
    FakeJellyfinClient,
    OPENAPI_PATH,
    make_movie,
    make_episode,
)


@pytest.fixture
def client():
    return JellyfinClient("http://jellyfin:8096", "test-api-key")



def test_fake_client_has_same_interface_as_real():
    """Ensure FakeJellyfinClient implements all public methods of JellyfinClient."""
    real_methods = {m for m in dir(JellyfinClient) if not m.startswith('_')}
    fake_methods = {m for m in dir(FakeJellyfinClient) if not m.startswith('_')}
    missing = real_methods - fake_methods
    assert not missing, f"FakeJellyfinClient is missing methods: {missing}"


@pytest.mark.skipif(not os.path.exists(OPENAPI_PATH), reason="jellyfin-openapi.json not found")
class TestFakeClientMatchesContract:
    """Verify that FakeJellyfinClient returns schema-valid responses."""

    def test_system_info(self):
        fake = FakeJellyfinClient()
        fake.get_system_info()  # validates internally

    def test_libraries(self):
        fake = FakeJellyfinClient()
        fake.get_libraries()

    def test_items(self):
        fake = FakeJellyfinClient()
        fake.items = [make_movie()]
        fake.get_items({})

    def test_episodes(self):
        fake = FakeJellyfinClient()
        fake.episodes = {"s1": {1: [make_episode()]}}
        fake.get_episodes("s1", 1)

    def test_empty_items(self):
        fake = FakeJellyfinClient()
        fake.get_items({})

    def test_empty_episodes(self):
        fake = FakeJellyfinClient()
        fake.get_episodes("s1", 1)



@patch.object(JellyfinClient, "post")
def test_refresh_item(mock_post, client):
    mock_post.return_value = MagicMock()
    client.refresh_item("item-123")
    mock_post.assert_called_once()
    assert "/Items/item-123/Refresh" in mock_post.call_args[0][0]


@patch.object(JellyfinClient, "post")
def test_report_media_updated(mock_post, client):
    mock_post.return_value = MagicMock()
    client.report_media_updated("/media/movies/Test Movie")
    mock_post.assert_called_once_with("/Library/Media/Updated", json={
        "Updates": [{"Path": "/media/movies/Test Movie", "UpdateType": "Modified"}],
    })


