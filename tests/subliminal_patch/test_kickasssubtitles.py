# -*- coding: utf-8 -*-
import os
import pytest
from subliminal_patch.providers.kickasssubtitles import KickAssSubtitlesProvider
from subliminal_patch.providers.kickasssubtitles import KickAssSubtitlesSubtitle
from subzero.language import Language


@pytest.fixture(scope="session")
def provider():
    """Fixture for KickAssSubtitles provider.
    
    Requires KICKASSSUBTITLES_API_KEY environment variable.
    """
    api_key = os.environ.get("KICKASSSUBTITLES_API_KEY")
    if not api_key:
        pytest.skip("KICKASSSUBTITLES_API_KEY environment variable not set")
    
    with KickAssSubtitlesProvider(api_key) as provider:
        yield provider


def test_provider_initialization():
    """Test that provider requires API key."""
    from subliminal.exceptions import ConfigurationError
    
    with pytest.raises(ConfigurationError):
        KickAssSubtitlesProvider(api_key=None)
    
    with pytest.raises(ConfigurationError):
        KickAssSubtitlesProvider(api_key="")


def test_subtitle_get_matches_movie(movies):
    """Test subtitle matching for movies."""
    subtitle = KickAssSubtitlesSubtitle(
        language=Language.fromalpha2("en"),
        page_link="https://kickasssubtitles.com",
        task_id="test_task_id",
        file_hash="1234567890abcdef",
        imdb_id="tt0468569",
        title="The Dark Knight",
        year=2008,
    )
    
    matches = subtitle.get_matches(movies["man_of_steel"])
    
    # Should match title at minimum
    assert "title" in matches


def test_subtitle_get_matches_episode(episodes):
    """Test subtitle matching for episodes."""
    subtitle = KickAssSubtitlesSubtitle(
        language=Language.fromalpha2("en"),
        page_link="https://kickasssubtitles.com",
        task_id="test_task_id",
        season=1,
        episode=1,
    )
    
    matches = subtitle.get_matches(episodes["breaking_bad_s01e01"])
    
    # Should match series, season, and episode
    assert "series" in matches
    assert "season" in matches
    assert "episode" in matches


def test_subtitle_get_matches_hash(episodes):
    """Test that hash matching works."""
    # Using the actual hash from got_s03e10 fixture
    subtitle = KickAssSubtitlesSubtitle(
        language=Language.fromalpha2("en"),
        page_link="https://kickasssubtitles.com",
        task_id="test_task_id",
        file_hash="b850baa096976c22",  # Hash from got_s03e10
        season=3,
        episode=10,
    )
    
    # The episode has matching hash in its hashes dict
    episode = episodes["got_s03e10"]
    matches = subtitle.get_matches(episode)
    
    # Should match hash since it matches the episode's opensubtitles hash
    assert "hash" in matches
    # Should also match series, season, episode
    assert "series" in matches
    assert "season" in matches
    assert "episode" in matches


# Integration tests require actual video files with computed hashes
# These tests are skipped by default as they require real files and may hit API rate limits

def test_list_subtitles_requires_hash(provider, movies, languages):
    """Test that provider requires video file hash for searching.
    
    Note: This will be skipped if video file doesn't exist on disk.
    KickAssSubtitles API requires filename, filesize, and OpenSubtitles hash.
    """
    video = movies["man_of_steel"]
    
    # Provider requires actual file to compute hash
    # This test documents the requirement but will skip without real file
    if not hasattr(video, 'name') or not os.path.exists(video.name):
        pytest.skip("Video file not available - hash computation requires actual file")
    
    subtitles = provider.list_subtitles(video, {languages["en"]})
    assert isinstance(subtitles, list)
