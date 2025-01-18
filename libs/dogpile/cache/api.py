from __future__ import annotations

import abc
import enum
import pickle
import time
from typing import Any
from typing import Callable
from typing import cast
from typing import Literal
from typing import Mapping
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Union

from ..util.typing import Self


class NoValue(enum.Enum):
    """Describe a missing cache value.

    The :data:`.NO_VALUE` constant should be used.

    """

    @property
    def payload(self) -> Self:
        return self

    def __repr__(self):
        """Ensure __repr__ is a consistent value in case NoValue is used to
        fill another cache key.

        """
        return "<dogpile.cache.api.NoValue object>"

    def __bool__(self) -> Literal[False]:  # pragma NO COVERAGE
        return False

    NO_VALUE = "NoValue"


NoValueType = Literal[NoValue.NO_VALUE]

NO_VALUE = NoValue.NO_VALUE
"""Value returned from :meth:`.CacheRegion.get` that describes
a  key not present."""

MetaDataType = Mapping[str, Any]


KeyType = str
"""A cache key."""

ValuePayload = Any
"""An object to be placed in the cache against a key."""


KeyManglerType = Callable[[KeyType], KeyType]
Serializer = Callable[[ValuePayload], bytes]
Deserializer = Callable[[bytes], ValuePayload]


class CantDeserializeException(Exception):
    """Exception indicating deserialization failed, and that caching
    should proceed to re-generate a value

    .. versionadded:: 1.2.0

    """


class CacheMutex(abc.ABC):
    """Describes a mutexing object with acquire and release methods.

    This is an abstract base class; any object that has acquire/release
    methods may be used.

    .. versionadded:: 1.1


    .. seealso::

        :meth:`.CacheBackend.get_mutex` - the backend method that optionally
        returns this locking object.

    """

    @abc.abstractmethod
    def acquire(self, wait: bool = True) -> bool:
        """Acquire the mutex.

        :param wait: if True, block until available, else return True/False
         immediately.

        :return: True if the lock succeeded.

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def release(self) -> None:
        """Release the mutex."""

        raise NotImplementedError()

    @abc.abstractmethod
    def locked(self) -> bool:
        """Check if the mutex was acquired.

        :return: true if the lock is acquired.

        .. versionadded:: 1.1.2

        """
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, C):
        return hasattr(C, "acquire") and hasattr(C, "release")


class CachedValue(NamedTuple):
    """Represent a value stored in the cache.

    :class:`.CachedValue` is a two-tuple of
    ``(payload, metadata)``, where ``metadata``
    is dogpile.cache's tracking information (
    currently the creation time).

    """

    payload: ValuePayload
    """the actual cached value."""

    metadata: MetaDataType
    """Metadata dictionary for the cached value.

    Prefer using accessors such as :attr:`.CachedValue.cached_time` rather
    than accessing this mapping directly.

    """

    @property
    def cached_time(self) -> float:
        """The epoch (floating point time value) stored when this payload was
        cached.

        .. versionadded:: 1.3

        """
        return cast(float, self.metadata["ct"])

    @property
    def age(self) -> float:
        """Returns the elapsed time in seconds as a `float` since the insertion
        of the value in the cache.

        This value is computed **dynamically** by subtracting the cached
        floating point epoch value from the value of ``time.time()``.

        .. versionadded:: 1.3

        """
        return time.time() - self.cached_time


CacheReturnType = Union[CachedValue, NoValueType]
"""The non-serialized form of what may be returned from a backend
get method.

