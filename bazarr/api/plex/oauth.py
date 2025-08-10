# coding=utf-8

"""Enhanced Plex OAuth implementation with security improvements."""
import time
import uuid
import requests
from functools import wraps
from itsdangerous import URLSafeSerializer
from datetime import datetime, timedelta
from flask import request, current_app
from flask_restx import Resource

from . import api_ns_plex
from .exceptions import *
from .security import TokenManager
from .cache import cache_pin, get_cached_pin, delete_cached_pin
from app.config import settings, write_config

from flask_restx import errors as restx_errors

# Register error handler for API namespace to always return JSON
@api_ns_plex.errorhandler(Exception)
def handle_api_exception(error):
    # If it's a known Bazarr exception, use its attributes
    if hasattr(error, 'error_code') and hasattr(error, 'message'):
        return {
            'error': error.message,
            'code': getattr(error, 'error_code', 'UNKNOWN_ERROR')
        }, getattr(error, 'status_code', 500)
    # If it's a requests exception
    if isinstance(error, requests.exceptions.RequestException):
        return {
            'error': str(error),
            'code': 'REQUEST_ERROR'
        }, 502
    # Otherwise, generic error
    return {
        'error': str(error),
        'code': 'UNKNOWN_ERROR'
    }, 500
def get_token_manager():
    """Get or create token manager with encryption key."""
    key = settings.plex.get('encryption_key')
    if not key:
        import secrets
        key = secrets.token_urlsafe(32)
        settings.plex.encryption_key = key
        write_config()
    return TokenManager(key)

token_manager = get_token_manager()

# Utility functions
def encrypt_token(token):
    """Encrypt Plex token for secure storage."""
    if not token:
        return None
    return token_manager.encrypt(token)

def decrypt_token(encrypted_token):
    """Decrypt Plex token."""
    if not encrypted_token:
        return None
    try:
        return token_manager.decrypt(encrypted_token)
    except Exception:
        raise InvalidTokenError("Failed to decrypt token")

def generate_client_id():
    """Generate unique client identifier."""
    return str(uuid.uuid4())

def validate_plex_token(token):
    """Validate token with Plex API."""
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
            raise InvalidTokenError()
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise PlexConnectionError(f"Failed to validate token: {str(e)}")

def refresh_token(token):
    """Refresh Plex token using ping endpoint."""
    try:
        headers = {
            'X-Plex-Token': token,
            'Accept': 'application/json'
        }
        
        # Use ping endpoint to refresh token
        response = requests.get(
            'https://plex.tv/api/v2/ping',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            raise TokenExpiredError()
        
        response.raise_for_status()
        
        # Token is still valid, return as-is
        return token
        
    except requests.exceptions.RequestException as e:
        raise PlexConnectionError(f"Failed to refresh token: {str(e)}")

def test_plex_connection(uri, token):
    """Test connection to a Plex server."""
    try:
        headers = {
            'X-Plex-Token': token,
            'Accept': 'application/json'
        }
        
        response = requests.get(
            f"{uri}/identity",
            headers=headers,
            timeout=5,
            verify=False  # Many Plex servers use self-signed certs
        )
        
        return response.status_code == 200
    except:
        return False

# Flask-RESTX Resources
@api_ns_plex.route('plex/oauth/pin')
class PlexPin(Resource):
    def post(self):
        """Create Plex OAuth PIN."""
        try:
            # Handle both JSON and form data, with fallback to empty dict
            try:
                data = request.get_json() or {}
            except:
                data = {}
            
            client_id = data.get('clientId', generate_client_id())
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Plex-Product': 'Bazarr',
                'X-Plex-Version': '1.0',  # Could get from app version
                'X-Plex-Client-Identifier': client_id,
                'X-Plex-Platform': 'Web',
                'X-Plex-Platform-Version': '1.0',
                'X-Plex-Device': 'Bazarr',
                'X-Plex-Device-Name': 'Bazarr Web'
            }
            
            response = requests.post(
                'https://plex.tv/api/v2/pins',
                headers=headers,
                json={'strong': True},
                timeout=10
            )
            response.raise_for_status()
            
            pin_data = response.json()
            
            # Store PIN in cache with expiration
            cache_pin(str(pin_data['id']), {
                'code': pin_data['code'],
                'client_id': client_id,
                'expires_at': time.time() + 600  # 10 minutes
            })
            
            return {
                'pinId': pin_data['id'],
                'code': pin_data['code'],
                'clientId': client_id,
                'authUrl': f"https://app.plex.tv/auth#?clientID={client_id}&code={pin_data['code']}&context[device][product]=Bazarr"
            }
            
        except requests.exceptions.RequestException as e:
            raise PlexConnectionError(f"Failed to create PIN: {str(e)}")

    def get(self):
        from flask_restx import abort
        abort(405, "Method not allowed. Use POST.")

