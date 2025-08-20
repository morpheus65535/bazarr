# coding=utf-8

class PlexAuthError(Exception):
    def __init__(self, message, status_code=500, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class InvalidTokenError(PlexAuthError):
    def __init__(self, message="Invalid or malformed Plex authentication token. Please re-authenticate with Plex."):
        super().__init__(message, status_code=401, error_code="INVALID_TOKEN")

class TokenExpiredError(PlexAuthError):
    def __init__(self, message="Plex authentication token has expired. Please re-authenticate with Plex to continue."):
        super().__init__(message, status_code=401, error_code="TOKEN_EXPIRED")

class PlexConnectionError(PlexAuthError):
    def __init__(self, message="Unable to establish connection to Plex server. Please check server status and network connectivity."):
        super().__init__(message, status_code=503, error_code="CONNECTION_ERROR")

class PlexServerNotFoundError(PlexAuthError):
    def __init__(self, message="Plex server not found or not accessible. Please verify server URL and authentication credentials."):
        super().__init__(message, status_code=404, error_code="SERVER_NOT_FOUND")

class PlexPinExpiredError(PlexAuthError):
    def __init__(self, message="Plex authentication PIN has expired. Please request a new PIN and try again."):
        super().__init__(message, status_code=410, error_code="PIN_EXPIRED")

class PlexAuthTimeoutError(PlexAuthError):
    def __init__(self, message="Plex authentication process timed out. Please try again or check your internet connection."):
        super().__init__(message, status_code=408, error_code="AUTH_TIMEOUT")

class UnauthorizedError(PlexAuthError):
    def __init__(self, message="Access denied. Please check your Plex authentication credentials and permissions."):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")
