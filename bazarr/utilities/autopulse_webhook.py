# coding=utf-8

import logging
import os
import requests
from urllib.parse import urlencode

from app.config import settings


def call_autopulse_webhook(subtitle_path, media_path, language, media_type):
    """
    Call external webhook after subtitle download.
    Supports both generic webhooks and Autopulse auto-configuration.
    """
    # Check if any external webhook is enabled
    if not settings.general.use_external_webhook and not settings.plex.use_autopulse:
        return

    try:
        # Use parent directory instead of specific file for better grouping
        parent_dir = os.path.dirname(media_path)
        
        # Get webhook configuration
        webhook_url = _get_webhook_url()
        auth = _get_webhook_auth()
        
        if not webhook_url:
            logging.debug("BAZARR external webhook not configured, skipping")
            return

        # Prepare query parameters
        params = {'path': parent_dir}
        full_url = f"{webhook_url}?{urlencode(params)}"
        
        headers = {'User-Agent': 'Bazarr'}
        
        logging.debug(f"BAZARR calling external webhook: {webhook_url} for path: {parent_dir}")
        
        # Make the webhook call
        response = requests.get(
            full_url,
            auth=auth,
            headers=headers,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            logging.info(f"BAZARR external webhook successful for {parent_dir}")
        else:
            logging.warning(f"BAZARR external webhook failed with status {response.status_code} for {parent_dir}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"BAZARR external webhook failed for {media_path}: {str(e)}")
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling external webhook for {media_path}: {str(e)}")


def test_autopulse_connection():
    """
    Test connection to external webhook.
    Returns (success: bool, message: str)
    """
    try:
        webhook_url = _get_webhook_url()
        auth = _get_webhook_auth()
        
        if not webhook_url:
            return False, "External webhook not configured"

        # Test with stats endpoint if it looks like Autopulse, otherwise test the main URL
        test_url = webhook_url
        if '/triggers/manual' in webhook_url:
            # For Autopulse, test the stats endpoint instead
            base_url = webhook_url.replace('/triggers/manual', '')
            test_url = f"{base_url}/stats"
        
        headers = {'User-Agent': 'Bazarr'}
        
        logging.debug(f"BAZARR testing external webhook: {test_url}")
        
        response = requests.get(
            test_url,
            auth=auth,
            headers=headers,
            timeout=10,
            verify=True
        )
        
        if response.status_code == 200:
            return True, "External webhook connection successful"
        else:
            return False, f"External webhook connection failed with status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return False, f"External webhook connection failed: {str(e)}"
    except Exception as e:
        return False, f"External webhook connection error: {str(e)}"


def get_plex_config_for_autopulse():
    """
    Get Plex configuration for Autopulse auto-configuration.
    Only used when Plex OAuth is available.
    Returns dict with config data or None if failed.
    """
    try:
        # Get the current Plex configuration from Bazarr's settings
        server_url = settings.plex.get('server_url', '')
        server_name = settings.plex.get('server_name', '')
        username = settings.plex.get('username', '')
        auth_method = settings.plex.get('auth_method', 'apikey')
        
        # Only proceed if OAuth is configured
        if auth_method != 'oauth':
            return None
            
        # Get the decrypted token
        key_existed = bool(getattr(settings.plex, 'encryption_key', None))
        if not key_existed:
            logging.warning("BAZARR no encryption key available for Plex config")
            return None
            
        encrypted_token = settings.plex.get('token')
        if not encrypted_token:
            logging.warning("BAZARR no encrypted token available for Plex config")
            return None
        
        # Decrypt the token
        try:
            from api.plex.security import get_or_create_encryption_key, TokenManager
            key = get_or_create_encryption_key(settings.plex, 'encryption_key')
            token_manager = TokenManager(key)
            decrypted_token = token_manager.decrypt(encrypted_token)
        except Exception as e:
            logging.error(f"BAZARR token decryption failed: {e}")
            return None
        
        if not decrypted_token or not server_url:
            logging.warning("BAZARR missing required Plex configuration")
            return None
        
        # Return simplified configuration data
        config_data = {
            'plex_url': server_url,
            'plex_token': decrypted_token,
            'server_name': server_name,
            'username': username,
            'auth_method': auth_method,
        }
        
        logging.info(f"BAZARR generated Plex config for Autopulse: {server_name}")
        return config_data
            
    except Exception as e:
        logging.error(f"BAZARR error generating Plex config: {str(e)}")
        return None


def _get_webhook_url():
    """Get the webhook URL (either manual or auto-generated for Autopulse)."""
    # Check if using Autopulse auto-configuration
    if settings.plex.use_autopulse:
        host = settings.plex.autopulse_host.strip()
        port = settings.plex.autopulse_port
        
        if host:
            return f"http://{host}:{port}/triggers/manual"
    
    # Check if using generic external webhook
    if settings.general.use_external_webhook:
        webhook_url = settings.general.external_webhook_url.strip()
        if webhook_url:
            return webhook_url
    
    return None


def _get_webhook_auth():
    """Get authentication for the webhook."""
    # Check if using Autopulse auto-configuration
    if settings.plex.use_autopulse:
        username = settings.plex.autopulse_username.strip()
        password = settings.plex.autopulse_password.strip()
        
        if username and password:
            return (username, password)
    
    # Check if using generic external webhook
    if settings.general.use_external_webhook:
        username = settings.general.external_webhook_username.strip()
        password = settings.general.external_webhook_password.strip()
        
        if username and password:
            return (username, password)
    
    return None