@api_ns_plex.route('plex/oauth/pin/<string:pin_id>/check')
class PlexPinCheck(Resource):
    def get(self, pin_id):
        """Check PIN status."""
        try:
            # Get cached PIN
            cached_pin = get_cached_pin(pin_id)
            
            if not cached_pin:
                raise PlexPinExpiredError()
            
            # Check if PIN has expired
            if cached_pin.get('expires_at', 0) < time.time():
                delete_cached_pin(pin_id)
                raise PlexPinExpiredError()
            
            headers = {
                'Accept': 'application/json',
                'X-Plex-Client-Identifier': cached_pin['client_id']
            }
            
            response = requests.get(
                f'https://plex.tv/api/v2/pins/{pin_id}',
                headers=headers,
                timeout=10
            )
            
            # Handle specific status codes
            if response.status_code == 404:
                # PIN was consumed or expired
                delete_cached_pin(pin_id)
                raise PlexPinExpiredError()
            
            response.raise_for_status()
            
            pin_data = response.json()
            
            if pin_data.get('authToken'):
                # Validate token immediately
                user_data = validate_plex_token(pin_data['authToken'])
                
                # Store encrypted token (Bazarr uses global settings, not per-user)
                encrypted_token = encrypt_token(pin_data['authToken'])
                
                # Ensure user_id is always a string, handle None case
                user_id = user_data.get('id')
                user_id_str = str(user_id) if user_id is not None else ''
                
                # Clear ALL legacy manual configuration when switching to OAuth
                settings.plex.apikey = ""  # Clear manual API key
                settings.plex.ip = "127.0.0.1"  # Reset manual IP to default
                settings.plex.port = 32400  # Reset to default port
                settings.plex.ssl = False  # Reset SSL setting
                
                # Set OAuth configuration
                settings.plex.token = encrypted_token
                settings.plex.username = user_data.get('username') or ''
                settings.plex.email = user_data.get('email') or ''
                settings.plex.user_id = user_id_str
                settings.plex.auth_method = 'oauth'
                
                # Enable Plex integration when OAuth succeeds
                settings.general.use_plex = True
                
                # Ensure config is written before returning success
                try:
                    write_config()
                    
                    # Clean up PIN only after successful config write
                    delete_cached_pin(pin_id)
                    
                    return {
                        'authenticated': True,
                        'username': user_data.get('username'),
                        'email': user_data.get('email')
                        # Never send actual token to frontend
                    }
                except Exception as config_error:
                    # If config write fails, clear the settings from memory and fail OAuth
                    current_app.logger.error(f"Failed to save OAuth settings: {config_error}")
                    
                    # Clear OAuth settings from memory since we couldn't persist them
                    settings.plex.token = ""
                    settings.plex.username = ""
                    settings.plex.email = ""
                    settings.plex.user_id = ""
                    settings.plex.auth_method = 'apikey'
                    
                    # Return error to frontend
                    raise PlexConnectionError("Failed to save authentication settings")
                
            
            return {
                'authenticated': False,
                'code': pin_data.get('code')
            }
            
        except requests.exceptions.RequestException as e:
            raise PlexConnectionError(f"Failed to check PIN: {str(e)}")

