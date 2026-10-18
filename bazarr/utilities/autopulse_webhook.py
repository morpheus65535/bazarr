# coding=utf-8

import logging
import os
import requests
from urllib.parse import urlencode
from retry.api import retry
from typing import TypedDict

from app.config import settings


class AutopulseTemplate(TypedDict, total=False):
    config: str
    version: str


class AutopulseConfig(TypedDict):
    config_yaml: str
    server_name: str
    rewrite_detected: bool
    rewrite_suggestion: str | None
    template_info: str


class RewriteConfig(TypedDict):
    detected: bool
    suggestion: str
    trigger_section: str
    target_section: str


def generate_autopulse_config(decrypted_token: str | None = None) -> AutopulseConfig | None:
    """
    Generate an Autopulse configuration for the configured Plex server.

    This function builds a Plex-specific Autopulse configuration based on the
    current application settings. It only proceeds when Plex is configured to
    use the OAuth authentication method; any other authentication method causes
    the function to return early without producing a configuration. If no
    decrypted token is supplied, the token is retrieved from the Plex OAuth
    subsystem. A configuration template is then fetched from the running
    Autopulse instance and populated with the Plex server URL, server name and
    access token.

    All failures are handled internally: missing OAuth credentials, a missing
    Plex server URL, an unavailable Autopulse template API, or any unexpected
    exception are logged and result in no configuration being returned.

    :param decrypted_token: An already decrypted Plex OAuth access token to use
        when building the configuration. When omitted or empty, the token is
        obtained from the Plex OAuth subsystem.
    :return: The generated Autopulse configuration, or ``None`` if Plex is not
        using OAuth authentication, required Plex settings or credentials are
        missing, the Autopulse template could not be retrieved, or an error
        occurred during generation.
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


def _get_autopulse_template() -> AutopulseTemplate | None:
    """
    Retrieve the Autopulse configuration template from the configured
    external webhook endpoint.

    The template URL and authentication credentials are resolved from the
    external webhook settings. If no URL is configured, the request is
    skipped. The request is issued with parameters selecting the dedicated
    Bazarr trigger type, the Plex target and the SQLite database, together
    with a user agent derived from the ``SZ_USER_AGENT`` environment
    variable (falling back to ``Bazarr``).

    Unsuccessful HTTP responses are logged with hints about possible
    misconfiguration (authentication failures, bad requests or other
    status codes) and no template is returned. Network-level failures and
    unexpected errors are caught and logged as well, so this function
    never propagates exceptions to the caller.

    :return: The parsed JSON configuration template when the request
        succeeds with a 200 status code, otherwise ``None`` (no URL
        configured, non-successful HTTP status, request failure or
        unexpected error).
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


def _get_autopulse_template_url() -> str | None:
    """
    Derive the autopulse configuration template API URL from the configured
    webhook URL.

    The configured webhook URL is retrieved and transformed into the URL of the
    configuration template endpoint. When the webhook URL contains a trigger
    path segment, everything from that segment onward is discarded and replaced
    with the API path. Otherwise, the webhook URL is treated as a base URL and
    the API path is appended after stripping any trailing slashes. Any failure
    during the transformation is silently handled.

    :return: The configuration template API URL, or ``None`` if no webhook URL
        is configured or the URL could not be transformed.

    """
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


