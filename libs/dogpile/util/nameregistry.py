import threading
from typing import Any
from typing import Callable
from typing import MutableMapping
import weakref


class NameRegistry(object):
    """Generates and return an object, keeping it as a
    singleton for a certain identifier for as long as its
    strongly referenced.

    e.g.::

        class MyFoo(object):
            "some important object."
            def __init__(self, identifier):
                self.identifier = identifier

        registry = NameRegistry(MyFoo)

        # thread 1:
        my_foo = registry.get("foo1")

        # thread 2
        my_foo = registry.get("foo1")

    Above, ``my_foo`` in both thread #1 and #2 will
    be *the same object*.   The constructor for
    ``MyFoo`` will be called once, passing the
    identifier ``foo1`` as the argument.

    When thread 1 and thread 2 both complete or
    otherwise delete references to ``my_foo``, the
    object is *removed* from the :class:`.NameRegistry` as
    a result of Python garbage collection.

    :param creator: A function that will create a new
     value, given the identifier passed to the :meth:`.NameRegistry.get`
     method.

    """

    _mutex = threading.RLock()

    def __init__(self, creator: Callable[..., Any]):
        """Create a new :class:`.NameRegistry`."""
        self._values: MutableMapping[str, Any] = weakref.WeakValueDictionary()
        self._mutex = threading.RLock()
        self.creator = creator

    def get(self, identifier: str, *args: Any, **kw: Any) -> Any:
        r"""Get and possibly create the value.

        :param identifier: Hash key for the value.
         If the creation function is called, this identifier
         will also be passed to the creation function.
        :param \*args, \**kw: Additional arguments which will
         also be passed to the creation function if it is
         called.

        """
        try:
            if identifier in self._values:
                return self._values[identifier]
            else:
                return self._sync_get(identifier, *args, **kw)
        except KeyError:
            return self._sync_get(identifier, *args, **kw)

    def _sync_get(self, identifier: str, *args: Any, **kw: Any) -> Any:
        self._mutex.acquire()
        try:
            try:
                if identifier in self._values:
                    return self._values[identifier]
                else:
                    self._values[identifier] = value = self.creator(
                        identifier, *args, **kw
                    )
                    return value
            except KeyError:
                self._values[identifier] = value = self.creator(
                    identifier, *args, **kw
                )
                return value
        finally:
            self._mutex.release()