@api_ns_plex.route('plex/oauth/validate')
class PlexValidate(Resource):
    def get(self):
        """Validate current Plex token."""
        try:
            # Only two authentication methods: apikey (manual) or oauth
            auth_method = settings.plex.get('auth_method', 'apikey')
            
            if auth_method == 'oauth':
                # OAuth: encrypted token
                token = settings.plex.get('token')
                if not token:
                    return {
                        'valid': False,
                        'auth_method': 'oauth'
                    }, 200
                decrypted_token = decrypt_token(token)
                
            else:
                # Manual/Legacy: API key (default)
                token = settings.plex.get('apikey')
                if not token:
                    return {
                        'valid': False,
                        'auth_method': 'apikey'
                    }, 200
                decrypted_token = token  # API keys aren't encrypted
            
            # Validate token with Plex
            user_data = validate_plex_token(decrypted_token)
            
            return {
                'valid': True,
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'auth_method': auth_method
            }
        except PlexAuthError as e:
            return {
                'valid': False,
                'error': e.message,
                'code': e.error_code
            }, 200  # Return 200 to distinguish from other errors

@api_ns_plex.route('plex/oauth/servers')
class PlexServers(Resource):
    def get(self):
        """Get Plex servers."""
        try:
            # Only two authentication methods: apikey (manual) or oauth
            auth_method = settings.plex.get('auth_method', 'apikey')
            
            if auth_method == 'oauth':
                # OAuth: encrypted token
                token = settings.plex.get('token')
                if not token:
                    raise UnauthorizedError()
                decrypted_token = decrypt_token(token)
                
            else:
                # Manual/Legacy: API key (default)
                token = settings.plex.get('apikey')
                if not token:
                    raise UnauthorizedError()
                decrypted_token = token  # API keys aren't encrypted
            
            headers = {
                'X-Plex-Token': decrypted_token,
                'Accept': 'application/json'
            }
            
            # Get servers from plex.tv - use the correct API endpoint
            response = requests.get(
                'https://plex.tv/pms/resources',
                headers=headers,
                params={'includeHttps': '1', 'includeRelay': '1'},
                timeout=10
            )
            
            # Add better error handling
            if response.status_code != 200:
                current_app.logger.error(f"Plex API error: {response.status_code} - {response.text}")
                raise PlexConnectionError(f"Failed to get servers: HTTP {response.status_code}")
            
            response.raise_for_status()
            
            # Check content type and parse accordingly
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                resources_data = response.json()
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                # Parse XML response
                import xml.etree.ElementTree as ET
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
                    # Test each connection
                    connections = []
                    for conn in device.get('connections', []):
                        connection_data = {
                            'uri': conn['uri'],
                            'protocol': conn.get('protocol'),
                            'address': conn.get('address'),
                            'port': conn.get('port'),
                            'local': conn.get('local', False)
                        }
                        
                        # Test connection
                        if test_plex_connection(conn['uri'], decrypted_token):
                            connection_data['available'] = True
                            connections.append(connection_data)
                    
                    if connections:
                        servers.append({
                            'name': device['name'],
                            'machineIdentifier': device['clientIdentifier'],
                            'connections': connections,
                            'version': device.get('productVersion'),
                            'platform': device.get('platform'),
                            'device': device.get('device')
                        })
            
            return {'servers': servers}
            
        except requests.exceptions.RequestException as e:
            raise PlexConnectionError(f"Failed to get servers: {str(e)}")

