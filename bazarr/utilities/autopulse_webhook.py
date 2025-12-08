# coding=utf-8

import logging
import os
import requests
from urllib.parse import urlencode
from retry.api import retry

from app.config import settings


def generate_autopulse_config(decrypted_token=None):
    """
    Generate complete Autopulse configuration for Plex integration by requesting
    a configuration template from Autopulse and adding Plex-specific details.
    
    This function uses the new Autopulse /api/config-template endpoint with the
    'bazarr' trigger type for improved integration. The response contains a 
    complete configuration with placeholders that are replaced with actual values.
    """
    try:
        # Get Plex configuration - OAuth required for this feature
        server_url = settings.plex.get('server_url', '')
        server_name = settings.plex.get('server_name', '')
        auth_method = settings.plex.get('auth_method', 'apikey')
        
        # Only proceed if OAuth is configured
        if auth_method != 'oauth':
            return None
            
        # Use provided token or get decrypted token from OAuth system
        if not decrypted_token:
            from api.plex.oauth import get_decrypted_token
            decrypted_token = get_decrypted_token()
            
        if not decrypted_token or not server_url:
            logging.warning("BAZARR missing required Plex OAuth configuration for Autopulse")
            return None
        
        # Get configuration template from Autopulse (required)
        autopulse_template = _get_autopulse_template()
        
        if not autopulse_template:
            logging.error("BAZARR Autopulse template API unavailable - please ensure Autopulse is running and supports the template API")
            return None
        
        # Generate Plex-specific configuration using template
        logging.info("BAZARR using dynamic Autopulse template for config generation")
        return _generate_config_from_template(autopulse_template, server_url, decrypted_token, server_name)
            
    except Exception as e:
        logging.error(f"BAZARR error generating Autopulse config: {str(e)}")
        return None


