#!/usr/bin/python -u
#
# p7zr library
#
# Copyright (c) 2019,2020 Hiroshi Miura <miurahr@linux.com>
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
#
"""Read 7zip format archives."""
import collections.abc
import datetime
import errno
import functools
import io
import operator
import os
import queue
import stat
import sys
import threading
from io import BytesIO
from typing import IO, Any, BinaryIO, Dict, List, Optional, Tuple, Union

from py7zr.archiveinfo import Folder, Header, SignatureHeader
from py7zr.callbacks import ExtractCallback
from py7zr.compression import SevenZipCompressor, Worker, get_methods_names
from py7zr.exceptions import Bad7zFile, InternalError
from py7zr.helpers import ArchiveTimestamp, MemIO, calculate_crc32, filetime_to_dt
from py7zr.properties import MAGIC_7Z, READ_BLOCKSIZE, ArchivePassword

if sys.version_info < (3, 6):
    import contextlib2 as contextlib
    import pathlib2 as pathlib
else:
    import contextlib
    import pathlib

if sys.platform.startswith('win'):
    import _winapi

FILE_ATTRIBUTE_UNIX_EXTENSION = 0x8000
FILE_ATTRIBUTE_WINDOWS_MASK = 0x04fff


class ArchiveFile:
    """Represent each files metadata inside archive file.
    It holds file properties; filename, permissions, and type whether
    it is directory, link or normal file.

    Instances of the :class:`ArchiveFile` class are returned by iterating :attr:`files_list` of
    :class:`SevenZipFile` objects.
    Each object stores information about a single member of the 7z archive. Most of users use :meth:`extractall()`.

    The class also hold an archive parameter where file is exist in
    archive file folder(container)."""
    def __init__(self, id: int, file_info: Dict[str, Any]) -> None:
        self.id = id
        self._file_info = file_info

    def file_properties(self) -> Dict[str, Any]:
        """Return file properties as a hash object. Following keys are included: ‘readonly’, ‘is_directory’,
        ‘posix_mode’, ‘archivable’, ‘emptystream’, ‘filename’, ‘creationtime’, ‘lastaccesstime’,
        ‘lastwritetime’, ‘attributes’
        """
        properties = self._file_info
        if properties is not None:
            properties['readonly'] = self.readonly
            properties['posix_mode'] = self.posix_mode
            properties['archivable'] = self.archivable
            properties['is_directory'] = self.is_directory
        return properties

    def _get_property(self, key: str) -> Any:
        try:
            return self._file_info[key]
        except KeyError:
            return None

    @property
    def origin(self) -> pathlib.Path:
        return self._get_property('origin')

    @property
    def folder(self) -> Folder:
        return self._get_property('folder')

    @property
    def filename(self) -> str:
        """return filename of archive file."""
        return self._get_property('filename')

    @property
    def emptystream(self) -> bool:
        """True if file is empty(0-byte file), otherwise False"""
        return self._get_property('emptystream')

    @property
    def uncompressed(self) -> List[int]:
        return self._get_property('uncompressed')

    @property
    def uncompressed_size(self) -> int:
        """Uncompressed file size."""
        return functools.reduce(operator.add, self.uncompressed)

    @property
    def compressed(self) -> Optional[int]:
        """Compressed size"""
        return self._get_property('compressed')

    def _test_attribute(self, target_bit: int) -> bool:
        attributes = self._get_property('attributes')
        if attributes is None:
            return False
        return attributes & target_bit == target_bit

    @property
    def archivable(self) -> bool:
        """File has a Windows `archive` flag."""
        return self._test_attribute(stat.FILE_ATTRIBUTE_ARCHIVE)  # type: ignore  # noqa

    @property
    def is_directory(self) -> bool:
        """True if file is a directory, otherwise False."""
        return self._test_attribute(stat.FILE_ATTRIBUTE_DIRECTORY)  # type: ignore  # noqa

    @property
    def readonly(self) -> bool:
        """True if file is readonly, otherwise False."""
        return self._test_attribute(stat.FILE_ATTRIBUTE_READONLY)  # type: ignore  # noqa

    def _get_unix_extension(self) -> Optional[int]:
        attributes = self._get_property('attributes')
        if self._test_attribute(FILE_ATTRIBUTE_UNIX_EXTENSION):
            return attributes >> 16
        return None

    @property
    def is_symlink(self) -> bool:
        """True if file is a symbolic link, otherwise False."""
        e = self._get_unix_extension()
        if e is not None:
            return stat.S_ISLNK(e)
        return self._test_attribute(stat.FILE_ATTRIBUTE_REPARSE_POINT)  # type: ignore  # noqa

    @property
    def is_junction(self) -> bool:
        """True if file is a junction/reparse point on windows, otherwise False."""
        return self._test_attribute(stat.FILE_ATTRIBUTE_REPARSE_POINT |  # type: ignore  # noqa
                                    stat.FILE_ATTRIBUTE_DIRECTORY)  # type: ignore  # noqa

    @property
    def is_socket(self) -> bool:
        """True if file is a socket, otherwise False."""
        e = self._get_unix_extension()
        if e is not None:
            return stat.S_ISSOCK(e)
        return False

    @property
    def lastwritetime(self) -> Optional[ArchiveTimestamp]:
        """Return last written timestamp of a file."""
        return self._get_property('lastwritetime')

    @property
    def posix_mode(self) -> Optional[int]:
        """
        posix mode when a member has a unix extension property, or None
        :return: Return file stat mode can be set by os.chmod()
        """
        e = self._get_unix_extension()
        if e is not None:
            return stat.S_IMODE(e)
        return None

    @property
    def st_fmt(self) -> Optional[int]:
        """
        :return: Return the portion of the file mode that describes the file type
        """
        e = self._get_unix_extension()
        if e is not None:
            return stat.S_IFMT(e)
        return None


