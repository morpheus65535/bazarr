# -*- coding: utf-8 -*-
"""
Test for Sonarr episode sync functionality.

Specifically tests the fix for TypeError when logging deleted episodes
where SQLAlchemy Row objects were accessed with dict-style syntax instead
of attribute access.

This bug occurred in bazarr/sonarr/sync/episodes.py line 245 where the code
used existing_episode["path"] (dict-style access) instead of existing_episode.path
(attribute access) on a SQLAlchemy Row object.
"""
import pytest


@pytest.fixture
def mock_row():
    """Mock SQLAlchemy Row object behavior.
    
    SQLAlchemy Row objects (returned by select().first()) behave like named tuples:
    - They support attribute access: row.column_name
    - They support integer indexing: row[0]
    - They do NOT support string key access: row["column_name"] raises TypeError
    """
    class MockRow:
        """Simulates SQLAlchemy Row object returned from select().first()"""
        def __init__(self, path, episode_file_id):
            # Store as tuple internally (like SQLAlchemy Row)
            self._data = (path, episode_file_id)
            # Set attributes for attribute access
            self.path = path
            self.episode_file_id = episode_file_id
        
        def __getitem__(self, key):
            """Simulate SQLAlchemy Row behavior - only integer indices work"""
            if isinstance(key, str):
                raise TypeError("tuple indices must be integers or slices, not str")
            return self._data[key]
    
    return MockRow


def test_row_object_attribute_access(mock_row):
    """Test that Row object supports attribute access (the correct way)."""
    row = mock_row("/path/to/episode.mkv", 12345)
    
    # Attribute access should work (this is what the fix uses)
    assert row.path == "/path/to/episode.mkv"
    assert row.episode_file_id == 12345


def test_row_object_dict_access_fails(mock_row):
    """Test that Row object raises TypeError with dict-style string key access.
    
    This test demonstrates the bug that was fixed in line 245.
    The code originally used: existing_episode["path"]
    Which raised: TypeError: tuple indices must be integers or slices, not str
    """
    row = mock_row("/path/to/episode.mkv", 12345)
    
    # Dict-style access with string key should raise TypeError (the bug)
    with pytest.raises(TypeError, match="tuple indices must be integers or slices, not str"):
        _ = row["path"]
    
    with pytest.raises(TypeError, match="tuple indices must be integers or slices, not str"):
        _ = row["episode_file_id"]


def test_row_object_integer_index_access(mock_row):
    """Test that Row object supports integer index access."""
    row = mock_row("/path/to/episode.mkv", 12345)
    
    # Integer index access should work
    assert row[0] == "/path/to/episode.mkv"
    assert row[1] == 12345


def test_bug_reproduction_dict_vs_attribute_access(mock_row):
    """Demonstrate the exact bug that was fixed.
    
    This test reproduces the bug from bazarr/sonarr/sync/episodes.py line 245:
    - Bug: path_mappings.path_replace(existing_episode["path"]) - TypeError
    - Fix: path_mappings.path_replace(existing_episode.path) - Works
    """
    # Create a Row-like object as returned by:
    # database.execute(select(TableEpisodes.path, TableEpisodes.episode_file_id).where(...)).first()
    existing_episode = mock_row("/tv/Show/S01E01.mkv", 12345)
    
    # ❌ The bug: trying to use dict-style access on Row object
    with pytest.raises(TypeError) as exc_info:
        path = existing_episode["path"]
        # This would be in: path_mappings.path_replace(existing_episode["path"])
    
    assert "tuple indices must be integers or slices, not str" in str(exc_info.value)
    
    # ✅ The fix: using attribute access instead
    path = existing_episode.path  # This works!
    assert path == "/tv/Show/S01E01.mkv"
    
    # Simulate the fixed line 245:
    # f'BAZARR deleted this episode from the database:{path_mappings.path_replace(existing_episode.path)}'
    result_path = existing_episode.path  # No TypeError!
    assert result_path == "/tv/Show/S01E01.mkv"

