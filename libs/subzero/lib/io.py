# coding=utf-8

import os
import sys

from scandir import scandir as _scandir

# thanks @ plex trakt scrobbler: https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/Contents/Libraries/Shared/plugin/core/io.py


class FileIO(object):
    @staticmethod
    def exists(path):
        return os.path.exists(path)

    @staticmethod
    def delete(path):
        os.remove(path)

    @staticmethod
    def read(path, mode='r'):
        with open(path, mode) as fp:
            data = fp.read()

        return data

    @staticmethod
    def write(path, data, mode='w'):
        with open(path, mode) as fp:
            fp.write(data)


VALID_ENCODINGS = ("latin1", "utf-8", "mbcs")


def get_viable_encoding():
    # fixme: bad
    encoding = sys.getfilesystemencoding()
    return "utf-8" if not encoding or encoding.lower() not in VALID_ENCODINGS else encoding


class ScandirListdirEntryStub(object):
    """
    A class which mimics the entries returned by scandir, for fallback purposes when using listdir instead.
    """
    __slots__ = ('name', '_d_type', '_stat', '_lstat', '_scandir_path', '_path', '_inode')

    def __init__(self, scandir_path, name, d_type, inode):
        self._scandir_path = scandir_path
        self.name = name
        self._d_type = d_type
        self._inode = inode
        self._stat = None
        self._lstat = None
        self._path = None

    @property
    def path(self):
        if self._path is None:
            self._path = os.path.join(self._scandir_path, self.name)
        return self._path

    def stat(self, follow_symlinks=True):
        path = self.path
        if follow_symlinks and self.is_symlink():
            path = os.path.realpath(path)

        return os.stat(path)

    def is_dir(self, follow_symlinks=True):
        path = self.path
        if follow_symlinks and self.is_symlink():
            path = os.path.realpath(path)

        return os.path.isdir(path)

    def is_file(self, follow_symlinks=True):
        path = self.path
        if follow_symlinks and self.is_symlink():
            path = os.path.realpath(path)

        return os.path.isfile(path)

    def is_symlink(self):
        return os.path.islink(self.path)


def scandir_listdir_fallback(path):
    for fn in os.listdir(path):
        yield ScandirListdirEntryStub(path, fn, None, None)


def scandir(path):
    try:
        return _scandir(path)

    # fallback for systems where sys.getfilesystemencoding() returns the "wrong" value
    except UnicodeDecodeError:
        return scandir_listdir_fallback(path)