class ArchiveFileList(collections.abc.Iterable):
    """Iteratable container of ArchiveFile."""

    def __init__(self, offset: int = 0):
        self.files_list = []  # type: List[dict]
        self.index = 0
        self.offset = offset

    def append(self, file_info: Dict[str, Any]) -> None:
        self.files_list.append(file_info)

    def __len__(self) -> int:
        return len(self.files_list)

    def __iter__(self) -> 'ArchiveFileListIterator':
        return ArchiveFileListIterator(self)

    def __getitem__(self, index):
        if index > len(self.files_list):
            raise IndexError
        if index < 0:
            raise IndexError
        res = ArchiveFile(index + self.offset, self.files_list[index])
        return res


class ArchiveFileListIterator(collections.abc.Iterator):

    def __init__(self, archive_file_list):
        self._archive_file_list = archive_file_list
        self._index = 0

    def __next__(self) -> ArchiveFile:
        if self._index == len(self._archive_file_list):
            raise StopIteration
        res = self._archive_file_list[self._index]
        self._index += 1
        return res


# ------------------
# Exported Classes
# ------------------
class ArchiveInfo:
    """Hold archive information"""

    def __init__(self, filename, size, header_size, method_names, solid, blocks, uncompressed):
        self.filename = filename
        self.size = size
        self.header_size = header_size
        self.method_names = method_names
        self.solid = solid
        self.blocks = blocks
        self.uncompressed = uncompressed


class FileInfo:
    """Hold archived file information."""

    def __init__(self, filename, compressed, uncompressed, archivable, is_directory, creationtime):
        self.filename = filename
        self.compressed = compressed
        self.uncompressed = uncompressed
        self.archivable = archivable
        self.is_directory = is_directory
        self.creationtime = creationtime