def _generate_config_from_template(template_data: AutopulseTemplate, server_url: str,
                                   decrypted_token: str, server_name: str) -> AutopulseConfig | None:
    """
    Generate a complete Autopulse configuration from a dynamic template.

    Builds a ready-to-use Autopulse configuration by taking the base
    configuration contained in the provided template and substituting its
    placeholders (``{url}``, ``{token}``, ``{username}`` and ``{password}``)
    with the given server URL, decrypted token and the configured webhook
    authentication credentials. When no webhook authentication is
    configured, the credential placeholders are replaced with empty
    strings. Autopulse defaults are then overridden with Bazarr-optimized
    values (refresh enabled, analyze disabled). Path rewriting needs are
    detected automatically and, when found, the corresponding rewrite
    section is injected into the configuration. Finally, a header comment
    containing the server name, template version, trigger type and path
    rewriting status is prepended, along with a trailing usage hint.

    Any failure during generation is logged and results in ``None`` being
    returned instead of an exception being propagated.

    :param template_data: Template response containing at least a
        ``config`` field with the base configuration and an optional
        ``version`` field describing the template version.
    :param server_url: URL of the server to substitute for the ``{url}``
        placeholder in the template.
    :param decrypted_token: Plain-text token to substitute for the
        ``{token}`` placeholder in the template.
    :param server_name: Human-readable server name included in the
        generated configuration header and in the returned result.
    :return: A mapping containing the generated configuration text, the
        server name, whether path rewriting was detected, an optional path
        rewrite suggestion and a template information message; ``None`` if
        the template is missing its configuration field or if any error
        occurs during generation.
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


def call_external_webhook(subtitle_path: str | None, media_path: str | None, language: str | None,
                          media_type: str | None, action_type: str | None) -> None:
    """
    Notify an externally configured webhook about a subtitle-related event.

    The call is skipped entirely when the external webhook feature is disabled
    in the general settings or when no webhook URL has been configured. All
    ``None`` arguments are normalised to empty strings before being sent. The
    parent directory of ``media_path`` is used as the grouping ``path`` query
    parameter, and all values are passed as URL-encoded query parameters of a
    GET request. The ``path`` parameter duplicates the directory of
    ``media_path`` for backward compatibility with Autopulse.

    Authentication credentials and the webhook URL are read from the
    application settings, and the request is retried on transient network
    issues. The HTTP response status is inspected and the outcome is reported
    through logging: success is logged at info level, authentication failures
    (401), bad requests (400) and any other non-200 statuses are logged as
    warnings, and request or unexpected errors are logged as errors. No
    exception is propagated to the caller.

    :param subtitle_path: Filesystem path of the subtitle file affected by the
        event, or ``None`` if not applicable.
    :param media_path: Filesystem path of the media file the subtitle belongs
        to, or ``None`` if not applicable.
    :param language: Language identifier of the subtitle, or ``None`` if not
        applicable.
    :param media_type: Kind of media involved (for example a movie or an
        episode), or ``None`` if not applicable.
    :param action_type: Kind of action that triggered the webhook, or ``None``
        if not applicable.
    :return: This function does not return a value.
    """
    # Check if external webhook is enabled
    if not settings.general.use_external_webhook:
        return

    params: dict[str, str] = {}
    try:
        # Use parent directory instead of specific file for better grouping
        media_path = "" if media_path is None else media_path
        parent_dir = os.path.dirname(media_path)
        
        # Get webhook configuration
        webhook_url = _get_webhook_url()
        auth = _get_webhook_auth()
        
        if not webhook_url:
            logging.debug("BAZARR external webhook not configured, skipping")
            return

        # Prepare query parameters
        # Note: 'path' is included even though it's redundant with 'media_path' for backward compatibility with Autopulse
        action_type   = "" if action_type is None else action_type
        language      = "" if language is None else language
        media_type    = "" if media_type is None else media_type
        subtitle_path = "" if subtitle_path is None else subtitle_path
        params = {'path': parent_dir, 'action_type': action_type, 'language': language, 'media_type': media_type, 'subtitle_path': subtitle_path, 'media_path': media_path}
        full_url = f"{webhook_url}?{urlencode(params)}"
        
        headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", 'Bazarr')}
        
        logging.debug(f"BAZARR calling external webhook: {webhook_url}, with params: {params}")
        
        # Make the webhook call with retry for network issues
        response = _make_webhook_request(full_url, auth, headers)
        
        if response.status_code == 200:
            logging.info(f"BAZARR external webhook successful for {params}")
        elif response.status_code == 401:
            logging.warning(f"BAZARR external webhook authentication failed (401) for {params}. Did you forget to save your external webhook settings?")
        elif response.status_code == 400:
            logging.warning(f"BAZARR external webhook bad request (400) for {params}. Check your webhook URL and credentials. Did you forget to save your external webhook settings?")
        else:
            logging.warning(f"BAZARR external webhook failed with status {response.status_code} for {params}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"BAZARR external webhook failed for {params}: {str(e)}. Did you forget to save your external webhook settings?")
    except Exception as e:
        logging.error(f"BAZARR unexpected error calling external webhook for {params}: {str(e)}")


@retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=1, backoff=2, jitter=(0, 1))
def _make_webhook_request(url: str, auth: tuple[str, str] | None, headers: dict[str, str]) -> requests.Response:
    """
    Perform an HTTP GET request to the given webhook URL with automatic retries.

    The request is issued with a 30-second timeout and TLS certificate
    verification enabled. If a ``requests.exceptions.RequestException``
    occurs, the call is retried up to three times with an exponentially
    increasing delay (starting at one second, doubling on each attempt)
    plus a random jitter of up to one second.

    :param url: The webhook endpoint to send the GET request to.
    :param auth: Optional ``(username, password)`` pair used for HTTP
        basic authentication, or ``None`` to send the request
        unauthenticated.
    :param headers: Additional HTTP headers to include in the request.
    :return: The HTTP response returned by the webhook endpoint.
    :raises requests.exceptions.RequestException: If the request fails on
        every retry attempt.
    """
    return requests.get(
        url,
        auth=auth,
        headers=headers,
        timeout=30,
        verify=True
    )


@retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=1, backoff=2, jitter=(0, 1))
def _make_autopulse_request(url: str, params: dict[str, str] | None = None,
                            auth: tuple[str, str] | None = None,
                            headers: dict[str, str] | None = None) -> requests.Response:
    """
    Perform an HTTP GET request against an Autopulse endpoint with automatic
    retries.

    The request is sent with a fixed timeout of 10 seconds and TLS certificate
    verification enabled. If the request fails with a
    ``requests.exceptions.RequestException``, it is retried up to three times
    using an exponential backoff strategy (initial delay of 1 second, doubled on
    each attempt) with a random jitter of up to 1 second added between retries.
    The response object is returned as-is; no status code validation is
    performed, so callers are responsible for checking the response status.

    :param url: Fully qualified URL of the Autopulse endpoint to query.
    :param params: Optional query string parameters to append to the request
        URL. Defaults to ``None``.
    :param auth: Optional ``(username, password)`` pair used for HTTP basic
        authentication. Defaults to ``None``.
    :param headers: Optional HTTP headers to include in the request. Defaults
        to ``None``.
    :return: The HTTP response returned by the Autopulse endpoint.
    :raises requests.exceptions.RequestException: If the request still fails
        after all retry attempts have been exhausted.
    """
    return requests.get(
        url,
        params=params,
        auth=auth,
        headers=headers,
        timeout=10,
        verify=True
    )


def test_external_webhook_connection() -> tuple[bool, str]:
    """
    Test connectivity to the configured external webhook endpoint.

    Reads the webhook URL and optional authentication credentials from the
    application settings and performs an HTTP GET request against the
    endpoint to verify that it is reachable and accepts the supplied
    credentials. When the configured URL appears to target an Autopulse
    trigger (contains a ``/triggers/`` path segment), the request is sent
    to the service's ``/stats`` endpoint instead of the trigger URL itself,
    so that no trigger is actually fired during the test.

    The request uses a 10 second timeout, enforces TLS certificate
    verification and sends a ``User-Agent`` header taken from the
    ``SZ_USER_AGENT`` environment variable, falling back to ``Bazarr``.
    Debug information about the test is written to the application log.

    All failure conditions, including a missing configuration, HTTP error
    statuses and network-level problems such as refused connections, DNS
    resolution failures and timeouts, are translated into human-readable
    messages intended to be displayed to the user. No exception is
    propagated to the caller.

    :return: A tuple whose first element indicates whether the connection
        test succeeded and whose second element is a descriptive message
        explaining the outcome or the reason for failure.
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


