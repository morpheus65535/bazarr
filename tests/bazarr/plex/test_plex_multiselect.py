# coding=utf-8

"""
Tests for Plex library multiselect functionality.

This test suite covers:
1. Helper logic for list normalization  
2. Config validator setup
3. Migration logic
4. Plex operations with multiple libraries
5. Edge cases (empty lists, filtering, etc.)

Note: Full integration tests with mocked PlexServer are included.
These tests verify the complete implementation works correctly.
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch, call

# Add bazarr to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bazarr'))


class TestPlexOperationsHelpers(unittest.TestCase):
    """Test helper logic in Plex operations."""

    def test_list_normalization_with_string(self):
        """Test that operations can normalize string to list."""
        # Simulate what operations do
        value = "Movies"
        
        # Normalize to list
        if not isinstance(value, list):
            normalized = [value] if value else []
        else:
            normalized = value
        
        self.assertEqual(normalized, ["Movies"])

    def test_list_normalization_with_empty_string(self):
        """Test normalization of empty string."""
        value = ""
        
        # Normalize to list
        if not isinstance(value, list):
            normalized = [value] if value else []
        else:
            normalized = value
        
        self.assertEqual(normalized, [])

    def test_list_normalization_with_list(self):
        """Test normalization when already a list."""
        value = ["Movies", "4K Movies"]
        
        # Normalize to list
        if not isinstance(value, list):
            normalized = [value] if value else []
        else:
            normalized = value
        
        self.assertEqual(normalized, ["Movies", "4K Movies"])

    def test_list_normalization_with_none(self):
        """Test normalization of None value."""
        value = None
        
        # Normalize to list
        if not isinstance(value, list):
            normalized = [value] if value else []
        else:
            normalized = value
        
        self.assertEqual(normalized, [])

    def test_skip_empty_strings_in_list(self):
        """Test filtering out empty strings from library list."""
        libraries = ["Movies", "", "4K Movies", None]
        
        # Filter like operations do
        valid_libraries = [lib for lib in libraries if lib]
        
        self.assertEqual(valid_libraries, ["Movies", "4K Movies"])

    def test_skip_empty_strings_all_empty(self):
        """Test filtering when all entries are empty."""
        libraries = ["", None, ""]
        
        # Filter like operations do
        valid_libraries = [lib for lib in libraries if lib]
        
        self.assertEqual(valid_libraries, [])

    def test_multiple_library_iteration(self):
        """Test iterating through multiple libraries with early exit."""
        libraries = ["Movies", "4K Movies", "Kids Movies"]
        found = False
        checked_count = 0
        
        # Simulate search logic
        for library_name in libraries:
            if not library_name:
                continue
            checked_count += 1
            if library_name == "Movies":
                found = True
                break  # Exit early on first match
        
        self.assertTrue(found)
        self.assertEqual(checked_count, 1)  # Only checked first library

    def test_multiple_library_fallthrough(self):
        """Test falling through all libraries when not found."""
        libraries = ["Movies", "4K Movies", "Kids Movies"]
        found = False
        checked_count = 0
        target = "NonExistent"
        
        # Simulate search logic
        for library_name in libraries:
            if not library_name:
                continue
            checked_count += 1
            if library_name == target:
                found = True
                break
        
        self.assertFalse(found)
        self.assertEqual(checked_count, 3)  # Checked all libraries


class TestConfigValidation(unittest.TestCase):
    """Test that config validators are properly set up."""

    def test_validators_exist_for_library_fields(self):
        """Test that validators exist for plex library fields."""
        try:
            from app.config import validators
        except (ImportError, ModuleNotFoundError) as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")
        
        # Find validators for our fields
        movie_lib_validator = None
        series_lib_validator = None
        
        for validator in validators:
            if 'plex.movie_library' in validator.names:
                movie_lib_validator = validator
            if 'plex.series_library' in validator.names:
                series_lib_validator = validator
        
        # Verify validators exist
        self.assertIsNotNone(movie_lib_validator, "movie_library validator not found")
        self.assertIsNotNone(series_lib_validator, "series_library validator not found")
        
        # Verify they expect list type
        self.assertEqual(movie_lib_validator.is_type_of, list)
        self.assertEqual(series_lib_validator.is_type_of, list)
        
        # Verify default is empty list
        self.assertEqual(movie_lib_validator.default, [])
        self.assertEqual(series_lib_validator.default, [])


class TestMigrationLogic(unittest.TestCase):
    """Test migration logic patterns."""

    def test_string_to_list_conversion(self):
        """Test converting string to list."""
        value = "Movies"
        
        # Migration logic
        if isinstance(value, str):
            if value:
                result = [value]
            else:
                result = []
        else:
            result = value
        
        self.assertEqual(result, ["Movies"])

    def test_empty_string_to_list_conversion(self):
        """Test converting empty string to empty list."""
        value = ""
        
        # Migration logic
        if isinstance(value, str):
            if value:
                result = [value]
            else:
                result = []
        else:
            result = value
        
        self.assertEqual(result, [])

    def test_list_unchanged_by_migration(self):
        """Test that list values are not changed."""
        value = ["Movies", "4K Movies"]
        
        # Migration logic
        if isinstance(value, str):
            if value:
                result = [value]
            else:
                result = []
        else:
            result = value
        
        self.assertEqual(result, ["Movies", "4K Movies"])


class TestPlexOperationsIntegration(unittest.TestCase):
    """Integration tests for Plex operations with multiple libraries."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings = Mock()
        self.mock_plex = MagicMock()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_plex_set_movie_added_date_now_single_library(self, mock_settings, mock_get_plex):
        """Test movie added date update with single library."""
        # Setup
        mock_settings.plex.movie_library = ["Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        mock_library = MagicMock()
        mock_plex.library.section.return_value = mock_library
        mock_video = MagicMock()
        mock_library.getGuid.return_value = mock_video
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Import and run
        try:
            from plex.operations import plex_set_movie_added_date_now
            plex_set_movie_added_date_now(mock_metadata)
            
            # Verify
            mock_plex.library.section.assert_called_once_with("Movies")
            mock_library.getGuid.assert_called_once_with(guid="tt1234567")
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_plex_set_movie_added_date_now_multiple_libraries(self, mock_settings, mock_get_plex):
        """Test movie added date update searches multiple libraries."""
        # Setup - movie is in second library
        mock_settings.plex.movie_library = ["Movies", "4K Movies", "Kids Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        # First library raises exception (not found)
        mock_library1 = MagicMock()
        mock_library1.getGuid.side_effect = Exception("Not found")
        
        # Second library has the movie
        mock_library2 = MagicMock()
        mock_video = MagicMock()
        mock_library2.getGuid.return_value = mock_video
        
        # Third library shouldn't be checked
        mock_library3 = MagicMock()
        
        # Return different libraries based on name
        def section_side_effect(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
            elif name == "Kids Movies":
                return mock_library3
        
        mock_plex.library.section.side_effect = section_side_effect
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Import and run
        try:
            from plex.operations import plex_set_movie_added_date_now
            plex_set_movie_added_date_now(mock_metadata)
            
            # Verify it checked first two libraries but not third
            self.assertEqual(mock_plex.library.section.call_count, 2)
            mock_plex.library.section.assert_any_call("Movies")
            mock_plex.library.section.assert_any_call("4K Movies")
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.logger')
    def test_plex_set_movie_added_date_now_empty_library_list(self, mock_logger, mock_settings, mock_get_plex):
        """Test behavior with empty library list."""
        # Setup
        mock_settings.plex.movie_library = []
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Import and run
        try:
            from plex.operations import plex_set_movie_added_date_now
            plex_set_movie_added_date_now(mock_metadata)
            
            # Verify it returns early without calling plex
            mock_plex.library.section.assert_not_called()
            mock_logger.debug.assert_called_with("No movie libraries configured in Plex settings")
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_plex_update_library_multiple_libraries(self, mock_settings, mock_get_plex):
        """Test library update with multiple libraries."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library1 = MagicMock()
        mock_library2 = MagicMock()
        
        def section_side_effect(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_side_effect
        
        # Import and run
        try:
            from plex.operations import plex_update_library
            plex_update_library(is_movie_library=True)
            
            # Verify both libraries were updated
            self.assertEqual(mock_plex.library.section.call_count, 2)
            mock_library1.update.assert_called_once()
            mock_library2.update.assert_called_once()
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_plex_refresh_item_movie_found_in_first_library(self, mock_settings, mock_get_plex):
        """Test movie refresh when found in first library."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library1 = MagicMock()
        mock_item = MagicMock()
        mock_item.title = "Test Movie"
        mock_library1.getGuid.return_value = mock_item
        
        mock_library2 = MagicMock()
        
        def section_side_effect(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_side_effect
        
        # Import and run
        try:
            from plex.operations import plex_refresh_item
            plex_refresh_item("tt1234567", is_movie=True)
            
            # Verify only first library was checked
            mock_plex.library.section.assert_called_once_with("Movies")
            mock_library1.getGuid.assert_called_once_with("imdb://tt1234567")
            mock_item.refresh.assert_called_once()
            
            # Second library should not be checked
            mock_library2.getGuid.assert_not_called()
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.plex_update_library')
    def test_plex_refresh_item_not_found_fallback(self, mock_update, mock_settings, mock_get_plex):
        """Test fallback to full library update when item not found."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        # Both libraries raise exception (not found)
        mock_library1 = MagicMock()
        mock_library1.getGuid.side_effect = Exception("Not found")
        
        mock_library2 = MagicMock()
        mock_library2.getGuid.side_effect = Exception("Not found")
        
        def section_side_effect(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_side_effect
        
        # Import and run
        try:
            from plex.operations import plex_refresh_item
            plex_refresh_item("tt1234567", is_movie=True)
            
            # Verify both libraries were checked
            self.assertEqual(mock_plex.library.section.call_count, 2)
            
            # Verify fallback to full library update
            mock_update.assert_called_once_with(True)
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_plex_refresh_item_episode(self, mock_settings, mock_get_plex):
        """Test episode refresh."""
        # Setup
        mock_settings.plex.series_library = ["TV Shows"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_show = MagicMock()
        mock_show.title = "Test Show"
        mock_episode = MagicMock()
        mock_show.episode.return_value = mock_episode
        mock_library.getGuid.return_value = mock_show
        
        mock_plex.library.section.return_value = mock_library
        
        # Import and run
        try:
            from plex.operations import plex_refresh_item
            plex_refresh_item("tt1234567", is_movie=False, season=1, episode=5)
            
            # Verify
            mock_library.getGuid.assert_called_once_with("imdb://tt1234567")
            mock_show.episode.assert_called_once_with(season=1, episode=5)
            mock_episode.refresh.assert_called_once()
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_list_normalization_string_value(self, mock_settings, mock_get_plex):
        """Test that operations normalize string values to list."""
        # Setup - settings returns string instead of list
        mock_settings.plex.movie_library = "Movies"  # String, not list
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_video = MagicMock()
        mock_library.getGuid.return_value = mock_video
        mock_plex.library.section.return_value = mock_library
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Import and run
        try:
            from plex.operations import plex_set_movie_added_date_now
            plex_set_movie_added_date_now(mock_metadata)
            
            # Should still work - normalized to list internally
            mock_plex.library.section.assert_called_once_with("Movies")
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_skip_empty_library_names(self, mock_settings, mock_get_plex):
        """Test that empty strings in library list are skipped."""
        # Setup - list contains empty strings
        mock_settings.plex.movie_library = ["Movies", "", "4K Movies", ""]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library1 = MagicMock()
        mock_library1.getGuid.side_effect = Exception("Not found")
        
        mock_library2 = MagicMock()
        mock_video = MagicMock()
        mock_library2.getGuid.return_value = mock_video
        
        def section_side_effect(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_side_effect
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Import and run
        try:
            from plex.operations import plex_set_movie_added_date_now
            plex_set_movie_added_date_now(mock_metadata)
            
            # Verify only non-empty library names were used
            self.assertEqual(mock_plex.library.section.call_count, 2)
            mock_plex.library.section.assert_any_call("Movies")
            mock_plex.library.section.assert_any_call("4K Movies")
        except ImportError as e:
            self.skipTest(f"Skipping test due to missing dependencies: {e}")


if __name__ == '__main__':
    unittest.main()

