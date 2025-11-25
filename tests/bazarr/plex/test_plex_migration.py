# coding=utf-8

"""
Tests for Plex library migration from string to list.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestPlexLibraryMigration:
    """Test the migrate_plex_library_to_list function."""

    @patch('app.config.write_config')
    @patch('app.config.settings')
    @patch('app.config.logging')
    def test_migrate_movie_library_string_to_list(self, mock_logging, mock_settings, mock_write):
        """Test migration of movie library from string to list."""
        # Setup
        mock_settings.plex.movie_library = "Movies"
        mock_settings.plex.series_library = []
        
        # Import and run
        from app.config import migrate_plex_library_to_list
        migrate_plex_library_to_list()
        
        # Verify
        assert mock_settings.plex.movie_library == ["Movies"]
        mock_write.assert_called_once()
        mock_logging.info.assert_any_call("Migrated plex.movie_library from string to list: Movies")

    @patch('app.config.write_config')
    @patch('app.config.settings')
    @patch('app.config.logging')
    def test_migrate_series_library_string_to_list(self, mock_logging, mock_settings, mock_write):
        """Test migration of series library from string to list."""
        # Setup
        mock_settings.plex.movie_library = []
        mock_settings.plex.series_library = "TV Shows"
        
        # Import and run
        from app.config import migrate_plex_library_to_list
        migrate_plex_library_to_list()
        
        # Verify
        assert mock_settings.plex.series_library == ["TV Shows"]
        mock_write.assert_called_once()
        mock_logging.info.assert_any_call("Migrated plex.series_library from string to list: TV Shows")

    @patch('app.config.write_config')
    @patch('app.config.settings')
    @patch('app.config.logging')
    def test_migrate_both_libraries(self, mock_logging, mock_settings, mock_write):
        """Test migration of both libraries."""
        # Setup
        mock_settings.plex.movie_library = "Movies"
        mock_settings.plex.series_library = "TV Shows"
        
        # Import and run
        from app.config import migrate_plex_library_to_list
        migrate_plex_library_to_list()
        
        # Verify
        assert mock_settings.plex.movie_library == ["Movies"]
        assert mock_settings.plex.series_library == ["TV Shows"]
        mock_write.assert_called_once()
        assert mock_logging.info.call_count == 2

    @patch('app.config.write_config')
    @patch('app.config.settings')
    def test_migrate_empty_string_to_empty_list(self, mock_settings, mock_write):
        """Test migration of empty string to empty list."""
        # Setup
        mock_settings.plex.movie_library = ""
        mock_settings.plex.series_library = ""
        
        # Import and run
        from app.config import migrate_plex_library_to_list
        migrate_plex_library_to_list()
        
        # Verify
        assert mock_settings.plex.movie_library == []
        assert mock_settings.plex.series_library == []
        mock_write.assert_called_once()

    @patch('app.config.write_config')
    @patch('app.config.settings')
    def test_no_migration_when_already_list(self, mock_settings, mock_write):
        """Test that already-list values are not changed."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_settings.plex.series_library = ["TV Shows"]
        
        # Import and run
        from app.config import migrate_plex_library_to_list
        migrate_plex_library_to_list()
        
        # Verify - no changes, no write
        assert mock_settings.plex.movie_library == ["Movies", "4K Movies"]
        assert mock_settings.plex.series_library == ["TV Shows"]
        mock_write.assert_not_called()

    @patch('app.config.write_config')
    @patch('app.config.settings')
    @patch('app.config.logging')
    def test_partial_migration(self, mock_logging, mock_settings, mock_write):
        """Test migration when one is string and one is list."""
        # Setup
        mock_settings.plex.movie_library = "Movies"
        mock_settings.plex.series_library = ["TV Shows"]
        
        # Import and run
        from app.config import migrate_plex_library_to_list
        migrate_plex_library_to_list()
        
        # Verify
        assert mock_settings.plex.movie_library == ["Movies"]
        assert mock_settings.plex.series_library == ["TV Shows"]
        mock_write.assert_called_once()
        mock_logging.info.assert_called_once_with("Migrated plex.movie_library from string to list: Movies")
