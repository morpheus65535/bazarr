# coding=utf-8

import logging
import requests
from urllib.parse import urlencode

from app.config import settings


def call_subtitle_webhook(subtitle_path, media_path, language, media_type):
    """
    Call Autopulse after subtitle download to trigger Plex metadata refresh.
    Uses Autopulse's automatic /triggers/manual endpoint.
    """
    # Check if Autopulse is enabled
    if not settings.plex.use_autopulse or not settings.plex.autopulse_host:
        return

    try:
        host = settings.plex.autopulse_host.strip()
        port = settings.plex.autopulse_port
        username = settings.plex.autopulse_username.strip()
        password = settings.plex.autopulse_password.strip()
        
        if not host:
            return

        # Build Autopulse manual trigger URL
        autopulse_url = f"http://{host}:{port}/triggers/manual"
        
        # Prepare query parameters for Autopulse
        params = {'path': media_path}
        
        # Build full URL with query parameters
        webhook_url = f"{autopulse_url}?{urlencode(params)}"
        
        # Setup authentication if provided
        auth = None
        if username and password:
            auth = (username, password)
        
        headers = {
            'User-Agent': 'Bazarr',
        }
        
        logging.debug(f"BAZARR calling Autopulse: {autopulse_url} for path: {media_path}")
        
        # Make the webhook call to Autopulse
        response = requests.get(
            webhook_url,
            auth=auth,
            headers=headers,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            logging.info(f"BAZARR Autopulse call successful for {media_path}")
        else:
            logging.warning(f"BAZARR Autopulse call failed with status {response.status_code} for {media_path}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"BAZARR Autopulse call failed for {media_path}: {str(e)}")
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling Autopulse for {media_path}: {str(e)}")


def test_autopulse_connection():
    """
    Test connection to Autopulse server.
    Returns (success: bool, message: str)
    """
    try:
        host = settings.plex.autopulse_host.strip()
        port = settings.plex.autopulse_port
        username = settings.plex.autopulse_username.strip()
        password = settings.plex.autopulse_password.strip()
        
        if not host:
            return False, "Autopulse host not configured"

        # Build Autopulse status URL
        status_url = f"http://{host}:{port}/status"
        
        # Setup authentication if provided
        auth = None
        if username and password:
            auth = (username, password)
        
        headers = {
            'User-Agent': 'Bazarr',
        }
        
        logging.debug(f"BAZARR testing Autopulse connection: {status_url}")
        
        # Test connection to Autopulse
        response = requests.get(
            status_url,
            auth=auth,
            headers=headers,
            timeout=10,
            verify=True
        )
        
        if response.status_code == 200:
            return True, "Autopulse connection successful"
        else:
            return False, f"Autopulse connection failed with status {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Autopulse connection failed: {str(e)}"
    except Exception as e:
        return False, f"Autopulse connection error: {str(e)}"
