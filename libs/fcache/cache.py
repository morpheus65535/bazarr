import codecs
from collections.abc import MutableMapping
import logging
import os
import pickle
import shutil
import tempfile

import platformdirs

from .posixemulation import rename

logger = logging.getLogger(__name__)


class FileCache(MutableMapping):
    """A persistent file cache that is dictionary-like and has a write buffer.

    *appname* is passed to `platformdirs <https://pypi.org/project/platformdirs/>`_
    to determine a system-appropriate location for the cache files. The cache
    directory used is available via :data:`cache_dir`.

    By default, a write buffer is used, so writing to cache files is not done
    until :meth:`sync` is explicitly called. This behavior can be changed using
    the optional *flag* argument.

    .. NOTE::
        Keys and values are always stored as :class:`bytes` objects. If data
        serialization is enabled, keys are returned as :class:`str` objects.
        If data serialization is disabled, keys are returned as a
        :class:`bytes` object.

    :param str appname: The app/script the cache should be associated with.
    :param str flag: How the cache should be opened. See below for details.
    :param mode: The Unix mode for the cache files or False to prevent changing
        permissions.
    :param str keyencoding: The encoding the keys use, defaults to 'utf-8'.
        This is used if *serialize* is ``False``; the keys are treated as
        :class:`bytes` objects.
    :param bool serialize: Whether or not to (de)serialize the values. If a
        cache is used with a :class:`~shelve.Shelf`, set this to ``False``.
    :param str app_cache_dir: absolute path to root cache directory to be
        used in place of system-appropriate location determined by platformdirs

    The optional *flag* argument can be:

    +---------+-------------------------------------------+
    | Value   | Meaning                                   |
    +=========+===========================================+
    | ``'r'`` | Open existing cache for reading only      |
    +---------+-------------------------------------------+
    | ``'w'`` | Open existing cache for reading and       |
    |         | writing                                   |
    +---------+-------------------------------------------+
    | ``'c'`` | Open cache for reading and writing,       |
    |         | creating it if it doesn't exist (default) |
    +---------+-------------------------------------------+
    | ``'n'`` | Always create a new, empty cache, open    |
    |         | for reading and writing                   |
    +---------+-------------------------------------------+

    If a ``'s'`` is appended to the *flag* argument, the cache will be opened
    in sync mode. Writing to the cache will happen immediately and will not be
    buffered.

    If an application needs to use more than one cache, then it should use
    subcaches. To create a subcache, append a series of one or more names
    separated by periods to the application name when creating a
    :class:`FileCache` object (e.g. ``'appname.subcache'`` or
    ``'appname.subcache.subcache'``).
    Subcaches are a way for an application to use more than one cache without
    polluting a user's cache directory. All caches -- main caches or subcaches
    -- are totally independent. The only aspect in which they are linked is
    that all of an application's caches exist in the same system directory.
    Because each cache is independent of every other cache, calling
    :meth:`delete` on an application's main cache will not delete data in
    its subcaches.

    """

    def __init__(
        self,
        appname,
        flag="c",
        mode=0o666,
        keyencoding="utf-8",
        serialize=True,
        app_cache_dir=None,
    ):
        """Initialize a :class:`FileCache` object."""
        if not isinstance(flag, str):
            raise TypeError("flag must be str not '{}'".format(type(flag)))
        elif flag[0] not in "rwcn":
            raise ValueError(
                "invalid flag: '{}', first flag must be one of "
                "'r', 'w', 'c' or 'n'".format(flag)
            )
        elif len(flag) > 1 and flag[1] != "s":
            raise ValueError(
                "invalid flag: '{}', second flag must be " "'s'".format(flag)
            )

        appname, subcache = self._parse_appname(appname)
        if "cache" in subcache:
            raise ValueError("invalid subcache name: 'cache'.")
        self._is_subcache = bool(subcache)

        if not app_cache_dir:
            app_cache_dir = platformdirs.user_cache_dir(appname, appname)
        subcache_dir = os.path.join(app_cache_dir, *subcache)
        self.cache_dir = os.path.join(subcache_dir, "cache")
        exists = os.path.exists(self.cache_dir)

        if len(flag) > 1 and flag[1] == "s":
            self._sync = True
        else:
            self._sync = False
            self._buffer = {}

        if exists and "n" in flag:
            self.clear()
            self.create()
        elif not exists and ("c" in flag or "n" in flag):
            self.create()
        elif not exists:
            raise FileNotFoundError("no such directory: '{}'".format(self.cache_dir))

        self._flag = "rb" if "r" in flag else "wb"
        self._mode = mode
        self._keyencoding = keyencoding
        self._serialize = serialize

    def _parse_appname(self, appname):
        """Splits an appname into the appname and subcache components."""
        components = appname.split(".")
        return components[0], components[1:]

    def create(self):
        """Create the write buffer and cache directory."""
        if not self._sync and not hasattr(self, "_buffer"):
            self._buffer = {}
        os.makedirs(self.cache_dir, exist_ok=True)

    def clear(self):
        """Remove all items from the write buffer and cache.

        The write buffer object and cache directory are not deleted.

        """
        self.delete()
        self.create()

    def delete(self):
        """Delete the write buffer and cache directory."""
        if not self._sync:
            del self._buffer

        # Allow multiple processes to delete() at the same time,
        # meaning some or all of cache_dir may already be deleted
        def _on_error(function, path, excinfo):
            if excinfo[0] != FileNotFoundError:
                raise

        shutil.rmtree(self.cache_dir, onerror=_on_error)

    def close(self):
        """Sync the write buffer, then close the cache.

        If a closed :class:`FileCache` object's methods are called, a
        :exc:`ValueError` will be raised.

        """
        self.sync()
        self.sync = self.create = self.delete = self._closed
        self._write_to_file = self._read_to_file = self._closed
        self._key_to_filename = self._filename_to_key = self._closed
        self.__getitem__ = self.__setitem__ = self.__delitem__ = self._closed
        self.__iter__ = self.__len__ = self.__contains__ = self._closed

    def sync(self):
        """Sync the write buffer with the cache files and clear the buffer.

        If the :class:`FileCache` object was opened with the optional ``'s'``
        *flag* argument, then calling :meth:`sync` will do nothing.
        """
        if self._sync:
            return  # opened in sync mode, so skip the manual sync
        self._sync = True
        for ekey in self._buffer:
            filename = self._key_to_filename(ekey)
            self._write_to_file(filename, self._buffer[ekey])
        self._buffer.clear()
        self._sync = False

    def _closed(self, *args, **kwargs):
        """Filler method for closed cache methods."""
        raise ValueError("invalid operation on closed cache")

    def _encode_key(self, key):
        """Encode key using *hex_codec* for constructing a cache filename.

        Keys are implicitly converted to :class:`bytes` if passed as
        :class:`str`.

        """
        if isinstance(key, str):
            key = key.encode(self._keyencoding)
        elif not isinstance(key, bytes):
            raise TypeError("key must be bytes or str")
        return codecs.encode(key, "hex_codec").decode(self._keyencoding)

    def _decode_key(self, key):
        """Decode key using hex_codec to retrieve the original key.

        Keys are returned as :class:`str` if serialization is enabled.
        Keys are returned as :class:`bytes` if serialization is disabled.

        """
        bkey = codecs.decode(key.encode(self._keyencoding), "hex_codec")
        return bkey.decode(self._keyencoding) if self._serialize else bkey

    def _dumps(self, value):
        return value if not self._serialize else pickle.dumps(value)

    def _loads(self, value):
        return value if not self._serialize else pickle.loads(value)

    def _key_to_filename(self, key):
        """Convert an encoded key to an absolute cache filename."""
        return os.path.join(self.cache_dir, key)

    def _filename_to_key(self, absfilename):
        """Convert an absolute cache filename to a key name."""
        return os.path.split(absfilename)[1]

    def _all_filenames(self):
        """Return a list of absolute cache filenames"""
        try:
            return [
                os.path.join(self.cache_dir, filename)
                for filename in os.listdir(self.cache_dir)
            ]
        except (FileNotFoundError, OSError):
            return []

    def _all_keys(self):
        """Return a list of all encoded key names."""
        file_keys = [self._filename_to_key(fn) for fn in self._all_filenames()]
        if self._sync:
            return set(file_keys)
        else:
            return set(file_keys + list(self._buffer))

    def _write_to_file(self, filename, bytesvalue):
        """Write bytesvalue to filename."""
        fh, tmp = tempfile.mkstemp()
        with os.fdopen(fh, self._flag) as f:
            f.write(self._dumps(bytesvalue))
        rename(tmp, filename)
        if self._mode:
            os.chmod(filename, self._mode)

    def _read_from_file(self, filename):
        """Read data from filename."""
        with open(filename, "rb") as f:
            return self._loads(f.read())

    def __setitem__(self, key, value):
        ekey = self._encode_key(key)
        if not self._sync:
            self._buffer[ekey] = value
        else:
            filename = self._key_to_filename(ekey)
            self._write_to_file(filename, value)

    def __getitem__(self, key):
        ekey = self._encode_key(key)
        if not self._sync:
            try:
                return self._buffer[ekey]
            except KeyError:
                pass
        filename = self._key_to_filename(ekey)
        if filename not in self._all_filenames():
            raise KeyError(key)
        return self._read_from_file(filename)

    def __delitem__(self, key):
        ekey = self._encode_key(key)
        found_in_buffer = hasattr(self, "_buffer") and ekey in self._buffer
        if not self._sync:
            try:
                del self._buffer[ekey]
            except KeyError:
                pass
        filename = self._key_to_filename(ekey)
        if filename in self._all_filenames():
            os.remove(filename)
        elif not found_in_buffer:
            raise KeyError(key)

    def __iter__(self):
        for key in self._all_keys():
            yield self._decode_key(key)

    def __len__(self):
        return len(self._all_keys())

    def __contains__(self, key):
        ekey = self._encode_key(key)
        return ekey in self._all_keys()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()
