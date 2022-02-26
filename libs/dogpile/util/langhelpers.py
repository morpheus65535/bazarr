import abc
import collections
import re
import threading
from typing import MutableMapping
from typing import MutableSet

import stevedore


def coerce_string_conf(d):
    result = {}
    for k, v in d.items():
        if not isinstance(v, str):
            result[k] = v
            continue

        v = v.strip()
        if re.match(r"^[-+]?\d+$", v):
            result[k] = int(v)
        elif re.match(r"^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?$", v):
            result[k] = float(v)
        elif v.lower() in ("false", "true"):
            result[k] = v.lower() == "true"
        elif v == "None":
            result[k] = None
        else:
            result[k] = v
    return result


class PluginLoader:
    def __init__(self, group):
        self.group = group
        self.impls = {}  # loaded plugins
        self._mgr = None  # lazily defined stevedore manager
        self._unloaded = {}  # plugins registered but not loaded

    def load(self, name):
        if name in self._unloaded:
            self.impls[name] = self._unloaded[name]()
            return self.impls[name]
        if name in self.impls:
            return self.impls[name]
        else:  # pragma NO COVERAGE
            if self._mgr is None:
                self._mgr = stevedore.ExtensionManager(self.group)
            try:
                self.impls[name] = self._mgr[name].plugin
                return self.impls[name]
            except KeyError:
                raise self.NotFound(
                    "Can't load plugin %s %s" % (self.group, name)
                )

    def register(self, name, modulepath, objname):
        def load():
            mod = __import__(modulepath, fromlist=[objname])
            return getattr(mod, objname)

        self._unloaded[name] = load

    class NotFound(Exception):
        """The specified plugin could not be found."""


class memoized_property:
    """A read-only @property that is only evaluated once."""

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


def to_list(x, default=None):
    """Coerce to a list."""
    if x is None:
        return default
    if not isinstance(x, (list, tuple)):
        return [x]
    else:
        return x


class Mutex(abc.ABC):
    @abc.abstractmethod
    def acquire(self, wait: bool = True) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def release(self) -> None:
        raise NotImplementedError()


class KeyReentrantMutex:
    def __init__(
        self,
        key: str,
        mutex: Mutex,
        keys: MutableMapping[int, MutableSet[str]],
    ):
        self.key = key
        self.mutex = mutex
        self.keys = keys

    @classmethod
    def factory(cls, mutex):
        # this collection holds zero or one
        # thread idents as the key; a set of
        # keynames held as the value.
        keystore: MutableMapping[
            int, MutableSet[str]
        ] = collections.defaultdict(set)

        def fac(key):
            return KeyReentrantMutex(key, mutex, keystore)

        return fac

    def acquire(self, wait=True):
        current_thread = threading.get_ident()
        keys = self.keys.get(current_thread)
        if keys is not None and self.key not in keys:
            # current lockholder, new key. add it in
            keys.add(self.key)
            return True
        elif self.mutex.acquire(wait=wait):
            # after acquire, create new set and add our key
            self.keys[current_thread].add(self.key)
            return True
        else:
            return False

    def release(self):
        current_thread = threading.get_ident()
        keys = self.keys.get(current_thread)
        assert keys is not None, "this thread didn't do the acquire"
        assert self.key in keys, "No acquire held for key '%s'" % self.key
        keys.remove(self.key)
        if not keys:
            # when list of keys empty, remove
            # the thread ident and unlock.
            del self.keys[current_thread]
            self.mutex.release()

    def locked(self):
        current_thread = threading.get_ident()
        keys = self.keys.get(current_thread)
        if keys is None:
            return False
        return self.key in keys
