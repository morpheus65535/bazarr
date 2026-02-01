from ...util import PluginLoader

_backend_loader = PluginLoader("dogpile.cache")
register_backend = _backend_loader.register

register_backend(
    "dogpile.cache.null", "dogpile.cache.backends.null", "NullBackend"
)
register_backend(
    "dogpile.cache.dbm", "dogpile.cache.backends.file", "DBMBackend"
)
register_backend(
    "dogpile.cache.pylibmc",
    "dogpile.cache.backends.memcached",
    "PylibmcBackend",
)
register_backend(
    "dogpile.cache.bmemcached",
    "dogpile.cache.backends.memcached",
    "BMemcachedBackend",
)
register_backend(
    "dogpile.cache.memcached",
    "dogpile.cache.backends.memcached",
    "MemcachedBackend",
)
register_backend(
    "dogpile.cache.pymemcache",
    "dogpile.cache.backends.memcached",
    "PyMemcacheBackend",
)
register_backend(
    "dogpile.cache.memory", "dogpile.cache.backends.memory", "MemoryBackend"
)
register_backend(
    "dogpile.cache.memory_pickle",
    "dogpile.cache.backends.memory",
    "MemoryPickleBackend",
)
register_backend(
    "dogpile.cache.redis", "dogpile.cache.backends.redis", "RedisBackend"
)
register_backend(
    "dogpile.cache.redis_sentinel",
    "dogpile.cache.backends.redis",
    "RedisSentinelBackend",
)
register_backend(
    "dogpile.cache.redis_cluster",
    "dogpile.cache.backends.redis",
    "RedisClusterBackend",
)
register_backend(
    "dogpile.cache.valkey", "dogpile.cache.backends.valkey", "ValkeyBackend"
)
register_backend(
    "dogpile.cache.valkey_sentinel",
    "dogpile.cache.backends.valkey",
    "ValkeySentinelBackend",
)
register_backend(
    "dogpile.cache.valkey_cluster",
    "dogpile.cache.backends.valkey",
    "ValkeyClusterBackend",
)
