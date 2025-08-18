# coding=utf-8

import secrets
import os
import time
import logging
from typing import Dict, Optional
from threading import RLock
from itsdangerous import URLSafeSerializer, BadSignature
from itsdangerous.exc import BadPayload
from datetime import datetime, timedelta, timezone

from .exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


class TokenManager:
    
    def __init__(self, encryption_key: str):
        self.serializer = URLSafeSerializer(encryption_key)
    
    def encrypt(self, token: str) -> str:
        if not token:
            return None
        
        salt = secrets.token_hex(16)
        timestamp = int(time.time())
        payload = {
            'token': token,
            'salt': salt, 
            'timestamp': timestamp
        }
        return self.serializer.dumps(payload)
    
    def decrypt(self, encrypted_token: str) -> str:
        if not encrypted_token:
            return None
        try:
            payload = self.serializer.loads(encrypted_token)
            if not isinstance(payload, dict) or 'token' not in payload:
                raise InvalidTokenError("Invalid token format")
            return payload['token']
        except (BadSignature, BadPayload, ValueError, KeyError):
            raise InvalidTokenError("Failed to decrypt token")
    
    def generate_state_token(self) -> str:
        return secrets.token_urlsafe(32)
    
    def validate_state_token(self, state: str, stored_state: str) -> bool:
        if not state or not stored_state:
            return False
        return secrets.compare_digest(state, stored_state)


def generate_secure_key() -> str:
    return secrets.token_urlsafe(32)

def get_or_create_encryption_key(settings_obj, key_name: str) -> str:
    key = getattr(settings_obj, key_name, None)
    # Check for both None and empty string
    if not key or key.strip() == "":
        key = generate_secure_key()
        setattr(settings_obj, key_name, key)
    return key

class PinCache:
    
    def __init__(self):
        self._cache = {}
        self._lock = RLock()
    
    def set(self, pin_id: str, data: Dict, ttl: int = 600):
        with self._lock:
            self._cache[pin_id] = {
                'data': data,
                'expires_at': datetime.now(timezone.utc) + timedelta(seconds=ttl)
            }
    
    def get(self, pin_id: str) -> Optional[Dict]:
        with self._lock:
            if pin_id not in self._cache:
                return None
            
            entry = self._cache[pin_id]
            if datetime.now(timezone.utc) > entry['expires_at']:
                del self._cache[pin_id]
                return None
            
            return entry['data'].copy()
    
    def delete(self, pin_id: str):
        with self._lock:
            self._cache.pop(pin_id, None)
    
    def cleanup_expired(self):
        with self._lock:
            current_time = datetime.now(timezone.utc)
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            for key in expired_keys:
                self._cache.pop(key, None)

pin_cache = PinCache()


def encrypt_api_key():
    """Encrypt plain text API key automatically."""
    from app.config import settings, write_config
    
    try:
        apikey = settings.plex.get('apikey')
        if apikey and not settings.plex.get('apikey_encrypted', False):
            
            encryption_key = get_or_create_encryption_key(settings.plex, 'encryption_key')
            token_manager = TokenManager(encryption_key)
            
            # Encrypt the API key
            encrypted_apikey = token_manager.encrypt(apikey)
            
            # Update settings
            settings.plex.apikey = encrypted_apikey
            settings.plex.apikey_encrypted = True
            
            # Save configuration
            write_config()
            
            logger.info("Successfully encrypted Plex API key")
            return True
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}")
        return False
    
    return False


def sanitize_server_url(url: str) -> str:
    if not url:
        return ""
    
    url = url.strip().rstrip('/')
    
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    return url

def sanitize_log_data(data: str) -> str:
    if not data or len(data) <= 8:
        return "***"
    
    visible_chars = min(4, len(data) // 3)
    if len(data) <= visible_chars * 2:
        return "***"
    
    return f"{data[:visible_chars]}...{data[-visible_chars:]}"
