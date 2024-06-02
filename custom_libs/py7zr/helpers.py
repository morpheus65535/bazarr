#!/usr/bin/python -u
#
# p7zr library
#
# Copyright (c) 2019 Hiroshi Miura <miurahr@linux.com>
# Copyright (c) 2004-2015 by Joachim Bauch, mail@joachim-bauch.de
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#

import _hashlib  # type: ignore  # noqa
import ctypes
import os
import pathlib
import platform
import sys
import time as _time
import zlib
from datetime import datetime, timedelta, timezone, tzinfo
from typing import BinaryIO, Optional, Union

import py7zr.win32compat


def calculate_crc32(data: bytes, value: Optional[int] = None, blocksize: int = 1024 * 1024) -> int:
    """Calculate CRC32 of strings with arbitrary lengths."""
    length = len(data)
    pos = blocksize
    if value:
        value = zlib.crc32(data[:pos], value)
    else:
        value = zlib.crc32(data[:pos])
    while pos < length:
        value = zlib.crc32(data[pos:pos + blocksize], value)
        pos += blocksize

    return value & 0xffffffff


def _calculate_key1(password: bytes, cycles: int, salt: bytes, digest: str) -> bytes:
    """Calculate 7zip AES encryption key."""
    if digest not in ('sha256'):
        raise ValueError('Unknown digest method for password protection.')
    assert cycles <= 0x3f
    if cycles == 0x3f:
        ba = bytearray(salt + password + bytes(32))
        key = bytes(ba[:32])  # type: bytes
    else:
        rounds = 1 << cycles
        m = _hashlib.new(digest)
        for round in range(rounds):
            m.update(salt + password + round.to_bytes(8, byteorder='little', signed=False))
        key = m.digest()[:32]
    return key


def _calculate_key2(password: bytes, cycles: int, salt: bytes, digest: str):
    """Calculate 7zip AES encryption key.
    It utilize ctypes and memoryview buffer and zero-copy technology on Python."""
    if digest not in ('sha256'):
        raise ValueError('Unknown digest method for password protection.')
    assert cycles <= 0x3f
    if cycles == 0x3f:
        key = bytes(bytearray(salt + password + bytes(32))[:32])  # type: bytes
    else:
        rounds = 1 << cycles
        m = _hashlib.new(digest)
        length = len(salt) + len(password)

        class RoundBuf(ctypes.LittleEndianStructure):
            _pack_ = 1
            _fields_ = [
                ('saltpassword', ctypes.c_ubyte * length),
                ('round', ctypes.c_uint64)
            ]

        buf = RoundBuf()
        for i, c in enumerate(salt + password):
            buf.saltpassword[i] = c
        buf.round = 0
        mv = memoryview(buf)  # type: ignore # noqa
        while buf.round < rounds:
            m.update(mv)
            buf.round += 1
        key = m.digest()[:32]
    return key


if platform.python_implementation() == "PyPy":
    calculate_key = _calculate_key1  # Avoid https://foss.heptapod.net/pypy/pypy/issues/3209
else:
    calculate_key = _calculate_key2  # ver2 is 1.7-2.0 times faster than ver1


def filetime_to_dt(ft):
    """Convert Windows NTFS file time into python datetime object."""
    EPOCH_AS_FILETIME = 116444736000000000
    us = (ft - EPOCH_AS_FILETIME) // 10
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=us)


ZERO = timedelta(0)
HOUR = timedelta(hours=1)
SECOND = timedelta(seconds=1)

# A class capturing the platform's idea of local time.
# (May result in wrong values on historical times in
#  timezones where UTC offset and/or the DST rules had
#  changed in the past.)

