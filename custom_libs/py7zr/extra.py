#!/usr/bin/python -u
#
# p7zr library
#
# Copyright (c) 2019 Hiroshi Miura <miurahr@linux.com>
# Copyright (c) 2004-2015 by Joachim Bauch, mail@joachim-bauch.de
# 7-Zip Copyright (C) 1999-2010 Igor Pavlov
# LZMA SDK Copyright (C) 1999-2010 Igor Pavlov
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
import lzma
import zlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from py7zr import UnsupportedCompressionMethodError
from py7zr.helpers import Buffer, calculate_key
from py7zr.properties import READ_BLOCKSIZE, CompressionMethod

try:
    import zstandard as Zstd  # type: ignore
except ImportError:
    Zstd = None


class ISevenZipCompressor(ABC):
    @abstractmethod
    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        pass

    @abstractmethod
    def flush(self) -> bytes:
        pass


class ISevenZipDecompressor(ABC):
    @abstractmethod
    def decompress(self, data: Union[bytes, bytearray, memoryview], max_length: int = -1) -> bytes:
        pass


class DeflateDecompressor(ISevenZipDecompressor):
    def __init__(self):
        self.buf = b''
        self._decompressor = zlib.decompressobj(-15)

    def decompress(self, data: Union[bytes, bytearray, memoryview], max_length: int = -1):
        if max_length < 0:
            res = self.buf + self._decompressor.decompress(data)
            self.buf = b''
        else:
            tmp = self.buf + self._decompressor.decompress(data)
            res = tmp[:max_length]
            self.buf = tmp[max_length:]
        return res


class CopyDecompressor(ISevenZipDecompressor):

    def __init__(self):
        self._buf = bytes()

    def decompress(self, data: Union[bytes, bytearray, memoryview], max_length: int = -1) -> bytes:
        if max_length < 0:
            length = len(data)
        else:
            length = min(len(data), max_length)
        buflen = len(self._buf)
        if length > buflen:
            res = self._buf + data[:length - buflen]
            self._buf = data[length - buflen:]
        else:
            res = self._buf[:length]
            self._buf = self._buf[length:] + data
        return res


class ZstdDecompressor(ISevenZipDecompressor):

    def __init__(self):
        if Zstd is None:
            raise UnsupportedCompressionMethodError
        self.buf = b''  # type: bytes
        self._ctc = Zstd.ZstdDecompressor()  # type: ignore

    def decompress(self, data: Union[bytes, bytearray, memoryview], max_length: int = -1) -> bytes:
        dobj = self._ctc.decompressobj()  # type: ignore
        if max_length < 0:
            res = self.buf + dobj.decompress(data)
            self.buf = b''
        else:
            tmp = self.buf + dobj.decompress(data)
            res = tmp[:max_length]
            self.buf = tmp[max_length:]
        return res


class ZstdCompressor(ISevenZipCompressor):

    def __init__(self):
        if Zstd is None:
            raise UnsupportedCompressionMethodError
        self._ctc = Zstd.ZstdCompressor()  # type: ignore

    def compress(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        return self._ctc.compress(data)  # type: ignore

    def flush(self):
        pass
