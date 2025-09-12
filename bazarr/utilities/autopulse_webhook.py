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
    if not settings.general.use_autopulse:
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
        
        logging.debug(f"BAZARR webhook test - URL: {webhook_url}")
        logging.debug(f"BAZARR webhook test - Auth: {auth is not None}")
        
        if not webhook_url:
            logging.debug("BAZARR webhook test - No URL configured")
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


def _get_webhook_url():
    """Get the webhook URL from General webhook configuration only."""
    # Check if using generic external webhook
    if settings.general.use_autopulse:
        webhook_url = settings.general.autopulse_url.strip()
        if webhook_url:
            return webhook_url
    
    return None


def _get_webhook_auth():
    """Get authentication for the General webhook only."""
    # Check if using generic external webhook
    if settings.general.use_autopulse:
        username = settings.general.autopulse_username.strip()
        password = settings.general.autopulse_password.strip()
        
        if username and password:
            return (username, password)
    
    return None