@api_ns_plex.route('plex/oauth/logout')
class PlexLogout(Resource):
    def post(self):
        """Complete Plex disconnect - clear ALL authentication and server settings."""
        try:
            # Clear ALL Plex authentication settings for complete reset
            settings.plex.token = ""  # Clear OAuth token
            settings.plex.apikey = ""  # Clear manual API key
            settings.plex.ip = "127.0.0.1"  # Reset IP to default
            settings.plex.port = 32400  # Reset port to default
            settings.plex.ssl = False  # Reset SSL to default
            settings.plex.username = ""  # Clear user info
            settings.plex.email = ""  # Clear user info
            settings.plex.user_id = ""  # Clear user info
            settings.plex.auth_method = 'apikey'  # Reset to default
            
            # Clear server selection as well for complete reset
            settings.plex.server_machine_id = ""
            settings.plex.server_name = ""
            settings.plex.server_url = ""
            settings.plex.server_local = False
            
            # Auto-disable Plex integration when disconnecting
            # Since OAuth auto-enables Plex, disconnect should auto-disable it for consistency
            settings.general.use_plex = False
            
            write_config()

            return {'success': True}
        except Exception as e:
            return {'error': 'Failed to logout'}, 500

# Additional endpoints referenced in frontend
@api_ns_plex.route('plex/test-connection')
class PlexTestConnection(Resource):
    def post(self):
        """Test connection to a specific Plex server URI."""
        data = request.get_json()
        uri = data.get('uri')
        
        if not uri:
            raise PlexAuthError('Missing URI', 'MISSING_PARAMETER')
        
        # Only two authentication methods: apikey (manual) or oauth
        auth_method = settings.plex.get('auth_method', 'apikey')
        
        if auth_method == 'oauth':
            # OAuth: encrypted token
            token = settings.plex.get('token')
            if not token:
                raise UnauthorizedError()
            decrypted_token = decrypt_token(token)
            
        else:
            # Manual/Legacy: API key (default)
            token = settings.plex.get('apikey')
            if not token:
                raise UnauthorizedError()
            decrypted_token = token  # API keys aren't encrypted
        
        try:
            # Test connection with a simple identity request
            headers = {
                'X-Plex-Token': decrypted_token,
                'Accept': 'application/json',
                'X-Plex-Client-Identifier': generate_client_id()
            }
            
            response = requests.get(
                f"{uri}/identity",
                headers=headers,
                timeout=5,
                verify=False  # Many Plex servers use self-signed certs
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
        from flask_restx import abort
        abort(405, "Method not allowed. Use POST.")

@api_ns_plex.route('plex/select-server')
class PlexSelectServer(Resource):
    def get(self):
        """Get currently selected Plex server."""
        try:
            server_info = {
                'machineIdentifier': settings.plex.get('server_machine_id'),
                'name': settings.plex.get('server_name'),
                'url': settings.plex.get('server_url'),
                'local': settings.plex.get('server_local', False)
            }
            
            # Only return server info if we have a machine identifier
            if server_info['machineIdentifier']:
                return {'server': server_info}
            else:
                return {'server': None}
                
        except Exception as e:
            return {'server': None}
    
    def post(self):
        """Select a specific Plex server to use."""
        data = request.get_json()
        machine_identifier = data.get('machineIdentifier')
        name = data.get('name')
        connection = data.get('connection', {})
        
        if not machine_identifier or not name or not connection.get('uri'):
            raise PlexAuthError('Missing required fields', 'MISSING_PARAMETER')
        
        # Save server information
        settings.plex.server_machine_id = machine_identifier
        settings.plex.server_name = name
        settings.plex.server_url = connection.get('uri')
        settings.plex.server_local = connection.get('local', False)
        write_config()
        
        return {
            'success': True,
            'server': {
                'machineIdentifier': machine_identifier,
                'name': name,
                'url': settings.plex.server_url,
                'local': settings.plex.server_local
            }
        }

# Note: Flask-RESTX handles exceptions differently than Blueprint error handlers
# The exceptions module should raise appropriate HTTP errors that Flask-RESTX will handle
