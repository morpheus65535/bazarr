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
import bz2
import io
import lzma
import os
import queue
import sys
import threading
from typing import IO, Any, BinaryIO, Dict, List, Optional, Union

from py7zr import UnsupportedCompressionMethodError
from py7zr.extra import AESDecompressor, CopyDecompressor, DeflateDecompressor, ISevenZipDecompressor, ZstdDecompressor
from py7zr.helpers import MemIO, NullIO, calculate_crc32, readlink
from py7zr.properties import READ_BLOCKSIZE, ArchivePassword, CompressionMethod

if sys.version_info < (3, 6):
    import pathlib2 as pathlib
else:
    import pathlib
try:
    import zstandard as Zstd  # type: ignore
except ImportError:
    Zstd = None


class Worker:
    """Extract worker class to invoke handler"""

    def __init__(self, files, src_start: int, header) -> None:
        self.target_filepath = {}  # type: Dict[int, Union[MemIO, pathlib.Path, None]]
        self.files = files
        self.src_start = src_start
        self.header = header

    def extract(self, fp: BinaryIO, parallel: bool, q=None) -> None:
        """Extract worker method to handle 7zip folder and decompress each files."""
        if hasattr(self.header, 'main_streams') and self.header.main_streams is not None:
            src_end = self.src_start + self.header.main_streams.packinfo.packpositions[-1]
            numfolders = self.header.main_streams.unpackinfo.numfolders
            if numfolders == 1:
                self.extract_single(fp, self.files, self.src_start, src_end, q)
            else:
                folders = self.header.main_streams.unpackinfo.folders
                positions = self.header.main_streams.packinfo.packpositions
                empty_files = [f for f in self.files if f.emptystream]
                if not parallel:
                    self.extract_single(fp, empty_files, 0, 0, q)
                    for i in range(numfolders):
                        self.extract_single(fp, folders[i].files, self.src_start + positions[i],
                                            self.src_start + positions[i + 1], q)
                else:
                    filename = getattr(fp, 'name', None)
                    self.extract_single(open(filename, 'rb'), empty_files, 0, 0, q)
                    extract_threads = []
                    for i in range(numfolders):
                        p = threading.Thread(target=self.extract_single,
                                             args=(filename, folders[i].files,
                                                   self.src_start + positions[i], self.src_start + positions[i + 1], q))
                        p.start()
                        extract_threads.append((p))
                    for p in extract_threads:
                        p.join()
        else:
            empty_files = [f for f in self.files if f.emptystream]
            self.extract_single(fp, empty_files, 0, 0, q)

    def extract_single(self, fp: Union[BinaryIO, str], files, src_start: int, src_end: int,
                       q: Optional[queue.Queue]) -> None:
        """Single thread extractor that takes file lists in single 7zip folder."""
        if files is None:
            return
        if isinstance(fp, str):
            fp = open(fp, 'rb')
        fp.seek(src_start)
        for f in files:
            if q is not None:
                q.put(('s', str(f.filename), str(f.compressed) if f.compressed is not None else '0'))
            fileish = self.target_filepath.get(f.id, None)
            if fileish is not None:
                fileish.parent.mkdir(parents=True, exist_ok=True)
                with fileish.open(mode='wb') as ofp:
                    if not f.emptystream:
                        # extract to file
                        self.decompress(fp, f.folder, ofp, f.uncompressed[-1], f.compressed, src_end)
                        ofp.seek(0)
                    else:
                        pass  # just create empty file
            elif not f.emptystream:
                # read and bin off a data but check crc
                with NullIO() as ofp:
                    self.decompress(fp, f.folder, ofp, f.uncompressed[-1], f.compressed, src_end)
            if q is not None:
                q.put(('e', str(f.filename), str(f.uncompressed[-1])))

    def decompress(self, fp: BinaryIO, folder, fq: IO[Any],
                   size: int, compressed_size: Optional[int], src_end: int) -> None:
        """decompressor wrapper called from extract method.

           :parameter fp: archive source file pointer
           :parameter folder: Folder object that have decompressor object.
           :parameter fq: output file pathlib.Path
           :parameter size: uncompressed size of target file.
           :parameter compressed_size: compressed size of target file.
           :parameter src_end: end position of the folder
           :returns None
        """
        assert folder is not None
        out_remaining = size
        decompressor = folder.get_decompressor(compressed_size)
        while out_remaining > 0:
            max_length = min(out_remaining, io.DEFAULT_BUFFER_SIZE)
            rest_size = src_end - fp.tell()
            read_size = min(READ_BLOCKSIZE, rest_size)
            if read_size == 0:
                tmp = decompressor.decompress(b'', max_length)
                if len(tmp) == 0:
                    raise Exception("decompression get wrong: no output data.")
            else:
                inp = fp.read(read_size)
                tmp = decompressor.decompress(inp, max_length)
            if len(tmp) > 0 and out_remaining >= len(tmp):
                out_remaining -= len(tmp)
                fq.write(tmp)
            if out_remaining <= 0:
                break
        if fp.tell() >= src_end:
            if decompressor.crc is not None and not decompressor.check_crc():
                print('\nCRC error! expected: {}, real: {}'.format(decompressor.crc, decompressor.digest))
        return

    def _find_link_target(self, target):
        """Find the target member of a symlink or hardlink member in the archive.
        """
        targetname = target.as_posix()  # type: str
        linkname = readlink(targetname)
        # Check windows full path symlinks
        if linkname.startswith("\\\\?\\"):
            linkname = linkname[4:]
        # normalize as posix style
        linkname = pathlib.Path(linkname).as_posix()  # type: str
        member = None
        for j in range(len(self.files)):
            if linkname == self.files[j].origin.as_posix():
                # FIXME: when API user specify arcname, it will break
                member = os.path.relpath(linkname, os.path.dirname(targetname))
                break
        if member is None:
            member = linkname
        return member

    def archive(self, fp: BinaryIO, folder, deref=False):
        """Run archive task for specified 7zip folder."""
        compressor = folder.get_compressor()
        outsize = 0
        self.header.main_streams.packinfo.numstreams = 1
        num_unpack_streams = 0
        self.header.main_streams.substreamsinfo.digests = []
        self.header.main_streams.substreamsinfo.digestsdefined = []
        last_file_index = 0
        foutsize = 0
        for i, f in enumerate(self.files):
            file_info = f.file_properties()
            self.header.files_info.files.append(file_info)
            self.header.files_info.emptyfiles.append(f.emptystream)
            foutsize = 0
            if f.is_symlink and not deref:
                last_file_index = i
                num_unpack_streams += 1
                link_target = self._find_link_target(f.origin)  # type: str
                tgt = link_target.encode('utf-8')  # type: bytes
                insize = len(tgt)
                crc = calculate_crc32(tgt, 0)  # type: int
                out = compressor.compress(tgt)
                outsize += len(out)
                foutsize += len(out)
                fp.write(out)
                self.header.main_streams.substreamsinfo.digests.append(crc)
                self.header.main_streams.substreamsinfo.digestsdefined.append(True)
                self.header.main_streams.substreamsinfo.unpacksizes.append(insize)
                self.header.files_info.files[i]['maxsize'] = foutsize
            elif not f.emptystream:
                last_file_index = i
                num_unpack_streams += 1
                insize = 0
                with f.origin.open(mode='rb') as fd:
                    data = fd.read(READ_BLOCKSIZE)
                    insize += len(data)
                    crc = 0
                    while data:
                        crc = calculate_crc32(data, crc)
                        out = compressor.compress(data)
                        outsize += len(out)
                        foutsize += len(out)
                        fp.write(out)
                        data = fd.read(READ_BLOCKSIZE)
                        insize += len(data)
                    self.header.main_streams.substreamsinfo.digests.append(crc)
                    self.header.main_streams.substreamsinfo.digestsdefined.append(True)
                    self.header.files_info.files[i]['maxsize'] = foutsize
                self.header.main_streams.substreamsinfo.unpacksizes.append(insize)
        else:
            out = compressor.flush()
            outsize += len(out)
            foutsize += len(out)
            fp.write(out)
            if len(self.files) > 0:
                self.header.files_info.files[last_file_index]['maxsize'] = foutsize
        # Update size data in header
        self.header.main_streams.packinfo.packsizes = [outsize]
        folder.unpacksizes = [sum(self.header.main_streams.substreamsinfo.unpacksizes)]
        self.header.main_streams.substreamsinfo.num_unpackstreams_folders = [num_unpack_streams]

    def register_filelike(self, id: int, fileish: Union[MemIO, pathlib.Path, None]) -> None:
        """register file-ish to worker."""
        self.target_filepath[id] = fileish


