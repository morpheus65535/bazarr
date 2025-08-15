# coding=utf-8

class PlexAuthError(Exception):
    def __init__(self, message, status_code=500, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class InvalidTokenError(PlexAuthError):
    def __init__(self, message="Invalid Plex token"):
        super().__init__(message, status_code=401, error_code="INVALID_TOKEN")

class TokenExpiredError(PlexAuthError):
    def __init__(self, message="Plex token has expired"):
        super().__init__(message, status_code=401, error_code="TOKEN_EXPIRED")

class PlexConnectionError(PlexAuthError):
    def __init__(self, message="Cannot connect to Plex"):
        super().__init__(message, status_code=503, error_code="CONNECTION_ERROR")

class PlexServerNotFoundError(PlexAuthError):
    def __init__(self, message="Plex server not found"):
        super().__init__(message, status_code=404, error_code="SERVER_NOT_FOUND")

class PlexPinExpiredError(PlexAuthError):
    def __init__(self, message="PIN has expired"):
        super().__init__(message, status_code=410, error_code="PIN_EXPIRED")

class PlexAuthTimeoutError(PlexAuthError):
    def __init__(self, message="Authentication timeout"):
        super().__init__(message, status_code=408, error_code="AUTH_TIMEOUT")

class UnauthorizedError(PlexAuthError):
    def __init__(self, message="Unauthorized"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")