def _get_webhook_url() -> str | None:
    """
    Retrieve the configured external webhook URL from the application
    settings. The URL is only resolved when the external webhook feature is
    enabled in the general settings. The configured value is stripped of
    surrounding whitespace and validated to ensure it uses the ``http://`` or
    ``https://`` scheme; an invalid scheme is logged as a warning and treated
    as if no URL were configured.

    :return: The validated external webhook URL, or ``None`` if the external
        webhook feature is disabled, the URL is empty, or the URL does not
        start with a supported scheme.
    """
    if settings.general.use_external_webhook:
        webhook_url = settings.general.external_webhook_url.strip()
        if webhook_url:
            # Basic URL validation
            if not webhook_url.startswith(('http://', 'https://')):
                logging.warning(f"BAZARR invalid webhook URL format: {webhook_url} (must start with http:// or https://)")
                return None
            return webhook_url
    
    return None


def _get_webhook_auth() -> tuple[str, str] | None:
    """
    Build the HTTP basic authentication credentials used for external
    webhook requests.

    The credentials are only produced when the use of an external webhook
    is enabled in the general settings and both the configured username and
    password are non-empty after stripping surrounding whitespace. In all
    other cases no credentials are provided, which signals that webhook
    requests should be sent without authentication.

    :return: A ``(username, password)`` pair suitable for HTTP basic
        authentication, or ``None`` if the external webhook is disabled or
        either credential is missing.
    """
    if settings.general.use_external_webhook:
        username = settings.general.external_webhook_username.strip()
        password = settings.general.external_webhook_password.strip()
        
        if username and password:
            return (username, password)
    
    return None


