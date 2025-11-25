# coding=utf-8

"""
Integration tests for Plex operations with multiselect support.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call


class TestPlexOperationsMultiselect:
    """Test Plex operations with multiple library support."""

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.update_added_date')
    def test_movie_added_date_single_library_success(self, mock_update, mock_settings, mock_get_plex):
        """Test setting movie added date with single library."""
        # Setup
        mock_settings.plex.movie_library = ["Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_video = MagicMock()
        mock_library.getGuid.return_value = mock_video
        mock_plex.library.section.return_value = mock_library
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Execute
        from plex.operations import plex_set_movie_added_date_now
        plex_set_movie_added_date_now(mock_metadata)
        
        # Verify
        mock_plex.library.section.assert_called_once_with("Movies")
        mock_library.getGuid.assert_called_once_with(guid="tt1234567")
        mock_update.assert_called_once()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.update_added_date')
    def test_movie_added_date_multiple_libraries_found_first(self, mock_update, mock_settings, mock_get_plex):
        """Test movie found in first of multiple libraries."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies", "Kids"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_video = MagicMock()
        mock_library.getGuid.return_value = mock_video
        mock_plex.library.section.return_value = mock_library
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Execute
        from plex.operations import plex_set_movie_added_date_now
        plex_set_movie_added_date_now(mock_metadata)
        
        # Verify - should only check first library
        mock_plex.library.section.assert_called_once_with("Movies")
        mock_update.assert_called_once()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.update_added_date')
    @patch('plex.operations.logger')
    def test_movie_added_date_multiple_libraries_found_second(self, mock_logger, mock_update, mock_settings, mock_get_plex):
        """Test movie found in second of multiple libraries."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        # First library - not found
        mock_library1 = MagicMock()
        mock_library1.getGuid.side_effect = Exception("Not found")
        
        # Second library - found
        mock_library2 = MagicMock()
        mock_video = MagicMock()
        mock_library2.getGuid.return_value = mock_video
        
        def section_mock(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_mock
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Execute
        from plex.operations import plex_set_movie_added_date_now
        plex_set_movie_added_date_now(mock_metadata)
        
        # Verify - checked both libraries
        assert mock_plex.library.section.call_count == 2
        calls = [call("Movies"), call("4K Movies")]
        mock_plex.library.section.assert_has_calls(calls)
        mock_update.assert_called_once()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.logger')
    def test_movie_added_date_not_found_any_library(self, mock_logger, mock_settings, mock_get_plex):
        """Test movie not found in any library."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_library.getGuid.side_effect = Exception("Not found")
        mock_plex.library.section.return_value = mock_library
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Execute
        from plex.operations import plex_set_movie_added_date_now
        plex_set_movie_added_date_now(mock_metadata)
        
        # Verify - checked all libraries and logged warning
        assert mock_plex.library.section.call_count == 2
        mock_logger.warning.assert_called()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.logger')
    def test_movie_added_date_empty_library_list(self, mock_logger, mock_settings, mock_get_plex):
        """Test with empty library list."""
        # Setup
        mock_settings.plex.movie_library = []
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_metadata = Mock()
        mock_metadata.imdbId = "tt1234567"
        
        # Execute
        from plex.operations import plex_set_movie_added_date_now
        plex_set_movie_added_date_now(mock_metadata)
        
        # Verify - returns early, no Plex calls
        mock_plex.library.section.assert_not_called()
        mock_logger.debug.assert_called_with("No movie libraries configured in Plex settings")

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_update_library_multiple_success(self, mock_settings, mock_get_plex):
        """Test updating multiple libraries."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library1 = MagicMock()
        mock_library2 = MagicMock()
        
        def section_mock(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_mock
        
        # Execute
        from plex.operations import plex_update_library
        plex_update_library(is_movie_library=True)
        
        # Verify - both libraries updated
        assert mock_plex.library.section.call_count == 2
        mock_library1.update.assert_called_once()
        mock_library2.update.assert_called_once()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    @patch('plex.operations.logger')
    def test_update_library_one_fails(self, mock_logger, mock_settings, mock_get_plex):
        """Test updating libraries when one fails."""
        # Setup
        mock_settings.plex.series_library = ["TV Shows", "Anime"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library1 = MagicMock()
        mock_library1.update.side_effect = Exception("Update failed")
        
        mock_library2 = MagicMock()
        
        def section_mock(name):
            if name == "TV Shows":
                return mock_library1
            elif name == "Anime":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_mock
        
        # Execute
        from plex.operations import plex_update_library
        plex_update_library(is_movie_library=False)
        
        # Verify - second library still updated despite first failure
        assert mock_plex.library.section.call_count == 2
        mock_library2.update.assert_called_once()
        mock_logger.error.assert_called()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_refresh_item_movie_success(self, mock_settings, mock_get_plex):
        """Test refreshing a movie item."""
        # Setup
        mock_settings.plex.movie_library = ["Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_item = MagicMock()
        mock_item.title = "Test Movie"
        mock_library.getGuid.return_value = mock_item
        mock_plex.library.section.return_value = mock_library
        
        # Execute
        from plex.operations import plex_refresh_item
        plex_refresh_item("tt1234567", is_movie=True)
        
        # Verify
        mock_library.getGuid.assert_called_once_with("imdb://tt1234567")
        mock_item.refresh.assert_called_once()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_refresh_item_episode_success(self, mock_settings, mock_get_plex):
        """Test refreshing an episode item."""
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
        
        # Execute
        from plex.operations import plex_refresh_item
        plex_refresh_item("tt1234567", is_movie=False, season=2, episode=5)
        
        # Verify
        mock_library.getGuid.assert_called_once_with("imdb://tt1234567")
        mock_show.episode.assert_called_once_with(season=2, episode=5)
        mock_episode.refresh.assert_called_once()

    @patch('plex.operations.plex_update_library')
    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_refresh_item_not_found_fallback(self, mock_settings, mock_get_plex, mock_update):
        """Test fallback to full update when item not found."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "4K Movies"]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_library.getGuid.side_effect = Exception("Not found")
        mock_plex.library.section.return_value = mock_library
        
        # Execute
        from plex.operations import plex_refresh_item
        plex_refresh_item("tt1234567", is_movie=True)
        
        # Verify - fallback called
        assert mock_plex.library.section.call_count == 2  # Checked both libraries
        mock_update.assert_called_once_with(True)

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_handles_string_value_backward_compatibility(self, mock_settings, mock_get_plex):
        """Test backward compatibility when settings returns string."""
        # Setup - simulate old config format
        mock_settings.plex.movie_library = "Movies"  # String instead of list
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library = MagicMock()
        mock_plex.library.section.return_value = mock_library
        
        # Execute
        from plex.operations import plex_update_library
        plex_update_library(is_movie_library=True)
        
        # Verify - still works
        mock_plex.library.section.assert_called_once_with("Movies")
        mock_library.update.assert_called_once()

    @patch('plex.operations.get_plex_server')
    @patch('plex.operations.settings')
    def test_filters_empty_library_names(self, mock_settings, mock_get_plex):
        """Test that empty strings in library list are filtered out."""
        # Setup
        mock_settings.plex.movie_library = ["Movies", "", "4K Movies", ""]
        mock_plex = MagicMock()
        mock_get_plex.return_value = mock_plex
        
        mock_library1 = MagicMock()
        mock_library2 = MagicMock()
        
        def section_mock(name):
            if name == "Movies":
                return mock_library1
            elif name == "4K Movies":
                return mock_library2
        
        mock_plex.library.section.side_effect = section_mock
        
        # Execute
        from plex.operations import plex_update_library
        plex_update_library(is_movie_library=True)
        
        # Verify - only non-empty names used
        assert mock_plex.library.section.call_count == 2
        calls = [call("Movies"), call("4K Movies")]
        mock_plex.library.section.assert_has_calls(calls)
        # Verify both libraries were updated
        mock_library1.update.assert_called_once()
        mock_library2.update.assert_called_once()
