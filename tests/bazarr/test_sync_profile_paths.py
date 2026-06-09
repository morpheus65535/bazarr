# coding=utf-8
import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from pathlib import Path
import logging

logging.disable(logging.CRITICAL)

from tests.test_helpers import load_isolated_module


def _load_radarr_utils():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "bazarr" / "radarr" / "sync" / "utils.py"
    return load_isolated_module(
        "radarr.sync.utils",
        module_path,
        ["app", "radarr", "constants"],
        {
            "app.config": SimpleNamespace(settings=SimpleNamespace(radarr=SimpleNamespace(apikey="test", http_timeout=30))),
            "radarr.info": SimpleNamespace(
                get_radarr_info=MagicMock(is_legacy=MagicMock(return_value=True)),
                url_api_radarr=MagicMock(return_value="http://localhost:7878/api/v3/")
            ),
            "constants": SimpleNamespace(HEADERS={}),
        },
    )


def _load_sonarr_utils():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "bazarr" / "sonarr" / "sync" / "utils.py"
    return load_isolated_module(
        "sonarr.sync.utils",
        module_path,
        ["app", "sonarr", "constants"],
        {
            "app.config": SimpleNamespace(settings=SimpleNamespace(sonarr=SimpleNamespace(apikey="test", http_timeout=30))),
            "sonarr.info": SimpleNamespace(
                get_sonarr_info=MagicMock(version=MagicMock(return_value="4.0.0")),
                url_api_sonarr=MagicMock(return_value="http://localhost:8989/api/v3/")
            ),
            "constants": SimpleNamespace(HEADERS={}),
        },
    )


class TestRadarrProfileParsingProperties:
    """Property tests for radarr profile parsing with malformed API responses"""

    def test_profile_language_is_none_filtered(self):
        """Fuzz: Radarr profile['language'] is None is filtered out gracefully"""
        radarr_utils = _load_radarr_utils()
        
        # Mock the API response with None language
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'id': 1, 'language': None},  # Filtered: not a string
                {'id': 2, 'language': 'English'},  # Valid
            ]
            mock_get.return_value = mock_response
            
            result = radarr_utils.get_profile_list()
            # Should only include the valid profile
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == [2, 'English']

    def test_profile_language_not_string_filtered(self):
        """Fuzz: Radarr profile['language'] is int is filtered out gracefully"""
        radarr_utils = _load_radarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'id': 1, 'language': 123},  # Filtered: not a string
                {'id': 2, 'language': 'French'},  # Valid
            ]
            mock_get.return_value = mock_response
            
            result = radarr_utils.get_profile_list()
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == [2, 'French']

    def test_profile_nested_language_name_none_filtered(self):
        """Fuzz: Radarr profile['language']['name'] is None is filtered (v4)"""
        radarr_utils = _load_radarr_utils()
        
        with patch('requests.get') as mock_get:
            with patch.object(radarr_utils.get_radarr_info, 'is_legacy', return_value=False):
                mock_response = MagicMock()
                mock_response.json.return_value = [
                    {'id': 1, 'language': {'name': None}},  # Filtered: name not a string
                    {'id': 2, 'language': {'name': 'Spanish'}},  # Valid
                ]
                mock_get.return_value = mock_response
                
                result = radarr_utils.get_profile_list()
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0] == [2, 'Spanish']

    def test_profile_missing_id_key_crashes_hard(self):
        """Fuzz: Radarr profile missing 'id' key still crashes (by design)"""
        radarr_utils = _load_radarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'language': 'English'},  # Missing 'id' — still crashes
            ]
            mock_get.return_value = mock_response
            
            # This is expected to crash — id is required for the profile list structure
            with pytest.raises(KeyError):
                radarr_utils.get_profile_list()


class TestSonarrProfileParsingProperties:
    """Property tests for sonarr profile parsing with malformed API responses"""

    def test_sonarr_profile_language_is_none_filtered(self):
        """Fuzz: Sonarr profile['language'] is None is filtered gracefully"""
        sonarr_utils = _load_sonarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'id': 1, 'language': None},  # Filtered: not a string
                {'id': 2, 'language': 'German'},  # Valid
            ]
            mock_get.return_value = mock_response
            
            with patch.object(sonarr_utils.get_sonarr_info, 'is_legacy', return_value=True):
                result = sonarr_utils.get_profile_list()
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0] == [2, 'German']

    def test_sonarr_profile_name_is_none_filtered(self):
        """Fuzz: Sonarr profile['name'] is None is filtered (v3 path)"""
        sonarr_utils = _load_sonarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'id': 1, 'name': None},  # Filtered: not a string
                {'id': 2, 'name': 'Profile1'},  # Valid
            ]
            mock_get.return_value = mock_response
            
            # Must use version 3.x to reach the profile parsing code
            with patch.object(sonarr_utils.get_sonarr_info, 'version', return_value='3.0.0'):
                with patch.object(sonarr_utils.get_sonarr_info, 'is_legacy', return_value=False):
                    result = sonarr_utils.get_profile_list()
                    assert isinstance(result, list)
                    assert len(result) == 1
                    assert result[0] == [2, 'Profile1']

    def test_sonarr_profile_language_not_string_filtered(self):
        """Fuzz: Sonarr profile['language'] is int is filtered (v3 legacy)"""
        sonarr_utils = _load_sonarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'id': 1, 'language': 123},  # Filtered: not a string
                {'id': 2, 'language': 'Italian'},  # Valid
            ]
            mock_get.return_value = mock_response
            
            with patch.object(sonarr_utils.get_sonarr_info, 'is_legacy', return_value=True):
                result = sonarr_utils.get_profile_list()
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0] == [2, 'Italian']

    def test_sonarr_empty_profiles_response(self):
        """Fuzz: Sonarr returns empty profile list"""
        sonarr_utils = _load_sonarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            with patch.object(sonarr_utils.get_sonarr_info, 'is_legacy', return_value=True):
                result = sonarr_utils.get_profile_list()
                assert result == []

    def test_sonarr_all_profiles_malformed_returns_empty(self):
        """Fuzz: Sonarr all profiles malformed returns empty list safely"""
        sonarr_utils = _load_sonarr_utils()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'id': 1, 'name': 123},  # int, not string
                {'id': 2, 'name': []},  # list, not string
                {'id': 3},  # Missing 'name'
            ]
            mock_get.return_value = mock_response
            
            with patch.object(sonarr_utils.get_sonarr_info, 'is_legacy', return_value=False):
                result = sonarr_utils.get_profile_list()
                # All profiles filtered, returns empty
                assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

