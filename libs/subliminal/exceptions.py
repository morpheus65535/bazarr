# -*- coding: utf-8 -*-
class Error(Exception):
    """Base class for exceptions in subliminal."""
    pass


class ProviderError(Error):
    """Exception raised by providers."""
    pass


class ConfigurationError(ProviderError):
    """Exception raised by providers when badly configured."""
    pass


class AuthenticationError(ProviderError):
    """Exception raised by providers when authentication failed."""
    pass


class TooManyRequests(ProviderError):
    """Exception raised by providers when too many requests are made."""
    pass


class DownloadLimitExceeded(ProviderError):
    """Exception raised by providers when download limit is exceeded."""
    pass
