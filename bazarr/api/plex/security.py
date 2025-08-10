# coding=utf-8

"""Security utilities for Plex authentication."""
import secrets
import hashlib
from typing import Dict, Optional
from itsdangerous import URLSafeSerializer, BadSignature
from datetime import datetime, timedelta

from .exceptions import InvalidTokenError

class TokenManager:
    """Manage secure token storage and validation."""
    
    def __init__(self, encryption_key: str):
        """Initialize token manager with encryption key."""
        self.serializer = URLSafeSerializer(encryption_key)
        self._tokens = {}  # In-memory token cache
    
    def encrypt(self, token: str) -> str:
        """Encrypt token for storage."""
        if not token:
            return None
        return self.serializer.dumps(token)
    
    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt stored token."""
        if not encrypted_token:
            return None
        try:
            return self.serializer.loads(encrypted_token)
        except BadSignature:
            raise InvalidTokenError("Failed to decrypt token")
    
    def generate_state_token(self) -> str:
        """Generate CSRF state token for OAuth flow."""
        return secrets.token_urlsafe(32)
    
    def validate_state_token(self, state: str, stored_state: str) -> bool:
        """Validate CSRF state token."""
        return secrets.compare_digest(state, stored_state)
    
    def store_token(self, user_id: str, token: str, expiry: Optional[datetime] = None):
        """Store token in cache with optional expiry."""
        self._tokens[user_id] = {
            'token': self.encrypt(token),
            'expiry': expiry or datetime.utcnow() + timedelta(days=30),
            'created': datetime.utcnow()
        }
    
    def get_token(self, user_id: str) -> Optional[str]:
        """Get token from cache if not expired."""
        if user_id not in self._tokens:
            return None
        
        token_data = self._tokens[user_id]
        if datetime.utcnow() > token_data['expiry']:
            del self._tokens[user_id]
            return None
        
        return self.decrypt(token_data['token'])
    
    def revoke_token(self, user_id: str):
        """Revoke user token."""
        if user_id in self._tokens:
            del self._tokens[user_id]

def hash_client_id(client_id: str) -> str:
    """Hash client ID for secure storage."""
    return hashlib.sha256(client_id.encode()).hexdigest()

def generate_secure_pin() -> str:
    """Generate secure PIN for OAuth flow."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def sanitize_server_url(url: str) -> str:
    """Sanitize and validate server URL."""
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Ensure protocol is specified
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    return url

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = datetime.utcnow()
        
        # Clean old attempts
        self._cleanup_old_attempts(now)
        
        if key not in self._attempts:
            self._attempts[key] = []
        
        # Count recent attempts
        recent_attempts = [
            attempt for attempt in self._attempts[key]
            if (now - attempt).total_seconds() < self.window_seconds
        ]
        
        if len(recent_attempts) >= self.max_attempts:
            return False
        
        self._attempts[key].append(now)
        return True
    
    def _cleanup_old_attempts(self, now: datetime):
        """Remove old attempts from memory."""
        for key in list(self._attempts.keys()):
            self._attempts[key] = [
                attempt for attempt in self._attempts[key]
                if (now - attempt).total_seconds() < self.window_seconds
            ]
            if not self._attempts[key]:
                del self._attempts[key]

# Global instances
rate_limiter = RateLimiter(max_attempts=10, window_seconds=300)

# Flask-RESTX decorator for rate limiting
def rate_limit(func):
    """Decorator to apply rate limiting to Flask-RESTX resources."""
    from functools import wraps
    from flask import request
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        endpoint = request.endpoint or 'unknown'
        key = f"{endpoint}_{client_ip}"
        
        if not rate_limiter.is_allowed(key):
            return {'error': 'Rate limit exceeded', 'code': 'RATE_LIMIT_EXCEEDED'}, 429
            
        return func(*args, **kwargs)
    
    return wrapper
