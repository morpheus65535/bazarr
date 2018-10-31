# coding=utf-8
from dogpile.cache.api import CacheBackend, NO_VALUE
from fcache.cache import FileCache


class SZFileBackend(CacheBackend):
    def __init__(self, arguments):
        self._cache = FileCache(arguments.pop("appname", None), flag=arguments.pop("flag", "c"),
                                serialize=arguments.pop("serialize", True),
                                app_cache_dir=arguments.pop("app_cache_dir", None))

    def get(self, key):
        value = self._cache.get(key, NO_VALUE)

        return value

    def get_multi(self, keys):
        ret = [
            self._cache.get(key, NO_VALUE)
            for key in keys]

        return ret

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

    @property
    def all_filenames(self):
        return self._cache._all_filenames()

    def sync(self, force=False):
        if (hasattr(self._cache, "_buffer") and self._cache._buffer) or force:
            self._cache.sync()

    def clear(self):
        self._cache.clear()
        if not hasattr(self._cache, "_buffer") or self._cache._sync:
            self._cache._sync = False
            self._cache._buffer = {}