class SevenZipDecompressor:
    """Main decompressor object which is properly configured and bind to each 7zip folder.
    because 7zip folder can have a custom compression method"""

    lzma_methods_map = {
        CompressionMethod.LZMA: lzma.FILTER_LZMA1,
        CompressionMethod.LZMA2: lzma.FILTER_LZMA2,
        CompressionMethod.DELTA: lzma.FILTER_DELTA,
        CompressionMethod.P7Z_BCJ: lzma.FILTER_X86,
        CompressionMethod.BCJ_ARM: lzma.FILTER_ARM,
        CompressionMethod.BCJ_ARMT: lzma.FILTER_ARMTHUMB,
        CompressionMethod.BCJ_IA64: lzma.FILTER_IA64,
        CompressionMethod.BCJ_PPC: lzma.FILTER_POWERPC,
        CompressionMethod.BCJ_SPARC: lzma.FILTER_SPARC,
    }

    FILTER_BZIP2 = 0x31
    FILTER_ZIP = 0x32
    FILTER_COPY = 0x33
    FILTER_AES = 0x34
    FILTER_ZSTD = 0x35
    alt_methods_map = {
        CompressionMethod.MISC_BZIP2: FILTER_BZIP2,
        CompressionMethod.MISC_DEFLATE: FILTER_ZIP,
        CompressionMethod.COPY: FILTER_COPY,
        CompressionMethod.CRYPT_AES256_SHA256: FILTER_AES,
        CompressionMethod.MISC_ZSTD: FILTER_ZSTD,
    }

    def __init__(self, coders: List[Dict[str, Any]], size: int, crc: Optional[int]) -> None:
        # Get password which was set when creation of py7zr.SevenZipFile object.
        self.input_size = size
        self.consumed = 0  # type: int
        self.crc = crc
        self.digest = None  # type: Optional[int]
        if self._check_lzma_coders(coders):
            self._set_lzma_decompressor(coders)
        else:
            self._set_alternative_decompressor(coders)

    def _check_lzma_coders(self, coders: List[Dict[str, Any]]) -> bool:
        res = True
        for coder in coders:
            if self.lzma_methods_map.get(coder['method'], None) is None:
                res = False
                break
        return res

    def _set_lzma_decompressor(self, coders: List[Dict[str, Any]]) -> None:
        filters = []  # type: List[Dict[str, Any]]
        for coder in coders:
            if coder['numinstreams'] != 1 or coder['numoutstreams'] != 1:
                raise UnsupportedCompressionMethodError('Only a simple compression method is currently supported.')
            filter_id = self.lzma_methods_map.get(coder['method'], None)
            if filter_id is None:
                raise UnsupportedCompressionMethodError
            properties = coder.get('properties', None)
            if properties is not None:
                filters[:0] = [lzma._decode_filter_properties(filter_id, properties)]  # type: ignore
            else:
                filters[:0] = [{'id': filter_id}]
        self.decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=filters)  # type: Union[bz2.BZ2Decompressor, lzma.LZMADecompressor, ISevenZipDecompressor]  # noqa

    def _set_alternative_decompressor(self, coders: List[Dict[str, Any]]) -> None:
        filter_id = self.alt_methods_map.get(coders[0]['method'], None)
        if filter_id == self.FILTER_BZIP2:
            self.decompressor = bz2.BZ2Decompressor()
        elif filter_id == self.FILTER_ZIP:
            self.decompressor = DeflateDecompressor()
        elif filter_id == self.FILTER_COPY:
            self.decompressor = CopyDecompressor()
        elif filter_id == self.FILTER_ZSTD and Zstd:
            self.decompressor = ZstdDecompressor()
        elif filter_id == self.FILTER_AES:
            password = ArchivePassword().get()
            properties = coders[0].get('properties', None)
            self.decompressor = AESDecompressor(properties, password, coders[1:])
        else:
            raise UnsupportedCompressionMethodError

    def decompress(self, data: bytes, max_length: Optional[int] = None) -> bytes:
        self.consumed += len(data)
        if max_length is not None:
            folder_data = self.decompressor.decompress(data, max_length=max_length)
        else:
            folder_data = self.decompressor.decompress(data)
        # calculate CRC with uncompressed data
        if self.crc is not None:
            self.digest = calculate_crc32(folder_data, self.digest)
        return folder_data

    def check_crc(self):
        return self.crc == self.digest


