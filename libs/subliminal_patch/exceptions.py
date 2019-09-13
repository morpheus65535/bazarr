# coding=utf-8
from subliminal import ProviderError


class TooManyRequests(ProviderError):
    """Exception raised by providers when too many requests are made."""
    pass


class APIThrottled(ProviderError):
    pass


class ServiceUnavailable(ProviderError):
    """Exception raised when status is '503 Service Unavailable'."""
    pass


class DownloadLimitExceeded(ProviderError):
    """Exception raised by providers when download limit is exceeded."""
    pass