def _detect_path_rewrite() -> RewriteConfig:
    """
    Detect path rewrite configuration between Bazarr and Plex.

    Attempts to determine how Bazarr paths should be rewritten to
    match Plex paths. Smart detection, which compares actual Bazarr
    and Plex paths, is tried first. If no differences are detected,
    detection falls back to matching common known path patterns.
    Any failure during detection is logged at debug level and an
    empty rewrite configuration is returned instead of propagating
    the error.

    :return: The detected rewrite configuration, or an empty rewrite
        configuration when detection fails or nothing is detected.
    """
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


def _detect_smart_path_differences() -> RewriteConfig:
    """
    Detect path differences between Bazarr and Plex library configurations
    and derive a path rewrite configuration.

    Reads the configured Bazarr movie and series root paths, retrieves the
    library paths registered in Plex, and compares the two sets. Movie paths
    are compared first; if a difference is detected, the resulting rewrite
    configuration is returned immediately. Otherwise, series paths are
    compared in the same way. When no difference is found, or when any
    error occurs during detection (for example, Plex being unreachable), an
    empty rewrite configuration is returned and the failure is logged at
    debug level so that the caller can proceed without path rewriting.

    :return: The detected rewrite configuration describing how Bazarr paths
        map to Plex paths, or an empty rewrite configuration if no
        difference could be detected or detection failed.
    """
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


def _compare_path_sets(bazarr_path: str, plex_paths: list[str], media_type: str) -> RewriteConfig:
    """
    Compare a Bazarr media path against a collection of Plex library paths
    in order to detect a mount point mismatch that would require a path
    rewrite rule.

    The Bazarr path and each Plex path are normalized (trailing slashes
    removed and platform-specific normalization applied) before comparison.
    Plex paths that are identical to the Bazarr path are skipped, since no
    rewrite is needed for them. For every remaining Plex path, a mount point
    difference check is performed; the first detected rewrite configuration
    is returned immediately. If no difference is found for any of the given
    Plex paths, an empty rewrite configuration is returned.

    :param bazarr_path: Root path used by Bazarr for the media library.
    :param plex_paths: Root paths reported by Plex for the corresponding
        library sections.
    :param media_type: Kind of media the paths belong to (for example
        series or movies), passed through to the mount point detection.
    :return: Rewrite configuration describing the detected mount point
        difference, or an empty configuration when the paths are
        equivalent or no difference could be detected.
    """
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


def _detect_mount_point_difference(bazarr_path: str, plex_path: str, media_type: str) -> RewriteConfig:
    """
    Compare a Bazarr media path with the corresponding Plex media path and
    determine whether one of them carries an additional mount point prefix
    that the other lacks.

    Both paths are split into their non-empty segments and compared from the
    tail. If the Bazarr path ends with the full Plex path, the leading extra
    segments of the Bazarr path are treated as a Bazarr-only prefix. If the
    Plex path ends with the full Bazarr path, the leading extra segments of the
    Plex path are treated as a Plex-only prefix. In either case a rewrite
    configuration is produced describing the detected difference, a
    human-readable suggestion mentioning the media type, and the TOML snippets
    needed to translate paths in both directions (trigger side and target
    side). When neither path is a suffix of the other, or when both paths are
    identical, an empty rewrite configuration is returned.

    :param bazarr_path: Absolute media path as seen by Bazarr.
    :param plex_path: Absolute media path as seen by Plex.
    :param media_type: Label of the media category (for example movies or
        series) used to contextualize the generated suggestion message.
    :return: A rewrite configuration mapping with the keys ``detected``,
        ``suggestion``, ``trigger_section`` and ``target_section``; the empty
        configuration is returned when no mount point difference is found.
    """
    # Drop the empty segment produced by the leading slash so the tails compare correctly
    bazarr_parts = [part for part in bazarr_path.split('/') if part]
    plex_parts = [part for part in plex_path.split('/') if part]

    # Check if Bazarr has extra prefix (e.g., /mnt/media vs /media)
    if (len(bazarr_parts) > len(plex_parts) and
        bazarr_parts[-len(plex_parts):] == plex_parts):

        bazarr_prefix = '/' + '/'.join(bazarr_parts[:-len(plex_parts)])
        return {
            'detected': True,
            'suggestion': f"Detected mount point difference in {media_type} paths: Bazarr uses '{bazarr_prefix}' prefix not used by Plex. Path rewriting configured automatically.",
            'trigger_section': f'\nrewrite.from = "{bazarr_prefix}/"\nrewrite.to = "/"',
            'target_section': f'\nrewrite.from = "/"\nrewrite.to = "{bazarr_prefix}/"'
        }
    
    # Check if Plex has extra prefix (e.g., /data/media vs /media)
    elif (len(plex_parts) > len(bazarr_parts) and
          plex_parts[-len(bazarr_parts):] == bazarr_parts):

        plex_prefix = '/' + '/'.join(plex_parts[:-len(bazarr_parts)])
        return {
            'detected': True,
            'suggestion': f"Detected mount point difference in {media_type} paths: Plex uses '{plex_prefix}' prefix not used by Bazarr. Path rewriting configured automatically.",
            'trigger_section': f'\nrewrite.from = "/"\nrewrite.to = "{plex_prefix}/"',
            'target_section': f'\nrewrite.from = "{plex_prefix}/"\nrewrite.to = "/"'
        }
    
    return _empty_rewrite_config()


