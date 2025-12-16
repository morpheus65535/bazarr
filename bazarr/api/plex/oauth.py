# coding=utf-8

import os
import time
import uuid
import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
from flask import request
from flask_restx import Resource, reqparse, abort
import plexapi
from plexapi.exceptions import BadRequest

from . import api_ns_plex
from .exceptions import *
from .security import (TokenManager, sanitize_log_data, pin_cache, get_or_create_encryption_key, sanitize_server_url,
                       encrypt_api_key)
from app.config import settings, write_config
from app.logger import logger
from utilities.plex_utils import _get_library_locations

def _update_plexapi_headers():
    """Update plexapi headers to show Bazarr identity in Plex.
    
    Sets product name, version, instance name, and client ID for consistent
    device identification across all Plex API calls via plexapi library.
    """
    bazarr_version = os.environ.get('BAZARR_VERSION', 'unknown')
    instance_name = settings.general.get('instance_name', 'Bazarr')
    client_id = get_or_create_client_identifier()
    
    plexapi.BASE_HEADERS['X-Plex-Product'] = 'Bazarr'
    plexapi.BASE_HEADERS['X-Plex-Version'] = bazarr_version
    plexapi.BASE_HEADERS['X-Plex-Device-Name'] = instance_name
    plexapi.BASE_HEADERS['X-Plex-Client-Identifier'] = client_id


def get_token_manager():
    # Check if encryption key exists before attempting to create one
    key_existed = bool(getattr(settings.plex, 'encryption_key', None))
    key = get_or_create_encryption_key(settings.plex, 'encryption_key')
    # Save config if a new key was generated
    if not key_existed:
        write_config()
    return TokenManager(key)


def encrypt_token(token):
    if not token:
        return None
    return get_token_manager().encrypt(token)


def decrypt_token(encrypted_token):
    if not encrypted_token:
        return None
    try:
        return get_token_manager().decrypt(encrypted_token)
    except Exception as e:
        logger.error(f"Token decryption failed: {type(e).__name__}: {str(e)}")
        raise InvalidTokenError("Failed to decrypt stored authentication token. The token may be corrupted or the encryption key may have changed. Please re-authenticate with Plex.")


def generate_client_id():
    return str(uuid.uuid4())


def get_or_create_client_identifier():
    """Get existing client identifier or create and persist a new one.
    
    This ensures each Bazarr instance has a persistent, unique identifier
    that survives restarts and is used consistently in all Plex API calls.
    """
    client_id = settings.plex.get('client_identifier', '')
    if not client_id:
        client_id = str(uuid.uuid4())
        settings.plex.client_identifier = client_id
        write_config()
        logger.info(f"Generated new persistent Plex client identifier: {client_id[:8]}...")
    return client_id


def get_decrypted_token():
    auth_method = settings.plex.get('auth_method', 'apikey')

    if auth_method == 'oauth':
        token = settings.plex.get('token')
        if not token:
            return None
        return decrypt_token(token)
    else:
        apikey = settings.plex.get('apikey')
        if not apikey:
            return None

        if not settings.plex.get('apikey_encrypted', False):
            if encrypt_api_key():
                apikey = settings.plex.get('apikey')
            else:
                return None

        return decrypt_token(apikey)


def check_plex_pass_feature(account, feature_name):
    """
    Check if a Plex account has access to a specific Plex Pass feature.
    
    This helper function can be reused across the codebase to check for
    any Plex Pass feature (webhooks, sync, hardware_transcoding, etc.)
    
    Args:
        account: MyPlexAccount instance
        feature_name: The feature to check (e.g., 'webhooks', 'sync')
    
    Returns:
        tuple: (has_feature: bool, error_message: str or None)
               - (True, None) if feature is available
               - (False, error_message) if feature is not available
    """
    # Check if subscription is active first
    if not account.subscriptionActive:
        return False, (
            f'Plex Pass subscription required. The "{feature_name}" feature requires Plex Pass. '
            'Please subscribe at https://www.plex.tv/plans/'
        )
    
    # Check if specific feature is in the subscription features list
    if feature_name not in account.subscriptionFeatures:
        return False, (
            f'The "{feature_name}" feature is not available for your Plex account. '
            'This may require a different Plex Pass tier or the feature may be disabled.'
        )
    
    return True, None