STDOFFSET = timedelta(seconds=-_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds=-_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET


class LocalTimezone(tzinfo):

    def fromutc(self, dt):
        assert dt.tzinfo is self
        stamp = (dt - datetime(1970, 1, 1, tzinfo=self)) // SECOND
        args = _time.localtime(stamp)[:6]
        dst_diff = DSTDIFF // SECOND
        # Detect fold
        fold = (args == _time.localtime(stamp - dst_diff))
        return datetime(*args, microsecond=dt.microsecond, tzinfo=self)

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0


Local = LocalTimezone()
TIMESTAMP_ADJUST = -11644473600


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

    def _call__(self):
        return self


class ArchiveTimestamp(int):
    """Windows FILETIME timestamp."""

    def __repr__(self):
        return '%s(%d)' % (type(self).__name__, self)

    def totimestamp(self) -> float:
        """Convert 7z FILETIME to Python timestamp."""
        # FILETIME is 100-nanosecond intervals since 1601/01/01 (UTC)
        return (self / 10000000.0) + TIMESTAMP_ADJUST

    def as_datetime(self):
        """Convert FILETIME to Python datetime object."""
        return datetime.fromtimestamp(self.totimestamp(), UTC())

    @staticmethod
    def from_datetime(val):
        return ArchiveTimestamp((val - TIMESTAMP_ADJUST) * 10000000.0)


def islink(path):
    """
    Cross-platform islink implementation.
    Supports Windows NT symbolic links and reparse points.
    """
    is_symlink = os.path.islink(path)
    if sys.version_info >= (3, 8) or sys.platform != "win32" or sys.getwindowsversion()[0] < 6:
        return is_symlink
    # special check for directory junctions which py38 does.
    if is_symlink:
        if py7zr.win32compat.is_reparse_point(path):
            is_symlink = False
    return is_symlink


def readlink(path: Union[str, pathlib.Path], *, dir_fd=None) -> Union[str, pathlib.Path]:
    """
    Cross-platform compat implementation of os.readlink and Path.readlink().
    Supports Windows NT symbolic links and reparse points.
    When called with path argument as pathlike(str), return result as a pathlike(str).
    When called with Path object, return also Path object.
    When called with path argument as bytes, return result as a bytes.
    """
    is_path_pathlib = isinstance(path, pathlib.Path)
    if sys.version_info >= (3, 9):
        if is_path_pathlib and dir_fd is None:
            return path.readlink()
        else:
            return os.readlink(path, dir_fd=dir_fd)
    elif sys.version_info >= (3, 8) or sys.platform != "win32":
        res = os.readlink(path, dir_fd=dir_fd)
        # Hack to handle a wrong type of results
        if isinstance(res, bytes):
            res = os.fsdecode(res)
        if is_path_pathlib:
            return pathlib.Path(res)
        else:
            return res
    elif not os.path.exists(str(path)):
        raise OSError(22, 'Invalid argument', path)
    return py7zr.win32compat.readlink(path)


class MemIO:
    """pathlib.Path-like IO class to write memory(io.Bytes)"""
    def __init__(self, buf: BinaryIO):
        self._buf = buf

    def write(self, data: bytes) -> int:
        return self._buf.write(data)

    def read(self, length: Optional[int] = None) -> bytes:
        if length is not None:
            return self._buf.read(length)
        else:
            return self._buf.read()

    def close(self) -> None:
        self._buf.seek(0)

    def flush(self) -> None:
        pass

    def seek(self, position: int) -> None:
        self._buf.seek(position)

    def open(self, mode=None):
        return self

    @property
    def parent(self):
        return self

    def mkdir(self, parents=None, exist_ok=False):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class NullIO:
    """pathlib.Path-like IO class of /dev/null"""

    def __init__(self):
        pass

    def write(self, data):
        return len(data)

    def read(self, length=None):
        if length is not None:
            return bytes(length)
        else:
            return b''

    def close(self):
        pass

    def flush(self):
        pass

    def open(self, mode=None):
        return self

    @property
    def parent(self):
        return self

    def mkdir(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class BufferOverflow(Exception):
    pass


class Buffer:

    def __init__(self, size: int = 16):
        self._size = size
        self._buf = bytearray(size)
        self._buflen = 0
        self.view = memoryview(self._buf[0:0])

    def add(self, data: Union[bytes, bytearray, memoryview]):
        length = len(data)
        if length + self._buflen > self._size:
            raise BufferOverflow()
        self._buf[self._buflen:self._buflen + length] = data
        self._buflen += length
        self.view = memoryview(self._buf[0:self._buflen])

    def reset(self) -> None:
        self._buflen = 0
        self.view = memoryview(self._buf[0:0])

    def set(self, data: Union[bytes, bytearray, memoryview]) -> None:
        length = len(data)
        if length > self._size:
            raise BufferOverflow()
        self._buf[0:length] = data
        self._buflen = length
        self.view = memoryview(self._buf[0:length])

    def __len__(self) -> int:
        return self._buflen
