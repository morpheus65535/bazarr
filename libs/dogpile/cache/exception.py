"""Exception classes for dogpile.cache."""


class DogpileCacheException(Exception):
    """Base Exception for dogpile.cache exceptions to inherit from."""


class RegionAlreadyConfigured(DogpileCacheException):
    """CacheRegion instance is already configured."""


class RegionNotConfigured(DogpileCacheException):
    """CacheRegion instance has not been configured."""


class ValidationError(DogpileCacheException):
    """Error validating a value or option."""


class PluginNotFound(DogpileCacheException):
    """The specified plugin could not be found.

    .. versionadded:: 0.6.4

    """