def _detect_common_patterns() -> RewriteConfig:
    """
    Detect common path prefix patterns in the configured Bazarr movie and
    series paths and derive a matching path rewrite configuration.

    The function inspects the ``movie_path`` and ``series_path`` values from
    the general settings and checks them against a predefined list of common
    mount-point prefixes (``/mnt``, ``/data`` and ``/media``). When one of
    these prefixes is found in either path, a rewrite configuration is built
    that maps the Bazarr-side prefix to the corresponding Plex-side prefix for
    the trigger section, and the reverse mapping for the target section. The
    first matching pattern wins; if no pattern matches, an empty rewrite
    configuration is returned instead.

    :return: A rewrite configuration describing whether a pattern was
        detected, a human-readable suggestion message, and the rewrite
        snippets for the trigger and target sections. If no known pattern is
        found, an empty rewrite configuration is returned.
    :rtype: RewriteConfig
    """
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


def _empty_rewrite_config() -> RewriteConfig:
    """
    Create an empty rewrite configuration with default values.

    Builds a ``RewriteConfig`` dictionary in which no rewrite has been
    detected, the suggestion is an empty string, and both the trigger
    section and the target section are empty strings. This serves as a
    neutral baseline that can later be populated when a rewrite is
    actually detected.

    :return: A rewrite configuration populated with default
        (empty / not detected) values.

    """
    return {
        'detected': False,
        'suggestion': "",
        'trigger_section': "",
        'target_section': ""
    }


def _inject_rewrite_config(config_text: str, rewrite_config: RewriteConfig) -> str:
    """
    Inject rewrite configuration snippets into an INI/TOML-style
    configuration text.

    The function scans the configuration line by line and tracks whether
    the current position is inside the ``[triggers.bazarr]`` or the
    ``[targets.plex]`` section. When the end of one of these sections is
    reached (either because a new section header begins or because the end
    of the text is reached), the corresponding snippet from the rewrite
    configuration is appended to that section. Snippets are stripped of
    surrounding whitespace and split into individual lines before being
    inserted. Empty or missing snippets are ignored and leave the
    corresponding section unchanged. All other lines are preserved as-is
    and in their original order.

    :param config_text: Full text of the configuration file whose
        ``[triggers.bazarr]`` and ``[targets.plex]`` sections should be
        extended.
    :param rewrite_config: Mapping providing the snippets to inject; the
        ``trigger_section`` entry is appended to the ``[triggers.bazarr]``
        section and the ``target_section`` entry is appended to the
        ``[targets.plex]`` section.
    :return: The modified configuration text with the rewrite snippets
        inserted at the end of their respective sections.
    """
    lines = config_text.split('\n')
    modified_lines = []
    in_bazarr_trigger = False
    in_plex_target = False
    
    for line in lines:
        # A new section header closes the current one, so the rewrite must be added before the header
        if line.startswith('[') and in_bazarr_trigger:
            if rewrite_config['trigger_section']:
                modified_lines.extend(rewrite_config['trigger_section'].strip().split('\n'))
            in_bazarr_trigger = False

        if line.startswith('[') and in_plex_target:
            if rewrite_config['target_section']:
                modified_lines.extend(rewrite_config['target_section'].strip().split('\n'))
            in_plex_target = False

        if '[triggers.bazarr]' in line:
            in_bazarr_trigger = True
        if '[targets.plex]' in line:
            in_plex_target = True

        modified_lines.append(line)

    # Handle case where we're still in a section at the end of file
    if in_bazarr_trigger and rewrite_config['trigger_section']:
        modified_lines.extend(rewrite_config['trigger_section'].strip().split('\n'))
    if in_plex_target and rewrite_config['target_section']:
        modified_lines.extend(rewrite_config['target_section'].strip().split('\n'))
    
    return '\n'.join(modified_lines)