class SevenZipFile(contextlib.AbstractContextManager):
    """The SevenZipFile Class provides an interface to 7z archives."""

    def __init__(self, file: Union[BinaryIO, str, pathlib.Path], mode: str = 'r',
                 *, filters: Optional[str] = None, dereference=False, password: Optional[str] = None) -> None:
        if mode not in ('r', 'w', 'x', 'a'):
            raise ValueError("ZipFile requires mode 'r', 'w', 'x', or 'a'")
        if password is not None:
            if mode not in ('r'):
                raise NotImplementedError("It has not been implemented to create archive with password.")
            ArchivePassword(password)
            self.password_protected = True
        else:
            self.password_protected = False
        # Check if we were passed a file-like object or not
        if isinstance(file, str):
            self._filePassed = False  # type: bool
            self.filename = file  # type: str
            if mode == 'r':
                self.fp = open(file, 'rb')  # type: BinaryIO
            elif mode == 'w':
                self.fp = open(file, 'w+b')
            elif mode == 'x':
                self.fp = open(file, 'x+b')
            elif mode == 'a':
                self.fp = open(file, 'r+b')
            else:
                raise ValueError("File open error.")
            self.mode = mode
        elif isinstance(file, pathlib.Path):
            self._filePassed = False
            self.filename = str(file)
            if mode == 'r':
                self.fp = file.open(mode='rb')  # type: ignore  # noqa   # typeshed issue: 2911
            elif mode == 'w':
                self.fp = file.open(mode='w+b')  # type: ignore  # noqa
            elif mode == 'x':
                self.fp = file.open(mode='x+b')  # type: ignore  # noqa
            elif mode == 'a':
                self.fp = file.open(mode='r+b')  # type: ignore  # noqa
            else:
                raise ValueError("File open error.")
            self.mode = mode
        elif isinstance(file, io.IOBase):
            self._filePassed = True
            self.fp = file
            self.filename = getattr(file, 'name', None)
            self.mode = mode  # type: ignore  #noqa
        else:
            raise TypeError("invalid file: {}".format(type(file)))
        self._fileRefCnt = 1
        try:
            if mode == "r":
                self._real_get_contents(self.fp)
                self._reset_worker()
            elif mode in 'w':
                # FIXME: check filters here
                self.folder = self._create_folder(filters)
                self.files = ArchiveFileList()
                self._prepare_write()
                self._reset_worker()
            elif mode in 'x':
                raise NotImplementedError
            elif mode == 'a':
                raise NotImplementedError
            else:
                raise ValueError("Mode must be 'r', 'w', 'x', or 'a'")
        except Exception as e:
            self._fpclose()
            raise e
        self.encoded_header_mode = False
        self._dict = {}  # type: Dict[str, IO[Any]]
        self.dereference = dereference
        self.reporterd = None  # type: Optional[threading.Thread]
        self.q = queue.Queue()  # type: queue.Queue[Any]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create_folder(self, filters):
        folder = Folder()
        folder.compressor = SevenZipCompressor(filters)
        folder.coders = folder.compressor.coders
        folder.solid = True
        folder.digestdefined = False
        folder.bindpairs = []
        folder.totalin = 1
        folder.totalout = 1
        return folder

    def _fpclose(self) -> None:
        assert self._fileRefCnt > 0
        self._fileRefCnt -= 1
        if not self._fileRefCnt and not self._filePassed:
            self.fp.close()

    def _real_get_contents(self, fp: BinaryIO) -> None:
        if not self._check_7zfile(fp):
            raise Bad7zFile('not a 7z file')
        self.sig_header = SignatureHeader.retrieve(self.fp)
        self.afterheader = self.fp.tell()
        buffer = self._read_header_data()
        header = Header.retrieve(self.fp, buffer, self.afterheader)
        if header is None:
            return
        self.header = header
        buffer.close()
        self.files = ArchiveFileList()
        if getattr(self.header, 'files_info', None) is not None:
            self._filelist_retrieve()

    def _read_header_data(self) -> BytesIO:
        self.fp.seek(self.sig_header.nextheaderofs, os.SEEK_CUR)
        buffer = io.BytesIO(self.fp.read(self.sig_header.nextheadersize))
        if self.sig_header.nextheadercrc != calculate_crc32(buffer.getvalue()):
            raise Bad7zFile('invalid header data')
        return buffer

    class ParseStatus:
        def __init__(self, src_pos=0):
            self.src_pos = src_pos
            self.folder = 0  # 7zip folder where target stored
            self.outstreams = 0  # output stream count
            self.input = 0  # unpack stream count in each folder
            self.stream = 0  # target input stream position

    def _gen_filename(self) -> str:
        # compressed file is stored without a name, generate one
        try:
            basefilename = self.filename
        except AttributeError:
            # 7z archive file doesn't have a name
            return 'contents'
        else:
            if basefilename is not None:
                fn, ext = os.path.splitext(os.path.basename(basefilename))
                return fn
            else:
                return 'contents'

    def _get_fileinfo_sizes(self, pstat, subinfo, packinfo, folder, packsizes, unpacksizes, file_in_solid, numinstreams):
        if pstat.input == 0:
            folder.solid = subinfo.num_unpackstreams_folders[pstat.folder] > 1
        maxsize = (folder.solid and packinfo.packsizes[pstat.stream]) or None
        uncompressed = unpacksizes[pstat.outstreams]
        if not isinstance(uncompressed, (list, tuple)):
            uncompressed = [uncompressed] * len(folder.coders)
        if file_in_solid > 0:
            compressed = None
        elif pstat.stream < len(packsizes):  # file is compressed
            compressed = packsizes[pstat.stream]
        else:  # file is not compressed
            compressed = uncompressed
        packsize = packsizes[pstat.stream:pstat.stream + numinstreams]
        return maxsize, compressed, uncompressed, packsize, folder.solid

    def _filelist_retrieve(self) -> None:
        # Initialize references for convenience
        if hasattr(self.header, 'main_streams') and self.header.main_streams is not None:
            folders = self.header.main_streams.unpackinfo.folders
            packinfo = self.header.main_streams.packinfo
            subinfo = self.header.main_streams.substreamsinfo
            packsizes = packinfo.packsizes
            unpacksizes = subinfo.unpacksizes if subinfo.unpacksizes is not None else [x.unpacksizes for x in folders]
        else:
            subinfo = None
            folders = None
            packinfo = None
            packsizes = []
            unpacksizes = [0]

        pstat = self.ParseStatus()
        pstat.src_pos = self.afterheader
        file_in_solid = 0

        for file_id, file_info in enumerate(self.header.files_info.files):
            if not file_info['emptystream'] and folders is not None:
                folder = folders[pstat.folder]
                numinstreams = max([coder.get('numinstreams', 1) for coder in folder.coders])
                (maxsize, compressed, uncompressed,
                 packsize, solid) = self._get_fileinfo_sizes(pstat, subinfo, packinfo, folder, packsizes,
                                                             unpacksizes, file_in_solid, numinstreams)
                pstat.input += 1
                folder.solid = solid
                file_info['folder'] = folder
                file_info['maxsize'] = maxsize
                file_info['compressed'] = compressed
                file_info['uncompressed'] = uncompressed
                file_info['packsizes'] = packsize
                if subinfo.digestsdefined[pstat.outstreams]:
                    file_info['digest'] = subinfo.digests[pstat.outstreams]
                if folder is None:
                    pstat.src_pos += file_info['compressed']
                else:
                    if folder.solid:
                        file_in_solid += 1
                    pstat.outstreams += 1
                    if folder.files is None:
                        folder.files = ArchiveFileList(offset=file_id)
                    folder.files.append(file_info)
                    if pstat.input >= subinfo.num_unpackstreams_folders[pstat.folder]:
                        file_in_solid = 0
                        pstat.src_pos += sum(packinfo.packsizes[pstat.stream:pstat.stream + numinstreams])
                        pstat.folder += 1
                        pstat.stream += numinstreams
                        pstat.input = 0
            else:
                file_info['folder'] = None
                file_info['maxsize'] = 0
                file_info['compressed'] = 0
                file_info['uncompressed'] = [0]
                file_info['packsizes'] = [0]

            if 'filename' not in file_info:
                file_info['filename'] = self._gen_filename()
            self.files.append(file_info)

    def _num_files(self) -> int:
        if getattr(self.header, 'files_info', None) is not None:
            return len(self.header.files_info.files)
        return 0

    def _set_file_property(self, outfilename: pathlib.Path, properties: Dict[str, Any]) -> None:
        # creation time
        creationtime = ArchiveTimestamp(properties['lastwritetime']).totimestamp()
        if creationtime is not None:
            os.utime(str(outfilename), times=(creationtime, creationtime))
        if os.name == 'posix':
            st_mode = properties['posix_mode']
            if st_mode is not None:
                outfilename.chmod(st_mode)
                return
        # fallback: only set readonly if specified
        if properties['readonly'] and not properties['is_directory']:
            ro_mask = 0o777 ^ (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
            outfilename.chmod(outfilename.stat().st_mode & ro_mask)

    def _reset_decompressor(self) -> None:
        if self.header.main_streams is not None and self.header.main_streams.unpackinfo.numfolders > 0:
            for i, folder in enumerate(self.header.main_streams.unpackinfo.folders):
                folder.decompressor = None

    def _reset_worker(self) -> None:
        """Seek to where archive data start in archive and recreate new worker."""
        self.fp.seek(self.afterheader)
        self.worker = Worker(self.files, self.afterheader, self.header)

    def set_encoded_header_mode(self, mode: bool) -> None:
        self.encoded_header_mode = mode

    @staticmethod
    def _check_7zfile(fp: Union[BinaryIO, io.BufferedReader]) -> bool:
        result = MAGIC_7Z == fp.read(len(MAGIC_7Z))[:len(MAGIC_7Z)]
        fp.seek(-len(MAGIC_7Z), 1)
        return result

    def _get_method_names(self) -> str:
        methods_names = []  # type: List[str]
        for folder in self.header.main_streams.unpackinfo.folders:
            methods_names += get_methods_names(folder.coders)
        return ', '.join(x for x in methods_names)

    def _test_digest_raw(self, pos: int, size: int, crc: int) -> bool:
        self.fp.seek(pos)
        remaining_size = size
        digest = None
        while remaining_size > 0:
            block = min(READ_BLOCKSIZE, remaining_size)
            digest = calculate_crc32(self.fp.read(block), digest)
            remaining_size -= block
        return digest == crc

    def _test_pack_digest(self) -> bool:
        self._reset_worker()
        crcs = self.header.main_streams.packinfo.crcs
        if crcs is not None and len(crcs) > 0:
            # check packed stream's crc
            for i, p in enumerate(self.header.main_streams.packinfo.packpositions):
                if not self._test_digest_raw(p, self.header.main_streams.packinfo.packsizes[i], crcs[i]):
                    return False
        return True

    def _test_unpack_digest(self) -> bool:
        self._reset_worker()
        for f in self.files:
            self.worker.register_filelike(f.id, None)
        try:
            self.worker.extract(self.fp, parallel=(not self.password_protected))  # TODO: print progress
        except Bad7zFile:
            return False
        else:
            return True

    def _test_digests(self) -> bool:
        if self._test_pack_digest():
            if self._test_unpack_digest():
                return True
        return False

    def _prepare_write(self) -> None:
        self.sig_header = SignatureHeader()
        self.sig_header._write_skelton(self.fp)
        self.afterheader = self.fp.tell()
        self.folder.totalin = 1
        self.folder.totalout = 1
        self.folder.bindpairs = []
        self.folder.unpacksizes = []
        self.header = Header.build_header([self.folder])

    def _write_archive(self):
        self.worker.archive(self.fp, self.folder, deref=self.dereference)
        # Write header and update signature header
        (header_pos, header_len, header_crc) = self.header.write(self.fp, self.afterheader,
                                                                 encoded=self.encoded_header_mode)
        self.sig_header.nextheaderofs = header_pos - self.afterheader
        self.sig_header.calccrc(header_len, header_crc)
        self.sig_header.write(self.fp)
        return

    def _is_solid(self):
        for f in self.header.main_streams.substreamsinfo.num_unpackstreams_folders:
            if f > 1:
                return True
        return False

    def _var_release(self):
        self._dict = None
        self.files = None
        self.folder = None
        self.header = None
        self.worker = None
        self.sig_header = None

    @staticmethod
    def _make_file_info(target: pathlib.Path, arcname: Optional[str] = None, dereference=False) -> Dict[str, Any]:
        f = {}  # type: Dict[str, Any]
        f['origin'] = target
        if arcname is not None:
            f['filename'] = pathlib.Path(arcname).as_posix()
        else:
            f['filename'] = target.as_posix()
        if os.name == 'nt':
            fstat = target.lstat()
            if target.is_symlink():
                if dereference:
                    fstat = target.stat()
                    if stat.S_ISDIR(fstat.st_mode):
                        f['emptystream'] = True
                        f['attributes'] = fstat.st_file_attributes & FILE_ATTRIBUTE_WINDOWS_MASK  # type: ignore  # noqa
                    else:
                        f['emptystream'] = False
                        f['attributes'] = stat.FILE_ATTRIBUTE_ARCHIVE  # type: ignore  # noqa
                        f['uncompressed'] = fstat.st_size
                else:
                    f['emptystream'] = False
                    f['attributes'] = fstat.st_file_attributes & FILE_ATTRIBUTE_WINDOWS_MASK  # type: ignore  # noqa
                    # f['attributes'] |= stat.FILE_ATTRIBUTE_REPARSE_POINT  # type: ignore  # noqa
            elif target.is_dir():
                f['emptystream'] = True
                f['attributes'] = fstat.st_file_attributes & FILE_ATTRIBUTE_WINDOWS_MASK  # type: ignore  # noqa
            elif target.is_file():
                f['emptystream'] = False
                f['attributes'] = stat.FILE_ATTRIBUTE_ARCHIVE  # type: ignore  # noqa
                f['uncompressed'] = fstat.st_size
        else:
            fstat = target.lstat()
            if target.is_symlink():
                if dereference:
                    fstat = target.stat()
                    if stat.S_ISDIR(fstat.st_mode):
                        f['emptystream'] = True
                        f['attributes'] = stat.FILE_ATTRIBUTE_DIRECTORY  # type: ignore  # noqa
                        f['attributes'] |= FILE_ATTRIBUTE_UNIX_EXTENSION | (stat.S_IFDIR << 16)
                        f['attributes'] |= (stat.S_IMODE(fstat.st_mode) << 16)
                    else:
                        f['emptystream'] = False
                        f['attributes'] = stat.FILE_ATTRIBUTE_ARCHIVE  # type: ignore  # noqa
                        f['attributes'] |= FILE_ATTRIBUTE_UNIX_EXTENSION | (stat.S_IMODE(fstat.st_mode) << 16)
                else:
                    f['emptystream'] = False
                    f['attributes'] = stat.FILE_ATTRIBUTE_ARCHIVE | stat.FILE_ATTRIBUTE_REPARSE_POINT # type: ignore  # noqa
                    f['attributes'] |= FILE_ATTRIBUTE_UNIX_EXTENSION | (stat.S_IFLNK << 16)
                    f['attributes'] |= (stat.S_IMODE(fstat.st_mode) << 16)
            elif target.is_dir():
                f['emptystream'] = True
                f['attributes'] = stat.FILE_ATTRIBUTE_DIRECTORY  # type: ignore  # noqa
                f['attributes'] |= FILE_ATTRIBUTE_UNIX_EXTENSION | (stat.S_IFDIR << 16)
                f['attributes'] |= (stat.S_IMODE(fstat.st_mode) << 16)
            elif target.is_file():
                f['emptystream'] = False
                f['uncompressed'] = fstat.st_size
                f['attributes'] = stat.FILE_ATTRIBUTE_ARCHIVE  # type: ignore  # noqa
                f['attributes'] |= FILE_ATTRIBUTE_UNIX_EXTENSION | (stat.S_IMODE(fstat.st_mode) << 16)

        f['creationtime'] = fstat.st_ctime
        f['lastwritetime'] = fstat.st_mtime
        f['lastaccesstime'] = fstat.st_atime
        return f

    # --------------------------------------------------------------------------
    # The public methods which SevenZipFile provides:
    def getnames(self) -> List[str]:
        """Return the members of the archive as a list of their names. It has
           the same order as the list returned by getmembers().
        """
        return list(map(lambda x: x.filename, self.files))

    def archiveinfo(self) -> ArchiveInfo:
        fstat = os.stat(self.filename)
        uncompressed = 0
        for f in self.files:
            uncompressed += f.uncompressed_size
        return ArchiveInfo(self.filename, fstat.st_size, self.header.size, self._get_method_names(),
                           self._is_solid(), len(self.header.main_streams.unpackinfo.folders),
                           uncompressed)

    def list(self) -> List[FileInfo]:
        """Returns contents information """
        alist = []  # type: List[FileInfo]
        creationtime = None  # type: Optional[datetime.datetime]
        for f in self.files:
            if f.lastwritetime is not None:
                creationtime = filetime_to_dt(f.lastwritetime)
            alist.append(FileInfo(f.filename, f.compressed, f.uncompressed_size, f.archivable, f.is_directory,
                                  creationtime))
        return alist

    def test(self) -> bool:
        """Test archive using CRC digests."""
        return self._test_digests()

    def readall(self) -> Optional[Dict[str, IO[Any]]]:
        return self._extract(path=None, return_dict=True)

    def extractall(self, path: Optional[Any] = None, callback: Optional[ExtractCallback] = None) -> None:
        """Extract all members from the archive to the current working
           directory and set owner, modification time and permissions on
           directories afterwards. `path' specifies a different directory
           to extract to.
        """
        self._extract(path=path, return_dict=False, callback=callback)

    def read(self, targets: Optional[List[str]] = None) -> Optional[Dict[str, IO[Any]]]:
        return self._extract(path=None, targets=targets, return_dict=True)

    def extract(self, path: Optional[Any] = None, targets: Optional[List[str]] = None) -> None:
        self._extract(path, targets, return_dict=False)

    def _extract(self, path: Optional[Any] = None, targets: Optional[List[str]] = None,
                 return_dict: bool = False, callback: Optional[ExtractCallback] = None) -> Optional[Dict[str, IO[Any]]]:
        if callback is not None and not isinstance(callback, ExtractCallback):
            raise ValueError('Callback specified is not a subclass of py7zr.callbacks.ExtractCallback class')
        elif callback is not None:
            self.reporterd = threading.Thread(target=self.reporter, args=(callback,), daemon=True)
            self.reporterd.start()
        target_junction = []  # type: List[pathlib.Path]
        target_sym = []  # type: List[pathlib.Path]
        target_files = []  # type: List[Tuple[pathlib.Path, Dict[str, Any]]]
        target_dirs = []  # type: List[pathlib.Path]
        if path is not None:
            if isinstance(path, str):
                path = pathlib.Path(path)
            try:
                if not path.exists():
                    path.mkdir(parents=True)
                else:
                    pass
            except OSError as e:
                if e.errno == errno.EEXIST and path.is_dir():
                    pass
                else:
                    raise e
        fnames = []  # type: List[str]  # check duplicated filename in one archive?
        self.q.put(('pre', None, None))
        for f in self.files:
            # TODO: sanity check
            # check whether f.filename with invalid characters: '../'
            if f.filename.startswith('../'):
                raise Bad7zFile
            # When archive has a multiple files which have same name
            # To guarantee order of archive, multi-thread decompression becomes off.
            # Currently always overwrite by latter archives.
            # TODO: provide option to select overwrite or skip.
            if f.filename not in fnames:
                outname = f.filename
            else:
                i = 0
                while True:
                    outname = f.filename + '_%d' % i
                    if outname not in fnames:
                        break
            fnames.append(outname)
            if path is not None:
                outfilename = path.joinpath(outname)
            else:
                outfilename = pathlib.Path(outname)
            if os.name == 'nt':
                if outfilename.is_absolute():
                    # hack for microsoft windows path length limit < 255
                    outfilename = pathlib.WindowsPath('\\\\?\\' + str(outfilename))
            if targets is not None and f.filename not in targets:
                self.worker.register_filelike(f.id, None)
                continue
            if f.is_directory:
                if not outfilename.exists():
                    target_dirs.append(outfilename)
                    target_files.append((outfilename, f.file_properties()))
                else:
                    pass
            elif f.is_socket:
                pass
            elif return_dict:
                fname = outfilename.as_posix()
                _buf = io.BytesIO()
                self._dict[fname] = _buf
                self.worker.register_filelike(f.id, MemIO(_buf))
            elif f.is_symlink:
                target_sym.append(outfilename)
                try:
                    if outfilename.exists():
                        outfilename.unlink()
                except OSError as ose:
                    if ose.errno not in [errno.ENOENT]:
                        raise
                self.worker.register_filelike(f.id, outfilename)
            elif f.is_junction:
                target_junction.append(outfilename)
                self.worker.register_filelike(f.id, outfilename)
            else:
                self.worker.register_filelike(f.id, outfilename)
                target_files.append((outfilename, f.file_properties()))
        for target_dir in sorted(target_dirs):
            try:
                target_dir.mkdir()
            except FileExistsError:
                if target_dir.is_dir():
                    # skip rare case
                    pass
                elif target_dir.is_file():
                    raise Exception("Directory name is existed as a normal file.")
                else:
                    raise Exception("Directory making fails on unknown condition.")

        if callback is not None:
            self.worker.extract(self.fp, parallel=(not self.password_protected and not self._filePassed), q=self.q)
        else:
            self.worker.extract(self.fp, parallel=(not self.password_protected and not self._filePassed))

        self.q.put(('post', None, None))
        if return_dict:
            return self._dict
        else:
            # create symbolic links on target path as a working directory.
            # if path is None, work on current working directory.
            for t in target_sym:
                sym_dst = t.resolve()
                with sym_dst.open('rb') as b:
                    sym_src = b.read().decode(encoding='utf-8')  # symlink target name stored in utf-8
                sym_dst.unlink()  # unlink after close().
                sym_dst.symlink_to(pathlib.Path(sym_src))
            # create junction point only on windows platform
            if sys.platform.startswith('win'):
                for t in target_junction:
                    junction_dst = t.resolve()
                    with junction_dst.open('rb') as b:
                        junction_target = pathlib.Path(b.read().decode(encoding='utf-8'))
                        junction_dst.unlink()
                        _winapi.CreateJunction(junction_target, str(junction_dst))  # type: ignore  # noqa
            # set file properties
            for o, p in target_files:
                self._set_file_property(o, p)
            return None

    def reporter(self, callback: ExtractCallback):
        while True:
            try:
                item: Optional[Tuple[str, str, str]] = self.q.get(timeout=1)
            except queue.Empty:
                pass
            else:
                if item is None:
                    break
                elif item[0] == 's':
                    callback.report_start(item[1], item[2])
                elif item[0] == 'e':
                    callback.report_end(item[1], item[2])
                elif item[0] == 'pre':
                    callback.report_start_preparation()
                elif item[0] == 'post':
                    callback.report_postprocess()
                elif item[0] == 'w':
                    callback.report_warning(item[1])
                else:
                    pass
                self.q.task_done()

    def writeall(self, path: Union[pathlib.Path, str], arcname: Optional[str] = None):
        """Write files in target path into archive."""
        if isinstance(path, str):
            path = pathlib.Path(path)
        if not path.exists():
            raise ValueError("specified path does not exist.")
        if path.is_dir() or path.is_file():
            self._writeall(path, arcname)
        else:
            raise ValueError("specified path is not a directory or a file")

    def _writeall(self, path, arcname):
        try:
            if path.is_symlink() and not self.dereference:
                self.write(path, arcname)
            elif path.is_file():
                self.write(path, arcname)
            elif path.is_dir():
                if not path.samefile('.'):
                    self.write(path, arcname)
                for nm in sorted(os.listdir(str(path))):
                    arc = os.path.join(arcname, nm) if arcname is not None else None
                    self._writeall(path.joinpath(nm), arc)
            else:
                return  # pathlib ignores ELOOP and return False for is_*().
        except OSError as ose:
            if self.dereference and ose.errno in [errno.ELOOP]:
                return  # ignore ELOOP here, this resulted to stop looped symlink reference.
            elif self.dereference and sys.platform == 'win32' and ose.errno in [errno.ENOENT]:
                return  # ignore ENOENT which is happened when a case of ELOOP on windows.
            else:
                raise

    def write(self, file: Union[pathlib.Path, str], arcname: Optional[str] = None):
        """Write single target file into archive(Not implemented yet)."""
        if isinstance(file, str):
            path = pathlib.Path(file)
        elif isinstance(file, pathlib.Path):
            path = file
        else:
            raise ValueError("Unsupported file type.")
        file_info = self._make_file_info(path, arcname, self.dereference)
        self.files.append(file_info)

    def close(self):
        """Flush all the data into archive and close it.
        When close py7zr start reading target and writing actual archive file.
        """
        if 'w' in self.mode:
            self._write_archive()
        if 'r' in self.mode:
            if self.reporterd is not None:
                self.q.put_nowait(None)
                self.reporterd.join(1)
                if self.reporterd.is_alive():
                    raise InternalError("Progress report thread terminate error.")
                self.reporterd = None
        self._fpclose()
        self._var_release()

    def reset(self) -> None:
        """When read mode, it reset file pointer, decompress worker and decompressor"""
        if self.mode == 'r':
            self._reset_worker()
            self._reset_decompressor()


# --------------------
# exported functions
# --------------------
def is_7zfile(file: Union[BinaryIO, str, pathlib.Path]) -> bool:
    """Quickly see if a file is a 7Z file by checking the magic number.
    The file argument may be a filename or file-like object too.
    """
    result = False
    try:
        if isinstance(file, io.IOBase) and hasattr(file, "read"):
            result = SevenZipFile._check_7zfile(file)  # type: ignore  # noqa
        elif isinstance(file, str):
            with open(file, 'rb') as fp:
                result = SevenZipFile._check_7zfile(fp)
        elif isinstance(file, pathlib.Path) or isinstance(file, pathlib.PosixPath) or \
                isinstance(file, pathlib.WindowsPath):
            with file.open(mode='rb') as fp:  # type: ignore  # noqa
                result = SevenZipFile._check_7zfile(fp)
        else:
            raise TypeError('invalid type: file should be str, pathlib.Path or BinaryIO, but {}'.format(type(file)))
    except OSError:
        pass
    return result


def unpack_7zarchive(archive, path, extra=None):
    """Function for registering with shutil.register_unpack_format()"""
    arc = SevenZipFile(archive)
    arc.extractall(path)
    arc.close()


def pack_7zarchive(base_name, base_dir, owner=None, group=None, dry_run=None, logger=None):
    """Function for registering with shutil.register_archive_format()"""
    target_name = '{}.7z'.format(base_name)
    archive = SevenZipFile(target_name, mode='w')
    archive.writeall(path=base_dir)
    archive.close()
