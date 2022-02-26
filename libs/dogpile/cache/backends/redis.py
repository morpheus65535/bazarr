"""
Redis Backends
------------------

Provides backends for talking to `Redis <http://redis.io>`_.

"""

from __future__ import absolute_import

import typing
import warnings

from ..api import BytesBackend
from ..api import NO_VALUE

if typing.TYPE_CHECKING:
    import redis
else:
    # delayed import
    redis = None  # noqa F811

__all__ = ("RedisBackend", "RedisSentinelBackend")


class RedisBackend(BytesBackend):
    """A `Redis <http://redis.io/>`_ backend, using the
    `redis-py <http://pypi.python.org/pypi/redis/>`_ backend.

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.redis',
            arguments = {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'redis_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True,
                'thread_local_lock': False
                }
        )


    Arguments accepted in the arguments dictionary:

    :param url: string. If provided, will override separate host/port/db
     params.  The format is that accepted by ``StrictRedis.from_url()``.

    :param host: string, default is ``localhost``.

    :param password: string, default is no password.

    :param port: integer, default is ``6379``.

    :param db: integer, default is ``0``.

    :param redis_expiration_time: integer, number of seconds after setting
     a value that Redis should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     redis-lock as the dogpile lock. Use this when multiple processes will be
     talking to the same redis instance. When left at False, dogpile will
     coordinate on a regular threading mutex.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     Redis should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param connection_pool: ``redis.ConnectionPool`` object.  If provided,
     this object supersedes other connection arguments passed to the
     ``redis.StrictRedis`` instance, including url and/or host as well as
     socket_timeout, and will be passed to ``redis.StrictRedis`` as the
     source of connectivity.

    :param thread_local_lock: bool, whether a thread-local Redis lock object
     should be used. This is the default, but is not compatible with
     asynchronous runners, as they run in a different thread than the one
     used to create the lock.

    """

    def __init__(self, arguments):
        arguments = arguments.copy()
        self._imports()
        self.url = arguments.pop("url", None)
        self.host = arguments.pop("host", "localhost")
        self.password = arguments.pop("password", None)
        self.port = arguments.pop("port", 6379)
        self.db = arguments.pop("db", 0)
        self.distributed_lock = arguments.get("distributed_lock", False)
        self.socket_timeout = arguments.pop("socket_timeout", None)

        self.lock_timeout = arguments.get("lock_timeout", None)
        self.lock_sleep = arguments.get("lock_sleep", 0.1)
        self.thread_local_lock = arguments.get("thread_local_lock", True)

        if self.distributed_lock and self.thread_local_lock:
            warnings.warn(
                "The Redis backend thread_local_lock parameter should be "
                "set to False when distributed_lock is True"
            )

        self.redis_expiration_time = arguments.pop("redis_expiration_time", 0)
        self.connection_pool = arguments.get("connection_pool", None)
        self._create_client()

    def _imports(self):
        # defer imports until backend is used
        global redis
        import redis  # noqa

    def _create_client(self):
        if self.connection_pool is not None:
            # the connection pool already has all other connection
            # options present within, so here we disregard socket_timeout
            # and others.
            self.writer_client = redis.StrictRedis(
                connection_pool=self.connection_pool
            )
            self.reader_client = self.writer_client
        else:
            args = {}
            if self.socket_timeout:
                args["socket_timeout"] = self.socket_timeout

            if self.url is not None:
                args.update(url=self.url)
                self.writer_client = redis.StrictRedis.from_url(**args)
                self.reader_client = self.writer_client
            else:
                args.update(
                    host=self.host,
                    password=self.password,
                    port=self.port,
                    db=self.db,
                )
                self.writer_client = redis.StrictRedis(**args)
                self.reader_client = self.writer_client

    def get_mutex(self, key):
        if self.distributed_lock:
            return self.writer_client.lock(
                "_lock{0}".format(key),
                timeout=self.lock_timeout,
                sleep=self.lock_sleep,
                thread_local=self.thread_local_lock,
            )
        else:
            return None

    def get_serialized(self, key):
        value = self.reader_client.get(key)
        if value is None:
            return NO_VALUE
        return value

    def get_serialized_multi(self, keys):
        if not keys:
            return []
        values = self.reader_client.mget(keys)
        return [v if v is not None else NO_VALUE for v in values]

    def set_serialized(self, key, value):
        if self.redis_expiration_time:
            self.writer_client.setex(key, self.redis_expiration_time, value)
        else:
            self.writer_client.set(key, value)

    def set_serialized_multi(self, mapping):
        if not self.redis_expiration_time:
            self.writer_client.mset(mapping)
        else:
            pipe = self.writer_client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, self.redis_expiration_time, value)
            pipe.execute()

    def delete(self, key):
        self.writer_client.delete(key)

    def delete_multi(self, keys):
        self.writer_client.delete(*keys)


