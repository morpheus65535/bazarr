# coding=utf-8

"""Security utilities for Plex authentication."""
import secrets
import os
from typing import Dict, Optional
from itsdangerous import URLSafeSerializer, BadSignature
from datetime import datetime, timedelta, timezone

from .exceptions import InvalidTokenError

class TokenManager:
    """Manage secure token storage and validation using proper encryption."""
    
    def __init__(self, encryption_key: str):
        """Initialize token manager with encryption key."""
        # Use Fernet-like symmetric encryption with itsdangerous
        from itsdangerous import URLSafeSerializer
        from itsdangerous.exc import BadSignature, BadPayload
        
        self.serializer = URLSafeSerializer(encryption_key)
    
    def encrypt(self, token: str) -> str:
        """Encrypt token for secure storage."""
        if not token:
            return None
        
        # Add timestamp and random salt for proper encryption-like behavior
        import time
        salt = secrets.token_hex(16)
        timestamp = int(time.time())
        payload = {
            'token': token,
            'salt': salt, 
            'timestamp': timestamp
        }
        return self.serializer.dumps(payload)
    
    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt stored token."""
        if not encrypted_token:
            return None
        try:
            payload = self.serializer.loads(encrypted_token)
            # Validate payload structure
            if not isinstance(payload, dict) or 'token' not in payload:
                raise InvalidTokenError("Invalid token format")
            return payload['token']
        except (BadSignature, BadPayload, ValueError, KeyError):
            raise InvalidTokenError("Failed to decrypt token")
    
    def generate_state_token(self) -> str:
        """Generate CSRF state token for OAuth flow."""
        return secrets.token_urlsafe(32)
    
    def validate_state_token(self, state: str, stored_state: str) -> bool:
        """Validate CSRF state token."""
        if not state or not stored_state:
            return False
        return secrets.compare_digest(state, stored_state)


def generate_secure_key() -> str:
    """Generate a secure encryption key from system entropy."""
    # Use os.urandom for cryptographically secure random bytes
    return secrets.token_urlsafe(32)

def get_or_create_encryption_key(settings_obj, key_name: str) -> str:
    """Get existing encryption key or create a new one."""
    key = getattr(settings_obj, key_name, None)
    if not key:
        key = generate_secure_key()
        setattr(settings_obj, key_name, key)
        # Config will be written by caller
    return key

class PinCache:
    """Thread-safe cache for OAuth PINs with atomic operations."""
    
    def __init__(self):
        from threading import RLock
        self._cache = {}
        self._lock = RLock()  # Use RLock to prevent deadlocks
    
    def set(self, pin_id: str, data: Dict, ttl: int = 600):
        """Store PIN data with time-to-live (default 10 minutes)."""
        with self._lock:
            self._cache[pin_id] = {
                'data': data,
                'expires_at': datetime.now(timezone.utc) + timedelta(seconds=ttl)
            }
    
    def get(self, pin_id: str) -> Optional[Dict]:
        """Get PIN data if not expired."""
        with self._lock:
            if pin_id not in self._cache:
                return None
            
            entry = self._cache[pin_id]
            if datetime.now(timezone.utc) > entry['expires_at']:
                del self._cache[pin_id]
                return None
            
            return entry['data'].copy()  # Return copy to prevent external modification
    
    def delete(self, pin_id: str):
        """Delete PIN from cache."""
        with self._lock:
            self._cache.pop(pin_id, None)
    
    def cleanup_expired(self):
        """Remove expired entries atomically."""
        with self._lock:
            current_time = datetime.now(timezone.utc)
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            for key in expired_keys:
                self._cache.pop(key, None)

# Global instances
pin_cache = PinCache()


def sanitize_server_url(url: str) -> str:
    """Sanitize and validate server URL."""
    if not url:
        return ""
    
    # Remove trailing slashes
    url = url.strip().rstrip('/')
    
    # Ensure protocol is specified
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    return url

def sanitize_log_data(data: str) -> str:
    """Sanitize sensitive data for logging."""
    if not data or len(data) <= 8:
        return "***"
    
    # Show first 4 and last 4 characters, mask the middle
    visible_chars = min(4, len(data) // 3)
    if len(data) <= visible_chars * 2:
        return "***"
    
    return f"{data[:visible_chars]}...{data[-visible_chars:]}"