class SevenZipCompressor:

    """Main compressor object to configured for each 7zip folder."""

    __slots__ = ['filters', 'compressor', 'coders']

    lzma_methods_map_r = {
        lzma.FILTER_LZMA2: CompressionMethod.LZMA2,
        lzma.FILTER_DELTA: CompressionMethod.DELTA,
        lzma.FILTER_X86: CompressionMethod.P7Z_BCJ,
    }

    def __init__(self, filters=None):
        if filters is None:
            self.filters = [{"id": lzma.FILTER_LZMA2, "preset": 7 | lzma.PRESET_EXTREME}, ]
        else:
            self.filters = filters
        self.compressor = lzma.LZMACompressor(format=lzma.FORMAT_RAW, filters=self.filters)
        self.coders = []
        for filter in self.filters:
            if filter is None:
                break
            method = self.lzma_methods_map_r[filter['id']]
            properties = lzma._encode_filter_properties(filter)
            self.coders.append({'method': method, 'properties': properties, 'numinstreams': 1, 'numoutstreams': 1})

    def compress(self, data):
        return self.compressor.compress(data)

    def flush(self):
        return self.compressor.flush()


def get_methods_names(coders: List[dict]) -> List[str]:
    """Return human readable method names for specified coders"""
    methods_name_map = {
        CompressionMethod.LZMA2: "LZMA2",
        CompressionMethod.LZMA: "LZMA",
        CompressionMethod.DELTA: "delta",
        CompressionMethod.P7Z_BCJ: "BCJ",
        CompressionMethod.BCJ_ARM: "BCJ(ARM)",
        CompressionMethod.BCJ_ARMT: "BCJ(ARMT)",
        CompressionMethod.BCJ_IA64: "BCJ(IA64)",
        CompressionMethod.BCJ_PPC: "BCJ(POWERPC)",
        CompressionMethod.BCJ_SPARC: "BCJ(SPARC)",
        CompressionMethod.CRYPT_AES256_SHA256: "7zAES",
    }
    methods_names = []  # type: List[str]
    for coder in coders:
        try:
            methods_names.append(methods_name_map[coder['method']])
        except KeyError:
            raise UnsupportedCompressionMethodError("Unknown method {}".format(coder['method']))
    return methods_names