def _get_autopulse_template():
    """
    Request configuration template from Autopulse API.
    Returns None if the API call fails or Autopulse is not available.
    """
    try:
        # Get Autopulse URL from external webhook settings
        autopulse_url = _get_autopulse_template_url()
        if not autopulse_url:
            logging.debug("BAZARR no Autopulse URL configured, skipping template request")
            return None
        
        # Get authentication for Autopulse
        auth = _get_webhook_auth()
        
        # Request configuration template using new API parameters
        headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", 'Bazarr')}
        params = {
            'triggers': 'bazarr',  # Use the dedicated Bazarr trigger type
            'targets': 'plex',     # Configure for Plex target
            'database': 'sqlite'   # Default to SQLite database
        }
        
        logging.debug(f"BAZARR requesting Autopulse template from: {autopulse_url}")
        
        response = _make_autopulse_request(
            autopulse_url,
            params=params,
            auth=auth,
            headers=headers
        )
        
        if response.status_code == 200:
            template_data = response.json()
            logging.debug("BAZARR received Autopulse configuration template")
            return template_data
        elif response.status_code == 401:
            logging.warning(f"BAZARR Autopulse template API authentication failed (401). Check your credentials. Did you forget to save your settings?")
            return None
        elif response.status_code == 400:
            logging.warning(f"BAZARR Autopulse template API bad request (400). Check your webhook URL and credentials. Did you forget to save your settings?")
            return None
        else:
            logging.warning(f"BAZARR Autopulse template API failed with status {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.debug(f"BAZARR Autopulse template API request failed: {str(e)}. Did you forget to save your external webhook settings?")
        return None
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling Autopulse template API: {str(e)}")
        return None


def _get_autopulse_template_url():
    """Get the Autopulse template API URL."""
    webhook_url = _get_webhook_url()
    if not webhook_url:
        return None
    
    # Convert webhook URL to template API URL
    # From: http://autopulse:2875/triggers/bazarr
    # To: http://autopulse:2875/api/config-template
    try:
        if '/triggers/' in webhook_url:
            # Remove the trigger path and replace with API path
            base_url = webhook_url.split('/triggers/')[0]
            return f"{base_url}/api/config-template"
        else:
            # Assume base URL and append API path
            base_url = webhook_url.rstrip('/')
            return f"{base_url}/api/config-template"
    except Exception:
        return None


def _generate_config_from_template(template_data, server_url, decrypted_token, server_name):
    """
    Generate configuration by replacing placeholders in the Autopulse template with Plex-specific details.
    """
    try:
        # Get the base configuration from template response
        base_config = template_data.get('config', '')
        template_version = template_data.get('version', 'unknown')
        
        if not base_config:
            logging.error("BAZARR Autopulse template response missing config field")
            return None
        
        # Replace placeholders with actual values
        config_with_values = base_config.replace('{url}', server_url)
        config_with_values = config_with_values.replace('{token}', decrypted_token)
        
        # Get webhook authentication and replace auth placeholders
        auth = _get_webhook_auth()
        if auth:
            username, password = auth
            config_with_values = config_with_values.replace('{username}', username)
            config_with_values = config_with_values.replace('{password}', password)
        else:
            # Replace with empty strings if no auth configured
            config_with_values = config_with_values.replace('{username}', '')
            config_with_values = config_with_values.replace('{password}', '')
        
        # Override Autopulse defaults with Bazarr-optimized values
        config_with_values = config_with_values.replace('refresh = false', 'refresh = true')
        config_with_values = config_with_values.replace('analyze = true', 'analyze = false')
        
        # Detect path rewriting needs
        rewrite_config = _detect_path_rewrite()
        
        # Add path rewriting to configuration if detected
        if rewrite_config['detected']:
            config_with_values = _inject_rewrite_config(config_with_values, rewrite_config)
        
        # Add header comment with metadata
        rewrite_status = "Path rewriting: Enabled" if rewrite_config['detected'] else "Path rewriting: Not detected"
        full_config = f"""# Autopulse Configuration - Generated using dynamic template
# Server: {server_name}
# Template version: {template_version}
# Generated with Bazarr trigger type
# {rewrite_status}

{config_with_values}

# Usage: Bazarr calls GET http://autopulse:2875/triggers/bazarr?path=/parent/directory
"""
        
        # Separate template info from rewrite suggestions
        template_info = f"Configuration generated using Autopulse template v{template_version}"
        path_suggestion = rewrite_config['suggestion'] if rewrite_config['suggestion'] else None
        
        return {
            'config_yaml': full_config,
            'server_name': server_name,
            'rewrite_detected': rewrite_config['detected'],
            'rewrite_suggestion': path_suggestion,
            'template_info': template_info
        }
        
    except Exception as e:
        logging.error(f"BAZARR error generating config from template: {str(e)}")
        return None


def call_external_webhook(subtitle_path, media_path, language, media_type):
    """
    Call external webhook after subtitle download.
    Supports generic webhooks and Autopulse integration.
    """
    # Check if external webhook is enabled
    if not settings.general.use_external_webhook:
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
        
        headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", 'Bazarr')}
        
        logging.debug(f"BAZARR calling external webhook: {webhook_url} for path: {parent_dir}")
        
        # Make the webhook call with retry for network issues
        response = _make_webhook_request(full_url, auth, headers)
        
        if response.status_code == 200:
            logging.info(f"BAZARR external webhook successful for {parent_dir}")
        elif response.status_code == 401:
            logging.warning(f"BAZARR external webhook authentication failed (401) for {parent_dir}. Did you forget to save your external webhook settings?")
        elif response.status_code == 400:
            logging.warning(f"BAZARR external webhook bad request (400) for {parent_dir}. Check your webhook URL and credentials. Did you forget to save your external webhook settings?")
        else:
            logging.warning(f"BAZARR external webhook failed with status {response.status_code} for {parent_dir}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"BAZARR external webhook failed for {media_path}: {str(e)}. Did you forget to save your external webhook settings?")
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling external webhook for {media_path}: {str(e)}")


@retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=1, backoff=2, jitter=(0, 1))
def _make_webhook_request(url, auth, headers):
    """Make webhook request with retry logic for network issues."""
    return requests.get(
        url,
        auth=auth,
        headers=headers,
        timeout=30,
        verify=True
    )


@retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=1, backoff=2, jitter=(0, 1))
def _make_autopulse_request(url, params=None, auth=None, headers=None):
    """Make Autopulse API request with retry logic for network issues."""
    return requests.get(
        url,
        params=params,
        auth=auth,
        headers=headers,
        timeout=10,
        verify=True
    )