class RedisSentinelBackend(RedisBackend):
    """A `Redis <http://redis.io/>`_ backend, using the
    `redis-py <http://pypi.python.org/pypi/redis/>`_ backend.
    It will use the Sentinel of a Redis cluster.

    .. versionadded:: 1.0.0

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.redis_sentinel',
            arguments = {
                'sentinels': [
                    ['redis_sentinel_1', 26379],
                    ['redis_sentinel_2', 26379]
                ],
                'db': 0,
                'redis_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True,
                'thread_local_lock': False
            }
        )


    Arguments accepted in the arguments dictionary:

    :param db: integer, default is ``0``.

    :param redis_expiration_time: integer, number of seconds after setting
     a value that Redis should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     redis-lock as the dogpile lock. Use this when multiple processes will be
     talking to the same redis instance. When False, dogpile will
     coordinate on a regular threading mutex, Default is True.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     Redis should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

    :param sentinels: is a list of sentinel nodes. Each node is represented by
     a pair (hostname, port).
     Default is None (not in sentinel mode).

    :param service_name: str, the service name.
     Default is 'mymaster'.

    :param sentinel_kwargs: is a dictionary of connection arguments used when
     connecting to sentinel instances. Any argument that can be passed to
     a normal Redis connection can be specified here.
     Default is {}.

    :param connection_kwargs: dict, are keyword arguments that will be used
     when establishing a connection to a Redis server.
     Default is {}.

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

    :param thread_local_lock: bool, whether a thread-local Redis lock object
     should be used. This is the default, but is not compatible with
     asynchronous runners, as they run in a different thread than the one
     used to create the lock.

    """

    def __init__(self, arguments):
        arguments = arguments.copy()

        self.sentinels = arguments.pop("sentinels", None)
        self.service_name = arguments.pop("service_name", "mymaster")
        self.sentinel_kwargs = arguments.pop("sentinel_kwargs", {})
        self.connection_kwargs = arguments.pop("connection_kwargs", {})

        super().__init__(
            arguments={
                "distributed_lock": True,
                "thread_local_lock": False,
                **arguments,
            }
        )

    def _imports(self):
        # defer imports until backend is used
        global redis
        import redis.sentinel  # noqa

    def _create_client(self):
        sentinel_kwargs = {}
        sentinel_kwargs.update(self.sentinel_kwargs)
        sentinel_kwargs.setdefault("password", self.password)

        connection_kwargs = {}
        connection_kwargs.update(self.connection_kwargs)
        connection_kwargs.setdefault("password", self.password)

        if self.db is not None:
            connection_kwargs.setdefault("db", self.db)
            sentinel_kwargs.setdefault("db", self.db)
        if self.socket_timeout is not None:
            connection_kwargs.setdefault("socket_timeout", self.socket_timeout)

        sentinel = redis.sentinel.Sentinel(
            self.sentinels,
            sentinel_kwargs=sentinel_kwargs,
            **connection_kwargs,
        )
        self.writer_client = sentinel.master_for(self.service_name)
        self.reader_client = sentinel.slave_for(self.service_name)