def validate_plex_token(token):
    if not token:
        raise InvalidTokenError("No authentication token provided. Please authenticate with Plex first.")

    try:
        headers = {
            'X-Plex-Token': token,
            'Accept': 'application/json'
        }
        response = requests.get(
            'https://plex.tv/api/v2/user',
            headers=headers,
            timeout=10
        )
        if response.status_code == 401:
            raise InvalidTokenError("Plex server rejected the authentication token. Token may be invalid or expired.")
        elif response.status_code == 403:
            raise UnauthorizedError("Access forbidden. Your Plex account may not have sufficient permissions.")
        elif response.status_code == 404:
            raise PlexConnectionError("Plex user API endpoint not found. Please check your Plex server version.")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection to Plex.tv failed: {str(e)}")
        raise PlexConnectionError("Unable to connect to Plex.tv servers. Please check your internet connection.")
    except requests.exceptions.Timeout as e:
        logger.error(f"Plex.tv request timed out: {str(e)}")
        raise PlexConnectionError("Request to Plex.tv timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Plex token validation failed: {type(e).__name__}: {str(e)}")
        raise PlexConnectionError(f"Failed to validate token with Plex.tv: {str(e)}")


def refresh_token(token):
    if not token:
        raise InvalidTokenError("No authentication token provided for refresh.")

    try:
        headers = {
            'X-Plex-Token': token,
            'Accept': 'application/json'
        }

        response = requests.get(
            'https://plex.tv/api/v2/ping',
            headers=headers,
            timeout=10
        )

        if response.status_code == 401:
            raise TokenExpiredError("Plex authentication token has expired and cannot be refreshed.")
        elif response.status_code == 403:
            raise UnauthorizedError("Access forbidden during token refresh. Your Plex account may not have sufficient permissions.")

        response.raise_for_status()
        return token

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection to Plex.tv failed during token refresh: {str(e)}")
        raise PlexConnectionError("Unable to connect to Plex.tv servers for token refresh. Please check your internet connection.")
    except requests.exceptions.Timeout as e:
        logger.error(f"Plex.tv token refresh timed out: {str(e)}")
        raise PlexConnectionError("Token refresh request to Plex.tv timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Plex token refresh failed: {type(e).__name__}: {str(e)}")
        raise PlexConnectionError(f"Failed to refresh token with Plex.tv: {str(e)}")


def test_plex_connection(uri, token):
    if not uri or not token:
        return False, None

    try:
        uri = sanitize_server_url(uri)

        headers = {
            'X-Plex-Token': token,
            'Accept': 'application/json'
        }

        start_time = time.time()
        response = requests.get(
            f"{uri}/identity",
            headers=headers,
            timeout=3,
            verify=False
        )
        latency_ms = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            return True, latency_ms
        else:
            return False, None
    except Exception as e:
        logger.debug(f"Plex connection test failed for {sanitize_log_data(uri)}: {type(e).__name__}")
        return False, None


