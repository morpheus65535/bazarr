from hashlib import sha1

from ..util import compat
from ..util import langhelpers


def function_key_generator(namespace, fn, to_str=str):
    """Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.

    This is used by :meth:`.CacheRegion.cache_on_arguments`
    to generate a cache key from a decorated function.

    An alternate function may be used by specifying
    the :paramref:`.CacheRegion.function_key_generator` argument
    for :class:`.CacheRegion`.

    .. seealso::

        :func:`.kwarg_function_key_generator` - similar function that also
        takes keyword arguments into account

    """

    if namespace is None:
        namespace = "%s:%s" % (fn.__module__, fn.__name__)
    else:
        namespace = "%s:%s|%s" % (fn.__module__, fn.__name__, namespace)

    args = compat.inspect_getargspec(fn)
    has_self = args[0] and args[0][0] in ("self", "cls")

    def generate_key(*args, **kw):
        if kw:
            raise ValueError(
                "dogpile.cache's default key creation "
                "function does not accept keyword arguments."
            )
        if has_self:
            args = args[1:]

        return namespace + "|" + " ".join(map(to_str, args))

    return generate_key


def function_multi_key_generator(namespace, fn, to_str=str):
    if namespace is None:
        namespace = "%s:%s" % (fn.__module__, fn.__name__)
    else:
        namespace = "%s:%s|%s" % (fn.__module__, fn.__name__, namespace)

    args = compat.inspect_getargspec(fn)
    has_self = args[0] and args[0][0] in ("self", "cls")

    def generate_keys(*args, **kw):
        if kw:
            raise ValueError(
                "dogpile.cache's default key creation "
                "function does not accept keyword arguments."
            )
        if has_self:
            args = args[1:]
        return [namespace + "|" + key for key in map(to_str, args)]

    return generate_keys


def kwarg_function_key_generator(namespace, fn, to_str=str):
    """Return a function that generates a string
    key, based on a given function as well as
    arguments to the returned function itself.

    For kwargs passed in, we will build a dict of
    all argname (key) argvalue (values) including
    default args from the argspec and then
    alphabetize the list before generating the
    key.

    .. versionadded:: 0.6.2

    .. seealso::

        :func:`.function_key_generator` - default key generation function

    """

    if namespace is None:
        namespace = "%s:%s" % (fn.__module__, fn.__name__)
    else:
        namespace = "%s:%s|%s" % (fn.__module__, fn.__name__, namespace)

    argspec = compat.inspect_getargspec(fn)
    default_list = list(argspec.defaults or [])
    # Reverse the list, as we want to compare the argspec by negative index,
    # meaning default_list[0] should be args[-1], which works well with
    # enumerate()
    default_list.reverse()
    # use idx*-1 to create the correct right-lookup index.
    args_with_defaults = dict(
        (argspec.args[(idx * -1)], default)
        for idx, default in enumerate(default_list, 1)
    )
    if argspec.args and argspec.args[0] in ("self", "cls"):
        arg_index_start = 1
    else:
        arg_index_start = 0

    def generate_key(*args, **kwargs):
        as_kwargs = dict(
            [
                (argspec.args[idx], arg)
                for idx, arg in enumerate(
                    args[arg_index_start:], arg_index_start
                )
            ]
        )
        as_kwargs.update(kwargs)
        for arg, val in args_with_defaults.items():
            if arg not in as_kwargs:
                as_kwargs[arg] = val

        argument_values = [as_kwargs[key] for key in sorted(as_kwargs.keys())]
        return namespace + "|" + " ".join(map(to_str, argument_values))

    return generate_key


def sha1_mangle_key(key):
    """a SHA1 key mangler."""

    if isinstance(key, str):
        key = key.encode("utf-8")

    return sha1(key).hexdigest()


def length_conditional_mangler(length, mangler):
    """a key mangler that mangles if the length of the key is
    past a certain threshold.

    """

    def mangle(key):
        if len(key) >= length:
            return mangler(key)
        else:
            return key

    return mangle


# in the 0.6 release these functions were moved to the dogpile.util namespace.
# They are linked here to maintain compatibility with older versions.

coerce_string_conf = langhelpers.coerce_string_conf
KeyReentrantMutex = langhelpers.KeyReentrantMutex
memoized_property = langhelpers.memoized_property
PluginLoader = langhelpers.PluginLoader
to_list = langhelpers.to_list


class repr_obj:
    __slots__ = ("value", "max_chars")

    def __init__(self, value, max_chars=300):
        self.value = value
        self.max_chars = max_chars

    def __eq__(self, other):
        return other.value == self.value

    def __repr__(self):
        rep = repr(self.value)
        lenrep = len(rep)
        if lenrep > self.max_chars:
            segment_length = self.max_chars // 2
            rep = (
                rep[0:segment_length]
                + (
                    " ... (%d characters truncated) ... "
                    % (lenrep - self.max_chars)
                )
                + rep[-segment_length:]
            )
        return rep