def test_external_webhook_connection():
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
            return False, "External webhook not configured. Please enter a webhook URL and save your settings."

        # Test with stats endpoint if it looks like Autopulse, otherwise test the main URL
        test_url = webhook_url
        if '/triggers/' in webhook_url:
            # For Autopulse, test the stats endpoint instead
            base_url = webhook_url.split('/triggers/')[0]
            test_url = f"{base_url}/stats"
        
        headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", 'Bazarr')}
        
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
        elif response.status_code == 401:
            return False, "External webhook authentication failed (401). Check your username and password."
        elif response.status_code == 400:
            return False, "External webhook bad request (400). Check your webhook URL and credentials."
        else:
            return False, f"External webhook connection failed with status {response.status_code}. Check your webhook configuration."
            
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        if 'Connection refused' in error_msg:
            return False, "External webhook connection refused. If using 'localhost', try using the Docker container name instead."
        elif 'Name or service not known' in error_msg or 'nodename nor servname provided' in error_msg or 'Name does not resolve' in error_msg or 'NameResolutionError' in error_msg:
            return False, "External webhook hostname not found. Check your webhook URL for typos or incorrect container name."
        else:
            return False, f"External webhook connection error: {error_msg}"
    except requests.exceptions.Timeout:
        return False, "External webhook connection timed out. Check if the service is running and accessible."
    except requests.exceptions.RequestException as e:
        return False, f"External webhook connection failed: {str(e)}"
    except Exception as e:
        return False, f"External webhook connection error: {str(e)}"


def _get_webhook_url():
    """Get the webhook URL from external webhook configuration."""
    if settings.general.use_external_webhook:
        webhook_url = settings.general.external_webhook_url.strip()
        if webhook_url:
            # Basic URL validation
            if not webhook_url.startswith(('http://', 'https://')):
                logging.warning(f"BAZARR invalid webhook URL format: {webhook_url} (must start with http:// or https://)")
                return None
            return webhook_url
    
    return None


def _get_webhook_auth():
    """Get authentication for the external webhook."""
    if settings.general.use_external_webhook:
        username = settings.general.external_webhook_username.strip()
        password = settings.general.external_webhook_password.strip()
        
        if username and password:
            return (username, password)
    
    return None


def _detect_path_rewrite():
    """Detect if path rewriting is needed between Bazarr and Plex."""
    try:
        # Step 1: Try smart detection (compare actual Bazarr vs Plex paths)
        smart_result = _detect_smart_path_differences()
        if smart_result['detected']:
            return smart_result
        
        # Step 2: Fall back to common pattern detection
        pattern_result = _detect_common_patterns()
        return pattern_result
        
    except Exception as e:
        logging.debug(f"BAZARR path rewrite detection failed: {e}")
        return _empty_rewrite_config()


def _detect_smart_path_differences():
    """Compare actual Bazarr vs Plex paths to detect mount point differences."""
    try:
        # Get Bazarr paths
        movie_path = settings.general.get('movie_path', '')
        series_path = settings.general.get('series_path', '')
        
        # Get Plex library paths using shared utility
        from utilities.plex_utils import get_plex_libraries_with_paths
        plex_paths = get_plex_libraries_with_paths()
        plex_movie_paths = plex_paths['movie_paths']
        plex_series_paths = plex_paths['series_paths']
        
        # Check movie paths first
        if movie_path and plex_movie_paths:
            result = _compare_path_sets(movie_path, plex_movie_paths, "movie")
            if result['detected']:
                return result
        
        # Check series paths
        if series_path and plex_series_paths:
            result = _compare_path_sets(series_path, plex_series_paths, "series")
            if result['detected']:
                return result
        
        return _empty_rewrite_config()
        
    except Exception as e:
        logging.debug(f"BAZARR smart path detection failed: {e}")
        return _empty_rewrite_config()


def _compare_path_sets(bazarr_path, plex_paths, media_type):
    """Compare a Bazarr path against Plex paths to detect differences."""
    bazarr_normalized = os.path.normpath(bazarr_path.rstrip('/'))
    
    for plex_path in plex_paths:
        plex_normalized = os.path.normpath(plex_path.rstrip('/'))
        
        # Skip if paths are identical
        if bazarr_normalized == plex_normalized:
            continue
        
        # Look for mount point differences
        rewrite_result = _detect_mount_point_difference(bazarr_normalized, plex_normalized, media_type)
        if rewrite_result['detected']:
            return rewrite_result
    
    return _empty_rewrite_config()