@api_ns_plex.route('plex/oauth/pin')
class PlexPin(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('clientId', type=str, required=False, help='Client ID')

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        try:
            args = self.post_request_parser.parse_args()
            
            # Use persistent client identifier for consistent device identity
            client_id = get_or_create_client_identifier()
            
            # Get instance name and version for device identification in Plex
            instance_name = settings.general.get('instance_name', 'Bazarr')
            bazarr_version = os.environ.get('BAZARR_VERSION', 'unknown')

            state_token = get_token_manager().generate_state_token()

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

            response = requests.post(
                'https://plex.tv/api/v2/pins',
                headers=headers,
                json={'strong': True},
                timeout=10
            )
            response.raise_for_status()

            pin_data = response.json()

            pin_cache.set(str(pin_data['id']), {
                'code': pin_data['code'],
                'client_id': client_id,
                'state_token': state_token,
                'created_at': datetime.now().isoformat()
            })

            # Include instance name in auth URL for Plex device display
            instance_name_encoded = quote_plus(instance_name)

            return {
                'data': {
                    'pinId': pin_data['id'],
                    'code': pin_data['code'],
                    'clientId': client_id,
                    'state': state_token,
                    'authUrl': f"https://app.plex.tv/auth#?clientID={client_id}&code={pin_data['code']}&context[device][product]=Bazarr&context[device][deviceName]={instance_name_encoded}"
                }
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create PIN: {type(e).__name__}")
            return {
                'error': f"Failed to create PIN: {str(e)}",
                'code': 'PLEX_CONNECTION_ERROR'
            }, 503

    def get(self):
        abort(405, "Method not allowed. Use POST.")


@api_ns_plex.route('plex/oauth/pin/<string:pin_id>/check')
class PlexPinCheck(Resource):
    def get(self, pin_id):
        try:
            state_param = request.args.get('state')

            cached_pin = pin_cache.get(pin_id)
            if not cached_pin:
                raise PlexPinExpiredError("PIN not found or expired")

            if state_param:
                stored_state = cached_pin.get('state_token')
                if not stored_state or not get_token_manager().validate_state_token(state_param, stored_state):
                    logger.warning(f"CSRF state validation failed for PIN {pin_id}")

            headers = {
                'Accept': 'application/json',
                'X-Plex-Client-Identifier': cached_pin['client_id']
            }

            response = requests.get(
                f'https://plex.tv/api/v2/pins/{pin_id}',
                headers=headers,
                timeout=10
            )

            if response.status_code == 404:
                pin_cache.delete(pin_id)
                raise PlexPinExpiredError("PIN expired or consumed")

            response.raise_for_status()
            pin_data = response.json()

            if pin_data.get('authToken'):
                user_data = validate_plex_token(pin_data['authToken'])

                encrypted_token = encrypt_token(pin_data['authToken'])

                user_id = user_data.get('id')
                user_id_str = str(user_id) if user_id is not None else ''

                settings.plex.apikey = ""
                settings.plex.ip = "127.0.0.1"
                settings.plex.port = 32400
                settings.plex.ssl = False

                settings.plex.token = encrypted_token
                settings.plex.username = user_data.get('username') or ''
                settings.plex.email = user_data.get('email') or ''
                settings.plex.user_id = user_id_str
                settings.plex.auth_method = 'oauth'
                settings.general.use_plex = True

                try:
                    write_config()
                    pin_cache.delete(pin_id)

                    logger.info(
                        f"OAuth authentication successful for user: {sanitize_log_data(user_data.get('username', ''))}")

                    return {
                        'data': {
                            'authenticated': True,
                            'username': user_data.get('username'),
                            'email': user_data.get('email')
                        }
                    }
                except Exception as config_error:
                    logger.error(f"Failed to save OAuth settings: {config_error}")

                    settings.plex.token = ""
                    settings.plex.username = ""
                    settings.plex.email = ""
                    settings.plex.user_id = ""
                    settings.plex.auth_method = 'apikey'

                    return {
                        'error': 'Failed to save authentication settings',
                        'code': 'CONFIG_SAVE_ERROR'
                    }, 500

            return {
                'data': {
                    'authenticated': False,
                    'code': pin_data.get('code')
                }
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check PIN: {type(e).__name__}")
            return {
                'error': f"Failed to check PIN: {str(e)}",
                'code': 'PLEX_CONNECTION_ERROR'
            }, 503


@api_ns_plex.route('plex/oauth/validate')
class PlexValidate(Resource):
    def get(self):
        try:
            auth_method = settings.plex.get('auth_method', 'apikey')
            decrypted_token = get_decrypted_token()

            if not decrypted_token:
                return {
                    'data': {
                        'valid': False,
                        'auth_method': auth_method
                    }
                }, 200

            user_data = validate_plex_token(decrypted_token)

            return {
                'data': {
                    'valid': True,
                    'username': user_data.get('username'),
                    'email': user_data.get('email'),
                    'auth_method': auth_method
                }
            }
        except PlexAuthError as e:
            return {
                'data': {
                    'valid': False,
                    'error': e.message,
                    'code': e.error_code
                }
            }, 200


@api_ns_plex.route('plex/oauth/servers')
class PlexServers(Resource):
    def get(self):
        try:
            decrypted_token = get_decrypted_token()
            if not decrypted_token:
                return {'data': []}

            headers = {
                'X-Plex-Token': decrypted_token,
                'Accept': 'application/json'
            }

            response = requests.get(
                'https://plex.tv/pms/resources',
                headers=headers,
                params={'includeHttps': '1', 'includeRelay': '1'},
                timeout=10
            )

            if response.status_code in (401, 403):
                logger.warning(f"Plex authentication failed: {response.status_code}")
                return {'data': []}
            elif response.status_code != 200:
                logger.error(f"Plex API error: {response.status_code}")
                raise PlexConnectionError(f"Failed to get servers: HTTP {response.status_code}")

            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                resources_data = response.json()
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                root = ET.fromstring(response.text)
                resources_data = []
                for device in root.findall('Device'):
                    connections = []
                    for conn in device.findall('Connection'):
                        connections.append({
                            'uri': conn.get('uri'),
                            'protocol': conn.get('protocol'),
                            'address': conn.get('address'),
                            'port': int(conn.get('port', 0)),
                            'local': conn.get('local') == '1'
                        })

                    if device.get('provides') == 'server' and device.get('owned') == '1':
                        resources_data.append({
                            'name': device.get('name'),
                            'clientIdentifier': device.get('clientIdentifier'),
                            'provides': device.get('provides'),
                            'owned': device.get('owned') == '1',
                            'connections': connections,
                            'productVersion': device.get('productVersion'),
                            'platform': device.get('platform'),
                            'device': device.get('device')
                        })
            else:
                raise PlexConnectionError(f"Unexpected response format: {content_type}")

            servers = []
            for device in resources_data:
                if isinstance(device, dict) and device.get('provides') == 'server' and device.get('owned'):
                    # Collect all connections for parallel testing
                    connection_candidates = []
                    connections = []
                    for conn in device.get('connections', []):
                        connection_data = {
                            'uri': conn['uri'],
                            'protocol': conn.get('protocol'),
                            'address': conn.get('address'),
                            'port': conn.get('port'),
                            'local': conn.get('local', False)
                        }
                        connection_candidates.append(connection_data)

                    # Test all connections in parallel using threads
                    if connection_candidates:
                        def test_connection_wrapper(conn_data):
                            available, latency = test_plex_connection(conn_data['uri'], decrypted_token)
                            if available:
                                conn_data['available'] = True
                                conn_data['latency'] = latency
                                return conn_data
                            return None

                        # Test connections in parallel with max 5 threads
                        with ThreadPoolExecutor(max_workers=min(5, len(connection_candidates))) as executor:
                            future_to_conn = {
                                executor.submit(test_connection_wrapper, conn): conn
                                for conn in connection_candidates
                            }

                            for future in as_completed(future_to_conn, timeout=10):
                                try:
                                    result = future.result()
                                    if result:
                                        connections.append(result)
                                except Exception as e:
                                    logger.debug(f"Connection test failed: {e}")

                    if connections:
                        # Sort connections by latency to find the best one
                        connections.sort(key=lambda x: x.get('latency', float('inf')))
                        bestConnection = connections[0] if connections else None

                        servers.append({
                            'name': device['name'],
                            'machineIdentifier': device['clientIdentifier'],
                            'connections': connections,
                            'bestConnection': bestConnection,
                            'version': device.get('productVersion'),
                            'platform': device.get('platform'),
                            'device': device.get('device')
                        })

            return {'data': servers}

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to connect to Plex: {type(e).__name__}: {str(e)}")
            return {'data': []}
        except Exception as e:
            logger.warning(f"Unexpected error getting Plex servers: {type(e).__name__}: {str(e)}")
            return {'data': []}


@api_ns_plex.route('plex/oauth/libraries')
class PlexLibraries(Resource):
    def get(self):
        try:
            decrypted_token = get_decrypted_token()
            if not decrypted_token:
                logger.warning("No decrypted token available for Plex library fetching")
                return {'data': []}

            # Get the selected server URL
            server_url = settings.plex.get('server_url')
            if not server_url:
                logger.warning("No Plex server selected")
                return {'data': []}

            logger.debug(f"Fetching Plex libraries from server: {sanitize_server_url(server_url)}")
            
            headers = {
                'X-Plex-Token': decrypted_token,
                'Accept': 'application/json'
            }

            # Get libraries from the selected server
            response = requests.get(
                f"{server_url}/library/sections",
                headers=headers,
                timeout=10,
                verify=False
            )

            if response.status_code in (401, 403):
                logger.warning(f"Plex authentication failed: {response.status_code}")
                return {'data': []}
            elif response.status_code != 200:
                logger.error(f"Plex API error: {response.status_code}")
                raise PlexConnectionError(f"Failed to get libraries: HTTP {response.status_code}")

            response.raise_for_status()
            
            # Parse the response - it could be JSON or XML depending on the server
            content_type = response.headers.get('content-type', '')
            logger.debug(f"Plex libraries response content-type: {content_type}")
            
            if 'application/json' in content_type:
                data = response.json()
                logger.debug(f"Plex libraries JSON response: {data}")
                if 'MediaContainer' in data and 'Directory' in data['MediaContainer']:
                    sections = data['MediaContainer']['Directory']
                else:
                    sections = []
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                sections = []
                for directory in root.findall('Directory'):
                    sections.append({
                        'key': directory.get('key'),
                        'title': directory.get('title'),
                        'type': directory.get('type'),
                        'count': int(directory.get('count', 0)),
                        'agent': directory.get('agent', ''),
                        'scanner': directory.get('scanner', ''),
                        'language': directory.get('language', ''),
                        'uuid': directory.get('uuid', ''),
                        'updatedAt': int(directory.get('updatedAt', 0)),
                        'createdAt': int(directory.get('createdAt', 0))
                    })
            else:
                raise PlexConnectionError(f"Unexpected response format: {content_type}")

            # Filter and format libraries for movie and show types only
            libraries = []
            for section in sections:
                if isinstance(section, dict) and section.get('type') in ['movie', 'show']:
                    # Get the actual count of items in this library section
                    try:
                        section_key = section.get('key')
                        count_response = requests.get(
                            f"{server_url}/library/sections/{section_key}/all",
                            headers={'X-Plex-Token': decrypted_token, 'Accept': 'application/json'},
                            timeout=5,
                            verify=False
                        )
                        
                        actual_count = 0
                        if count_response.status_code == 200:
                            count_data = count_response.json()
                            if 'MediaContainer' in count_data:
                                container = count_data['MediaContainer']
                                # The 'size' field contains the number of items in the library
                                actual_count = int(container.get('size', len(container.get('Metadata', []))))
                        
                        logger.debug(f"Library '{section.get('title')}' has {actual_count} items")
                        
                    except Exception as e:
                        logger.warning(f"Failed to get count for library {section.get('title')}: {e}")
                        actual_count = 0

                    libraries.append({
                        'key': str(section.get('key', '')),
                        'title': section.get('title', ''),
                        'type': section.get('type', ''),
                        'count': actual_count,
                        'agent': section.get('agent', ''),
                        'scanner': section.get('scanner', ''),
                        'language': section.get('language', ''),
                        'uuid': section.get('uuid', ''),
                        'updatedAt': int(section.get('updatedAt', 0)),
                        'createdAt': int(section.get('createdAt', 0)),
                        'locations': _get_library_locations(server_url, section_key, decrypted_token)
                    })

            logger.debug(f"Filtered Plex libraries: {libraries}")
            return {'data': libraries}

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to connect to Plex server: {type(e).__name__}: {str(e)}")
            return {'data': []}
        except Exception as e:
            logger.warning(f"Unexpected error getting Plex libraries: {type(e).__name__}: {str(e)}")
            return {'data': []}


@api_ns_plex.route('plex/oauth/logout')
class PlexLogout(Resource):
    post_request_parser = reqparse.RequestParser()

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        try:
            settings.plex.token = ""
            settings.plex.apikey = ""
            settings.plex.apikey_encrypted = False
            settings.plex.ip = "127.0.0.1"
            settings.plex.port = 32400
            settings.plex.ssl = False
            settings.plex.username = ""
            settings.plex.email = ""
            settings.plex.user_id = ""
            settings.plex.auth_method = 'apikey'
            settings.plex.server_machine_id = ""
            settings.plex.server_name = ""
            settings.plex.server_url = ""
            settings.plex.server_local = False
            settings.plex.encryption_key = ""
            settings.general.use_plex = False

            write_config()

            return {'success': True}
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return {'error': 'Failed to logout'}, 500


@api_ns_plex.route('plex/encrypt-apikey')
class PlexEncryptApiKey(Resource):
    post_request_parser = reqparse.RequestParser()

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        try:
            if encrypt_api_key():
                return {'success': True, 'message': 'API key encrypted successfully'}
            else:
                return {'success': False, 'message': 'No plain text API key found or already encrypted'}

        except Exception as e:
            logger.error(f"API key encryption failed: {e}")
            return {'error': 'Failed to encrypt API key'}, 500


@api_ns_plex.route('plex/apikey')
class PlexApiKey(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('apikey', type=str, required=True, help='API key')

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        try:
            args = self.post_request_parser.parse_args()
            apikey = args.get('apikey', '').strip()

            if not apikey:
                return {'error': 'API key is required'}, 400

            encrypted_apikey = encrypt_token(apikey)

            settings.plex.apikey = encrypted_apikey
            settings.plex.apikey_encrypted = True
            settings.plex.auth_method = 'apikey'

            write_config()

            logger.debug("API key saved and encrypted")
            return {'success': True, 'message': 'API key saved securely'}

        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            return {'error': 'Failed to save API key'}, 500


@api_ns_plex.route('plex/test-connection')
class PlexTestConnection(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('uri', type=str, required=True, help='Server URI')

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        args = self.post_request_parser.parse_args()
        uri = args.get('uri')

        decrypted_token = get_decrypted_token()
        if not decrypted_token:
            return {
                'error': 'No authentication token available',
                'code': 'UNAUTHORIZED'
            }, 401

        try:
            headers = {
                'X-Plex-Token': decrypted_token,
                'Accept': 'application/json',
                'X-Plex-Client-Identifier': generate_client_id()
            }

            response = requests.get(
                f"{uri}/identity",
                headers=headers,
                timeout=3,
                verify=False
            )

            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False}

        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Connection timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get(self):
        abort(405, "Method not allowed. Use POST.")


@api_ns_plex.route('plex/select-server')
class PlexSelectServer(Resource):
    def get(self):
        try:
            server_info = {
                'machineIdentifier': settings.plex.get('server_machine_id'),
                'name': settings.plex.get('server_name'),
                'url': settings.plex.get('server_url'),
                'local': settings.plex.get('server_local', False)
            }

            if server_info['machineIdentifier']:
                return {'data': server_info}
            else:
                return {'data': None}

        except Exception as e:
            return {'data': None}

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('machineIdentifier', type=str, required=True, help='Machine identifier')
    post_request_parser.add_argument('name', type=str, required=True, help='Server name')
    post_request_parser.add_argument('uri', type=str, required=True, help='Connection URI')
    post_request_parser.add_argument('local', type=str, required=False, default='false', help='Is local connection')

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        args = self.post_request_parser.parse_args()
        machine_identifier = args.get('machineIdentifier')
        name = args.get('name')
        connection_uri = args.get('uri')
        connection_local = args.get('local', 'false').lower() == 'true'

        settings.plex.server_machine_id = machine_identifier
        settings.plex.server_name = name
        settings.plex.server_url = connection_uri
        settings.plex.server_local = connection_local
        write_config()

        return {
            'data': {
                'success': True,
                'server': {
                    'machineIdentifier': machine_identifier,
                    'name': name,
                    'url': settings.plex.server_url,
                    'local': settings.plex.server_local
                }
            }
        }


@api_ns_plex.route('plex/webhook/create')
class PlexWebhookCreate(Resource):
    post_request_parser = reqparse.RequestParser()

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        try:
            decrypted_token = get_decrypted_token()
            if not decrypted_token:
                raise UnauthorizedError()

            # Update plexapi device name before using the library
            _update_plexapi_headers()
            
            # Import MyPlexAccount here to avoid circular imports
            from plexapi.myplex import MyPlexAccount
            
            # Create account instance with OAuth token
            account = MyPlexAccount(token=decrypted_token)
            
            # Check if user has Plex Pass with webhooks feature
            has_webhooks, error_msg = check_plex_pass_feature(account, 'webhooks')
            if not has_webhooks:
                logger.warning(f"Plex Pass check failed for webhooks: {error_msg}")
                return {'error': error_msg}, 403
            
            # Build webhook URL for this Bazarr instance
            # Try to get base URL from settings first, then fall back to request host
            configured_base_url = getattr(settings.general, 'base_url', '').rstrip('/')
            
            # Get the API key for webhook authentication
            apikey = getattr(settings.auth, 'apikey', '')
            if not apikey:
                logger.error("No API key configured - cannot create webhook")
                return {'error': 'No API key configured. Set up API key in Settings > General first.'}, 400
            
            # Get instance name for webhook identification
            instance_name = settings.general.get('instance_name', 'Bazarr')
            instance_param = quote_plus(instance_name)
            
            if configured_base_url:
                webhook_url = f"{configured_base_url}/api/webhooks/plex?apikey={apikey}&instance={instance_param}"
                logger.info(f"Using configured base URL for webhook: {configured_base_url}/api/webhooks/plex (instance: {instance_name})")
            else:
                # Fall back to using the current request's host
                scheme = 'https' if request.is_secure else 'http'
                host = request.host
                webhook_url = f"{scheme}://{host}/api/webhooks/plex?apikey={apikey}&instance={instance_param}"
                logger.info(f"Using request host for webhook (no base URL configured): {scheme}://{host}/api/webhooks/plex (instance: {instance_name})")
                logger.info("Note: If Bazarr is behind a reverse proxy, configure Base URL in General Settings for better reliability")
            
            # Get existing webhooks
            existing_webhooks = account.webhooks()
            existing_urls = []
            
            for webhook in existing_webhooks:
                try:
                    if hasattr(webhook, 'url'):
                        existing_urls.append(webhook.url)
                    elif isinstance(webhook, str):
                        existing_urls.append(webhook)
                    elif isinstance(webhook, dict) and 'url' in webhook:
                        existing_urls.append(webhook['url'])
                except Exception as e:
                    logger.warning(f"Failed to process existing webhook {webhook}: {e}")
                    continue
            
            if webhook_url in existing_urls:
                return {
                    'data': {
                        'success': True,
                        'message': 'Webhook already exists',
                        'webhook_url': webhook_url
                    }
                }
            
            # Add the webhook
            updated_webhooks = account.addWebhook(webhook_url)
            
            logger.info(f"Successfully created Plex webhook: {webhook_url}")
            
            return {
                'data': {
                    'success': True,
                    'message': 'Webhook created successfully',
                    'webhook_url': webhook_url,
                    'total_webhooks': len(updated_webhooks)
                }
            }

        except BadRequest as e:
            error_msg = str(e)
            logger.error(f"Plex API rejected webhook creation: {error_msg}")
            
            # Parse common Plex error scenarios
            if '422' in error_msg:
                if '1998' in error_msg or 'validation' in error_msg.lower():
                    return {
                        'error': 'Plex rejected the webhook. This usually means:\n'
                                 '1. Plex Pass subscription is required but not active\n'
                                 '2. The webhook URL is not publicly accessible\n'
                                 '3. Maximum webhook limit reached (check plex.tv/webhooks)\n'
                                 f'Technical details: {error_msg}'
                    }, 422
            
            return {'error': f'Plex API error: {error_msg}'}, 502

        except Exception as e:
            logger.error(f"Failed to create Plex webhook: {e}")
            return {'error': f'Failed to create webhook: {str(e)}'}, 502


@api_ns_plex.route('plex/webhook/list')
class PlexWebhookList(Resource):
    def get(self):
        try:
            decrypted_token = get_decrypted_token()
            if not decrypted_token:
                raise UnauthorizedError()

            # Update plexapi device name before using the library
            _update_plexapi_headers()
            
            from plexapi.myplex import MyPlexAccount
            account = MyPlexAccount(token=decrypted_token)
            
            webhooks = account.webhooks()
            webhook_list = []
            
            for webhook in webhooks:
                try:
                    # Handle different webhook object types
                    if hasattr(webhook, 'url'):
                        webhook_url = webhook.url
                    elif isinstance(webhook, str):
                        webhook_url = webhook
                    elif isinstance(webhook, dict) and 'url' in webhook:
                        webhook_url = webhook['url']
                    else:
                        logger.warning(f"Unknown webhook type: {type(webhook)}, value: {webhook}")
                        continue
                    
                    webhook_list.append({'url': webhook_url})
                except Exception as e:
                    logger.warning(f"Failed to process webhook {webhook}: {e}")
                    continue
            
            return {
                'data': {
                    'webhooks': webhook_list,
                    'count': len(webhook_list),
                    'plexPassSubscription': {
                        'active': account.subscriptionActive,
                        'has_webhooks_feature': 'webhooks' in account.subscriptionFeatures,
                        'plan': getattr(account, 'subscriptionPlan', None)
                    }
                }
            }

        except Exception as e:
            logger.error(f"Failed to list Plex webhooks: {e}")
            return {'error': f'Failed to list webhooks: {str(e)}'}, 502


@api_ns_plex.route('plex/webhook/delete')
class PlexWebhookDelete(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('webhook_url', type=str, required=True, help='Webhook URL to delete')

    @api_ns_plex.doc(parser=post_request_parser)
    def post(self):
        try:
            args = self.post_request_parser.parse_args()
            webhook_url = args.get('webhook_url')
            
            logger.info(f"Attempting to delete Plex webhook: {webhook_url}")
            
            decrypted_token = get_decrypted_token()
            if not decrypted_token:
                raise UnauthorizedError()

            # Update plexapi device name before using the library
            _update_plexapi_headers()
            
            from plexapi.myplex import MyPlexAccount
            account = MyPlexAccount(token=decrypted_token)
            
            # First, let's see what webhooks actually exist
            existing_webhooks = account.webhooks()
            logger.info(f"Existing webhooks before deletion: {[str(w) for w in existing_webhooks]}")
            
            # Delete the webhook
            account.deleteWebhook(webhook_url)
            
            logger.info(f"Successfully deleted Plex webhook: {webhook_url}")
            
            return {
                'data': {
                    'success': True,
                    'message': 'Webhook deleted successfully'
                }
            }

        except Exception as e:
            logger.error(f"Failed to delete Plex webhook: {e}")
            return {'error': f'Failed to delete webhook: {str(e)}'}, 502


@api_ns_plex.route('plex/autopulse/config')
class PlexAutopulseConfig(Resource):
    get_request_parser = reqparse.RequestParser()

    @api_ns_plex.doc(parser=get_request_parser)
    def get(self):
        try:
            decrypted_token = get_decrypted_token()
            if not decrypted_token:
                raise UnauthorizedError()

            # Use config generator from utilities (handles OAuth and decryption internally)
            from utilities.autopulse_webhook import generate_autopulse_config
            config = generate_autopulse_config(decrypted_token)
            
            if config:
                return {
                    'data': config
                }
            else:
                return {'error': 'Failed to get Plex configuration for Autopulse'}, 400

        except UnauthorizedError:
            return {'error': 'Plex authentication required'}, 401
        except Exception as e:
            logger.error(f"Failed to get Autopulse config: {e}")
            return {'error': f'Failed to get Autopulse config: {str(e)}'}, 500