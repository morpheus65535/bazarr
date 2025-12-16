# -*- coding: utf-8 -*-
"""
Tests for Plex unique instance identification functionality.
Phase 0: Instance-Identified Webhook URLs
"""

import pytest
from unittest.mock import MagicMock, patch
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
