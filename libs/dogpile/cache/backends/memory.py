"""
Memory Backends
---------------

Provides simple dictionary-based backends.

The two backends are :class:`.MemoryBackend` and :class:`.MemoryPickleBackend`;
the latter applies a serialization step to cached values while the former
places the value as given into the dictionary.

"""


from ..api import CacheBackend
from ..api import DefaultSerialization
from ..api import NO_VALUE


class MemoryBackend(CacheBackend):
    """A backend that uses a plain dictionary.

    There is no size management, and values which
    are placed into the dictionary will remain
    until explicitly removed.   Note that
    Dogpile's expiration of items is based on
    timestamps and does not remove them from
    the cache.

    E.g.::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.memory'
        )


    To use a Python dictionary of your choosing,
    it can be passed in with the ``cache_dict``
    argument::

        my_dictionary = {}
        region = make_region().configure(
            'dogpile.cache.memory',
            arguments={
                "cache_dict":my_dictionary
            }
        )


    """

    def __init__(self, arguments):
        self._cache = arguments.pop("cache_dict", {})

    def get(self, key):
        return self._cache.get(key, NO_VALUE)

    def get_multi(self, keys):
        return [self._cache.get(key, NO_VALUE) for key in keys]

    def set(self, key, value):
        self._cache[key] = value

    def set_multi(self, mapping):
        for key, value in mapping.items():
            self._cache[key] = value

    def delete(self, key):
        self._cache.pop(key, None)

    def delete_multi(self, keys):
        for key in keys:
            self._cache.pop(key, None)


class MemoryPickleBackend(DefaultSerialization, MemoryBackend):
    """A backend that uses a plain dictionary, but serializes objects on
    :meth:`.MemoryBackend.set` and deserializes :meth:`.MemoryBackend.get`.

    E.g.::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.memory_pickle'
        )

    The usage of pickle to serialize cached values allows an object
    as placed in the cache to be a copy of the original given object, so
    that any subsequent changes to the given object aren't reflected
    in the cached value, thus making the backend behave the same way
    as other backends which make use of serialization.

    The serialization is performed via pickle, and incurs the same
    performance hit in doing so as that of other backends; in this way
    the :class:`.MemoryPickleBackend` performance is somewhere in between
    that of the pure :class:`.MemoryBackend` and the remote server oriented
    backends such as that of Memcached or Redis.

    Pickle behavior here is the same as that of the Redis backend, using
    either ``cPickle`` or ``pickle`` and specifying ``HIGHEST_PROTOCOL``
    upon serialize.

    .. versionadded:: 0.5.3

    """