"""

SerializedReturnType = Union[bytes, NoValueType]
"""the serialized form of what may be returned from a backend get method."""

BackendFormatted = Union[CacheReturnType, SerializedReturnType]
"""Describes the type returned from the :meth:`.CacheBackend.get` method."""

BackendSetType = Union[CachedValue, bytes]
"""Describes the value argument passed to the :meth:`.CacheBackend.set`
method."""

BackendArguments = Mapping[str, Any]


class CacheBackend:
    """Base class for backend implementations.

    Backends which set and get Python object values should subclass this
    backend.   For backends in which the value that's stored is ultimately
    a stream of bytes, the :class:`.BytesBackend` should be used.

    """

    key_mangler: Optional[Callable[[KeyType], KeyType]] = None
    """Key mangling function.

    May be None, or otherwise declared
    as an ordinary instance method.

    """

    serializer: Union[None, Serializer] = None
    """Serializer function that will be used by default if not overridden
    by the region.

    .. versionadded:: 1.1

    """

    deserializer: Union[None, Deserializer] = None
    """deserializer function that will be used by default if not overridden
    by the region.

    .. versionadded:: 1.1

    """

    def __init__(self, arguments: BackendArguments):  # pragma NO COVERAGE
        """Construct a new :class:`.CacheBackend`.

        Subclasses should override this to
        handle the given arguments.

        :param arguments: The ``arguments`` parameter
         passed to :func:`.make_registry`.

        """
        raise NotImplementedError()

    @classmethod
    def from_config_dict(
        cls, config_dict: Mapping[str, Any], prefix: str
    ) -> Self:
        prefix_len = len(prefix)
        return cls(
            dict(
                (key[prefix_len:], config_dict[key])
                for key in config_dict
                if key.startswith(prefix)
            )
        )

    def has_lock_timeout(self) -> bool:
        return False

    def get_mutex(self, key: KeyType) -> Optional[CacheMutex]:
        """Return an optional mutexing object for the given key.

        This object need only provide an ``acquire()``
        and ``release()`` method.

        May return ``None``, in which case the dogpile
        lock will use a regular ``threading.Lock``
        object to mutex concurrent threads for
        value creation.   The default implementation
        returns ``None``.

        Different backends may want to provide various
        kinds of "mutex" objects, such as those which
        link to lock files, distributed mutexes,
        memcached semaphores, etc.  Whatever
        kind of system is best suited for the scope
        and behavior of the caching backend.

        A mutex that takes the key into account will
        allow multiple regenerate operations across
        keys to proceed simultaneously, while a mutex
        that does not will serialize regenerate operations
        to just one at a time across all keys in the region.
        The latter approach, or a variant that involves
        a modulus of the given key's hash value,
        can be used as a means of throttling the total
        number of value recreation operations that may
        proceed at one time.

        """
        return None

    def get(self, key: KeyType) -> BackendFormatted:  # pragma NO COVERAGE
        """Retrieve an optionally serialized value from the cache.

        :param key: String key that was passed to the :meth:`.CacheRegion.get`
         method, which will also be processed by the "key mangling" function
         if one was present.

        :return: the Python object that corresponds to
         what was established via the :meth:`.CacheBackend.set` method,
         or the :data:`.NO_VALUE` constant if not present.

        If a serializer is in use, this method will only be called if the
        :meth:`.CacheBackend.get_serialized` method is not overridden.

        """
        raise NotImplementedError()

    def get_multi(
        self, keys: Sequence[KeyType]
    ) -> Sequence[BackendFormatted]:  # pragma NO COVERAGE
        """Retrieve multiple optionally serialized values from the cache.

        :param keys: sequence of string keys that was passed to the
         :meth:`.CacheRegion.get_multi` method, which will also be processed
         by the "key mangling" function if one was present.

        :return a list of values as would be returned
         individually via the :meth:`.CacheBackend.get` method, corresponding
         to the list of keys given.

        If a serializer is in use, this method will only be called if the
        :meth:`.CacheBackend.get_serialized_multi` method is not overridden.

        .. versionadded:: 0.5.0

        """
        raise NotImplementedError()

    def get_serialized(self, key: KeyType) -> SerializedReturnType:
        """Retrieve a serialized value from the cache.

        :param key: String key that was passed to the :meth:`.CacheRegion.get`
         method, which will also be processed by the "key mangling" function
         if one was present.

        :return: a bytes object, or :data:`.NO_VALUE`
         constant if not present.

        The default implementation of this method for :class:`.CacheBackend`
        returns the value of the :meth:`.CacheBackend.get` method.

        .. versionadded:: 1.1

        .. seealso::

            :class:`.BytesBackend`

        """
        return cast(SerializedReturnType, self.get(key))

    def get_serialized_multi(
        self, keys: Sequence[KeyType]
    ) -> Sequence[SerializedReturnType]:  # pragma NO COVERAGE
        """Retrieve multiple serialized values from the cache.

        :param keys: sequence of string keys that was passed to the
         :meth:`.CacheRegion.get_multi` method, which will also be processed
         by the "key mangling" function if one was present.

        :return: list of bytes objects

        The default implementation of this method for :class:`.CacheBackend`
        returns the value of the :meth:`.CacheBackend.get_multi` method.

        .. versionadded:: 1.1

        .. seealso::

            :class:`.BytesBackend`

        """
        return cast(Sequence[SerializedReturnType], self.get_multi(keys))

    def set(
        self, key: KeyType, value: BackendSetType
    ) -> None:  # pragma NO COVERAGE
        """Set an optionally serialized value in the cache.

        :param key: String key that was passed to the :meth:`.CacheRegion.set`
         method, which will also be processed by the "key mangling" function
         if one was present.

        :param value: The optionally serialized :class:`.CachedValue` object.
         May be an instance of :class:`.CachedValue` or a bytes object
         depending on if a serializer is in use with the region and if the
         :meth:`.CacheBackend.set_serialized` method is not overridden.

        .. seealso::

            :meth:`.CacheBackend.set_serialized`

        """
        raise NotImplementedError()

    def set_serialized(
        self, key: KeyType, value: bytes
    ) -> None:  # pragma NO COVERAGE
        """Set a serialized value in the cache.

        :param key: String key that was passed to the :meth:`.CacheRegion.set`
         method, which will also be processed by the "key mangling" function
         if one was present.

        :param value: a bytes object to be stored.

        The default implementation of this method for :class:`.CacheBackend`
        calls upon the :meth:`.CacheBackend.set` method.

        .. versionadded:: 1.1

        .. seealso::

            :class:`.BytesBackend`

        """
        self.set(key, value)

    def set_multi(
        self, mapping: Mapping[KeyType, BackendSetType]
    ) -> None:  # pragma NO COVERAGE
        """Set multiple values in the cache.

        :param mapping: a dict in which the key will be whatever was passed to
         the :meth:`.CacheRegion.set_multi` method, processed by the "key
         mangling" function, if any.

        When implementing a new :class:`.CacheBackend` or cutomizing via
        :class:`.ProxyBackend`, be aware that when this method is invoked by
        :meth:`.Region.get_or_create_multi`, the ``mapping`` values are the
        same ones returned to the upstream caller. If the subclass alters the
        values in any way, it must not do so 'in-place' on the ``mapping`` dict
        -- that will have the undesirable effect of modifying the returned
        values as well.

        If a serializer is in use, this method will only be called if the
        :meth:`.CacheBackend.set_serialized_multi` method is not overridden.


        .. versionadded:: 0.5.0

        """
        raise NotImplementedError()

    def set_serialized_multi(
        self, mapping: Mapping[KeyType, bytes]
    ) -> None:  # pragma NO COVERAGE
        """Set multiple serialized values in the cache.

        :param mapping: a dict in which the key will be whatever was passed to
         the :meth:`.CacheRegion.set_multi` method, processed by the "key
         mangling" function, if any.

        When implementing a new :class:`.CacheBackend` or cutomizing via
        :class:`.ProxyBackend`, be aware that when this method is invoked by
        :meth:`.Region.get_or_create_multi`, the ``mapping`` values are the
        same ones returned to the upstream caller. If the subclass alters the
        values in any way, it must not do so 'in-place' on the ``mapping`` dict
        -- that will have the undesirable effect of modifying the returned
        values as well.

        .. versionadded:: 1.1

        The default implementation of this method for :class:`.CacheBackend`
        calls upon the :meth:`.CacheBackend.set_multi` method.

        .. seealso::

            :class:`.BytesBackend`


        """
        self.set_multi(mapping)

    def delete(self, key: KeyType) -> None:  # pragma NO COVERAGE
        """Delete a value from the cache.

        :param key: String key that was passed to the
         :meth:`.CacheRegion.delete`
         method, which will also be processed by the "key mangling" function
         if one was present.

        The behavior here should be idempotent,
        that is, can be called any number of times
        regardless of whether or not the
        key exists.
        """
        raise NotImplementedError()

    def delete_multi(
        self, keys: Sequence[KeyType]
    ) -> None:  # pragma NO COVERAGE
        """Delete multiple values from the cache.

        :param keys: sequence of string keys that was passed to the
         :meth:`.CacheRegion.delete_multi` method, which will also be processed
         by the "key mangling" function if one was present.

        The behavior here should be idempotent,
        that is, can be called any number of times
        regardless of whether or not the
        key exists.

        .. versionadded:: 0.5.0

        """
        raise NotImplementedError()


class DefaultSerialization:
    serializer: Union[None, Serializer] = staticmethod(  # type: ignore
        pickle.dumps
    )
    deserializer: Union[None, Deserializer] = staticmethod(  # type: ignore
        pickle.loads
    )


class BytesBackend(DefaultSerialization, CacheBackend):
    """A cache backend that receives and returns series of bytes.

    This backend only supports the "serialized" form of values; subclasses
    should implement :meth:`.BytesBackend.get_serialized`,
    :meth:`.BytesBackend.get_serialized_multi`,
    :meth:`.BytesBackend.set_serialized`,
    :meth:`.BytesBackend.set_serialized_multi`.

    .. versionadded:: 1.1

    """

    def get_serialized(self, key: KeyType) -> SerializedReturnType:
        """Retrieve a serialized value from the cache.

        :param key: String key that was passed to the :meth:`.CacheRegion.get`
         method, which will also be processed by the "key mangling" function
         if one was present.

        :return: a bytes object, or :data:`.NO_VALUE`
         constant if not present.

        .. versionadded:: 1.1

        """
        raise NotImplementedError()

    def get_serialized_multi(
        self, keys: Sequence[KeyType]
    ) -> Sequence[SerializedReturnType]:  # pragma NO COVERAGE
        """Retrieve multiple serialized values from the cache.

        :param keys: sequence of string keys that was passed to the
         :meth:`.CacheRegion.get_multi` method, which will also be processed
         by the "key mangling" function if one was present.

        :return: list of bytes objects

        .. versionadded:: 1.1

        """
        raise NotImplementedError()

    def set_serialized(
        self, key: KeyType, value: bytes
    ) -> None:  # pragma NO COVERAGE
        """Set a serialized value in the cache.

        :param key: String key that was passed to the :meth:`.CacheRegion.set`
         method, which will also be processed by the "key mangling" function
         if one was present.

        :param value: a bytes object to be stored.

        .. versionadded:: 1.1

        """
        raise NotImplementedError()

    def set_serialized_multi(
        self, mapping: Mapping[KeyType, bytes]
    ) -> None:  # pragma NO COVERAGE
        """Set multiple serialized values in the cache.

        :param mapping: a dict in which the key will be whatever was passed to
         the :meth:`.CacheRegion.set_multi` method, processed by the "key
         mangling" function, if any.

        When implementing a new :class:`.CacheBackend` or cutomizing via
        :class:`.ProxyBackend`, be aware that when this method is invoked by
        :meth:`.Region.get_or_create_multi`, the ``mapping`` values are the
        same ones returned to the upstream caller. If the subclass alters the
        values in any way, it must not do so 'in-place' on the ``mapping`` dict
        -- that will have the undesirable effect of modifying the returned
        values as well.

        .. versionadded:: 1.1

        """
        raise NotImplementedError()
