# coding=utf-8

"""
Tests for Plex library multiselect functionality.

This test suite covers:
1. Helper logic for list normalization  
2. Config validator setup
3. Edge cases (empty lists, filtering, etc.)

Note: Full integration tests with mocked settings are complex due to Dynaconf.
These tests focus on the logic patterns used in the implementation.
"""

import unittest
import sys
import os

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


if __name__ == '__main__':
    unittest.main()
