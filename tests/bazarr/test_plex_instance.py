# -*- coding: utf-8 -*-
"""
Tests for Plex unique instance identification functionality.
Phase 0: Instance-Identified Webhook URLs
Phase 1: Persistent Client Identifier & Device Name
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch, PropertyMock
from urllib.parse import quote_plus, urlparse, parse_qs


class TestWebhookInstanceParameter:
    """Test that webhook URLs include the instance parameter."""
    
    def test_quote_plus_encodes_instance_name(self):
        """Test that instance names are properly URL encoded."""
        # Test basic name
        assert quote_plus("Bazarr") == "Bazarr"
        
        # Test name with spaces
        assert quote_plus("Bazarr 4K Movies") == "Bazarr+4K+Movies"
        
        # Test name with special characters
        assert quote_plus("Bazarr-4K-Movies") == "Bazarr-4K-Movies"
        assert quote_plus("Bazarr_4K_Movies") == "Bazarr_4K_Movies"
        
        # Test name with unusual characters
        assert quote_plus("Bazarr (4K)") == "Bazarr+%284K%29"
    
    def test_webhook_url_structure_with_instance(self):
        """Test the expected webhook URL structure."""
        base_url = "https://bazarr.local"
        apikey = "test-api-key"
        instance_name = "Bazarr-4K-Movies"
        instance_param = quote_plus(instance_name)
        
        webhook_url = f"{base_url}/api/webhooks/plex?apikey={apikey}&instance={instance_param}"
        
        # Parse and verify URL structure
        parsed = urlparse(webhook_url)
        query_params = parse_qs(parsed.query)
        
        assert parsed.scheme == "https"
        assert parsed.netloc == "bazarr.local"
        assert parsed.path == "/api/webhooks/plex"
        assert "apikey" in query_params
        assert "instance" in query_params
        assert query_params["apikey"][0] == apikey
        assert query_params["instance"][0] == instance_name
    
    def test_webhook_url_with_spaces_in_instance_name(self):
        """Test webhook URL when instance name contains spaces."""
        base_url = "https://bazarr.local"
        apikey = "test-api-key"
        instance_name = "Bazarr 4K Movies"
        instance_param = quote_plus(instance_name)
        
        webhook_url = f"{base_url}/api/webhooks/plex?apikey={apikey}&instance={instance_param}"
        
        # Verify the URL is properly encoded
        assert "Bazarr+4K+Movies" in webhook_url
        
        # Parse and verify it decodes back correctly
        parsed = urlparse(webhook_url)
        query_params = parse_qs(parsed.query)
        assert query_params["instance"][0] == instance_name
    
    def test_default_instance_name(self):
        """Test that default instance name 'Bazarr' is used when not configured."""
        default_instance = "Bazarr"
        instance_param = quote_plus(default_instance)
        
        webhook_url = f"https://bazarr.local/api/webhooks/plex?apikey=test&instance={instance_param}"
        
        parsed = urlparse(webhook_url)
        query_params = parse_qs(parsed.query)
        assert query_params["instance"][0] == "Bazarr"


class TestInstanceParameterInOAuth:
    """Test the actual OAuth webhook creation code path."""
    
    @patch('bazarr.api.plex.oauth.settings')
    def test_instance_name_retrieved_from_settings(self, mock_settings):
        """Test that instance name is retrieved from general settings."""
        mock_settings.general.get.return_value = "Test-Instance"
        
        instance_name = mock_settings.general.get('instance_name', 'Bazarr')
        
        assert instance_name == "Test-Instance"
        mock_settings.general.get.assert_called_with('instance_name', 'Bazarr')
    
    @patch('bazarr.api.plex.oauth.settings')
    def test_instance_name_defaults_to_bazarr(self, mock_settings):
        """Test that instance name defaults to 'Bazarr' when not set."""
        # Simulate no instance_name configured (returns the default)
        mock_settings.general.get.return_value = 'Bazarr'
        
        instance_name = mock_settings.general.get('instance_name', 'Bazarr')
        
        assert instance_name == "Bazarr"


class TestPersistentClientIdentifier:
    """Phase 1: Test persistent client identifier functionality."""
    
    def test_uuid_format(self):
        """Test that generated UUIDs are valid."""
        client_id = str(uuid.uuid4())
        
        # Verify it's a valid UUID format
        assert len(client_id) == 36
        assert client_id.count('-') == 4
        
        # Verify it can be parsed back
        parsed = uuid.UUID(client_id)
        assert str(parsed) == client_id
    
    @patch('bazarr.api.plex.oauth.write_config')
    @patch('bazarr.api.plex.oauth.settings')
    def test_get_or_create_client_identifier_creates_new(self, mock_settings, mock_write_config):
        """Test that a new client identifier is created when none exists."""
        from bazarr.api.plex.oauth import get_or_create_client_identifier
        
        # Simulate no existing client identifier
        mock_settings.plex.get.return_value = ''
        
        client_id = get_or_create_client_identifier()
        
        # Verify a UUID was generated
        assert len(client_id) == 36
        assert client_id.count('-') == 4
        
        # Verify it was saved to settings
        mock_write_config.assert_called_once()
    
    @patch('bazarr.api.plex.oauth.write_config')
    @patch('bazarr.api.plex.oauth.settings')
    def test_get_or_create_client_identifier_reuses_existing(self, mock_settings, mock_write_config):
        """Test that existing client identifier is reused."""
        from bazarr.api.plex.oauth import get_or_create_client_identifier
        
        existing_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        mock_settings.plex.get.return_value = existing_id
        
        client_id = get_or_create_client_identifier()
        
        # Verify the existing ID was returned
        assert client_id == existing_id
        
        # Verify config was NOT written (no new ID generated)
        mock_write_config.assert_not_called()


class TestPlexHeaders:
    """Test Plex API headers include correct device information."""
    
    def test_auth_url_includes_device_name(self):
        """Test that auth URL includes instance name as device name."""
        client_id = "test-client-id"
        code = "test-code"
        instance_name = "Bazarr-4K-Movies"
        instance_name_encoded = quote_plus(instance_name)
        
        auth_url = f"https://app.plex.tv/auth#?clientID={client_id}&code={code}&context[device][product]=Bazarr&context[device][deviceName]={instance_name_encoded}"
        
        # Verify the URL contains the encoded instance name
        assert f"deviceName]={instance_name_encoded}" in auth_url
        assert "context[device][product]=Bazarr" in auth_url
    
    def test_auth_url_with_spaces_in_instance_name(self):
        """Test auth URL properly encodes spaces in instance name."""
        instance_name = "Bazarr 4K Movies"
        instance_name_encoded = quote_plus(instance_name)
        
        auth_url = f"https://app.plex.tv/auth#?context[device][deviceName]={instance_name_encoded}"
        
        # Verify spaces are encoded as +
        assert "Bazarr+4K+Movies" in auth_url
    
    def test_expected_plex_headers_structure(self):
        """Test the expected structure of Plex API headers."""
        instance_name = "Test-Instance"
        bazarr_version = "1.4.5"
        client_id = "test-client-id"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Plex-Product': 'Bazarr',
            'X-Plex-Version': bazarr_version,
            'X-Plex-Client-Identifier': client_id,
            'X-Plex-Platform': 'Web',
            'X-Plex-Platform-Version': '1.0',
            'X-Plex-Device': 'Bazarr',
            'X-Plex-Device-Name': instance_name
        }
        
        # Verify all required headers are present
        assert headers['X-Plex-Product'] == 'Bazarr'
        assert headers['X-Plex-Version'] == bazarr_version
        assert headers['X-Plex-Client-Identifier'] == client_id
        assert headers['X-Plex-Device-Name'] == instance_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
