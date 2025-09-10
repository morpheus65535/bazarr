# coding=utf-8

import logging
import requests
from urllib.parse import urlencode

from app.config import settings


def call_subtitle_webhook(subtitle_path, media_path, language, media_type):
    """
    Call configured webhook after subtitle download.
    Designed for Autopulse and similar services that need to trigger Plex metadata refresh.
    """
    if not settings.plex.use_subtitle_webhook or not settings.plex.subtitle_webhook_url:
        return

    try:
        url = settings.plex.subtitle_webhook_url.strip()
        username = settings.plex.subtitle_webhook_username.strip()
        password = settings.plex.subtitle_webhook_password.strip()
        
        if not url:
            return

        # Prepare webhook payload with path parameter (common for Autopulse)
        params = {'path': media_path}
        
        # Build full URL with query parameters
        webhook_url = f"{url}?{urlencode(params)}"
        
        # Setup authentication if provided
        auth = None
        if username and password:
            auth = (username, password)
        
        headers = {
            'User-Agent': 'Bazarr',
            'Content-Type': 'application/json'
        }
        
        logging.debug(f"BAZARR calling subtitle webhook: {url} for path: {media_path}")
        
        # Make the webhook call
        response = requests.get(
            webhook_url,
            auth=auth,
            headers=headers,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            logging.info(f"BAZARR webhook call successful for {media_path}")
        else:
            logging.warning(f"BAZARR webhook call failed with status {response.status_code} for {media_path}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"BAZARR webhook call failed for {media_path}: {str(e)}")
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling webhook for {media_path}: {str(e)}")