def _detect_mount_point_difference(bazarr_path, plex_path, media_type):
    """Detect mount point differences between two paths."""
    bazarr_parts = bazarr_path.split('/')
    plex_parts = plex_path.split('/')
    
    # Check if Bazarr has extra prefix (e.g., /mnt/media vs /media)
    if (len(bazarr_parts) > len(plex_parts) and 
        bazarr_parts[-len(plex_parts):] == plex_parts[-len(plex_parts):]):
        
        bazarr_prefix = '/'.join(bazarr_parts[:-len(plex_parts)])
        return {
            'detected': True,
            'suggestion': f"Detected mount point difference in {media_type} paths: Bazarr uses '{bazarr_prefix}' prefix not used by Plex. Path rewriting configured automatically.",
            'trigger_section': f'\nrewrite.from = "{bazarr_prefix}/"\nrewrite.to = "/"',
            'target_section': f'\nrewrite.from = "/"\nrewrite.to = "{bazarr_prefix}/"'
        }
    
    # Check if Plex has extra prefix (e.g., /data/media vs /media)
    elif (len(plex_parts) > len(bazarr_parts) and 
          plex_parts[-len(bazarr_parts):] == bazarr_parts[-len(bazarr_parts):]):
        
        plex_prefix = '/'.join(plex_parts[:-len(bazarr_parts)])
        return {
            'detected': True,
            'suggestion': f"Detected mount point difference in {media_type} paths: Plex uses '{plex_prefix}' prefix not used by Bazarr. Path rewriting configured automatically.",
            'trigger_section': f'\nrewrite.from = "/"\nrewrite.to = "{plex_prefix}/"',
            'target_section': f'\nrewrite.from = "{plex_prefix}/"\nrewrite.to = "/"'
        }
    
    return _empty_rewrite_config()


def _detect_common_patterns():
    """Check for common Docker mount patterns when smart detection fails."""
    movie_path = settings.general.get('movie_path', '')
    series_path = settings.general.get('series_path', '')
    
    # Define common rewrite patterns
    common_rewrites = [
        ('/mnt', ''),
        ('/data', ''),
        ('/media', ''),
    ]
    
    for bazarr_pattern, plex_pattern in common_rewrites:
        if (movie_path and bazarr_pattern in movie_path) or (series_path and bazarr_pattern in series_path):
            return {
                'detected': True,
                'suggestion': f"Detected path pattern '{bazarr_pattern}' in Bazarr settings. Path rewriting configured automatically.",
                'trigger_section': f'\nrewrite.from = "{bazarr_pattern}"\nrewrite.to = "{plex_pattern}"',
                'target_section': f'\nrewrite.from = "{plex_pattern}"\nrewrite.to = "{bazarr_pattern}"'
            }
    
    return _empty_rewrite_config()


def _empty_rewrite_config():
    """Return empty rewrite configuration."""
    return {
        'detected': False,
        'suggestion': "",
        'trigger_section': "",
        'target_section': ""
    }


def _inject_rewrite_config(config_text, rewrite_config):
    """Inject rewrite configuration into appropriate TOML sections."""
    lines = config_text.split('\n')
    modified_lines = []
    in_bazarr_trigger = False
    in_plex_target = False
    
    for line in lines:
        modified_lines.append(line)
        
        # Detect bazarr trigger section
        if '[triggers.bazarr]' in line:
            in_bazarr_trigger = True
        elif line.startswith('[') and in_bazarr_trigger:
            # Add rewrite config before closing the trigger section
            if rewrite_config['trigger_section']:
                modified_lines.extend(rewrite_config['trigger_section'].strip().split('\n'))
            in_bazarr_trigger = False
        
        # Detect plex target section  
        if '[targets.plex]' in line:
            in_plex_target = True
        elif line.startswith('[') and in_plex_target:
            # Add rewrite config before closing the target section
            if rewrite_config['target_section']:
                modified_lines.extend(rewrite_config['target_section'].strip().split('\n'))
            in_plex_target = False
    
    # Handle case where we're still in a section at the end of file
    if in_bazarr_trigger and rewrite_config['trigger_section']:
        modified_lines.extend(rewrite_config['trigger_section'].strip().split('\n'))
    if in_plex_target and rewrite_config['target_section']:
        modified_lines.extend(rewrite_config['target_section'].strip().split('\n'))
    
    return '\n'.join(modified_lines)
