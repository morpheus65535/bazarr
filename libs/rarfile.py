# rarfile.py
#
# Copyright (c) 2005-2016  Marko Kreen <markokr@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

r"""RAR archive reader.

This is Python module for Rar archive reading.  The interface
is made as :mod:`zipfile`-like as possible.

Basic logic:
 - Parse archive structure with Python.
 - Extract non-compressed files with Python
 - Extract compressed files with unrar.
 - Optionally write compressed data to temp file to speed up unrar,
   otherwise it needs to scan whole archive on each execution.

Example::

    import rarfile

    rf = rarfile.RarFile('myarchive.rar')
    for f in rf.infolist():
        print f.filename, f.file_size
        if f.filename == 'README':
            print(rf.read(f))

Archive files can also be accessed via file-like object returned
by :meth:`RarFile.open`::

    import rarfile

    with rarfile.RarFile('archive.rar') as rf:
        with rf.open('README') as f:
            for ln in f:
                print(ln.strip())

There are few module-level parameters to tune behaviour,
here they are with defaults, and reason to change it::

    import rarfile

    # Set to full path of unrar.exe if it is not in PATH
    rarfile.UNRAR_TOOL = "unrar"

    # Set to '\\' to be more compatible with old rarfile
    rarfile.PATH_SEP = '/'

For more details, refer to source.

"""

from __future__ import division, print_function

##
## Imports and compat - support both Python 2.x and 3.x
##

import sys
import os
import errno
import struct

from struct import pack, unpack, Struct
from binascii import crc32, hexlify
from tempfile import mkstemp
from subprocess import Popen, PIPE, STDOUT
from io import RawIOBase
from hashlib import sha1, sha256
from hmac import HMAC
from datetime import datetime, timedelta, tzinfo

# fixed offset timezone, for UTC
try:
    from datetime import timezone
except ImportError:
    class timezone(tzinfo):
        """Compat timezone."""
        __slots__ = ('_ofs', '_name')
        _DST = timedelta(0)

        def __init__(self, offset, name):
            super(timezone, self).__init__()
            self._ofs, self._name = offset, name

        def utcoffset(self, dt):
            return self._ofs

        def tzname(self, dt):
            return self._name

        def dst(self, dt):
            return self._DST

# only needed for encryped headers
try:
    try:
        from cryptography.hazmat.primitives.ciphers import algorithms, modes, Cipher
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf import pbkdf2

        class AES_CBC_Decrypt(object):
            """Decrypt API"""
            def __init__(self, key, iv):
                ciph = Cipher(algorithms.AES(key), modes.CBC(iv), default_backend())
                self.decrypt = ciph.decryptor().update

        def pbkdf2_sha256(password, salt, iters):
            """PBKDF2 with HMAC-SHA256"""
            ctx = pbkdf2.PBKDF2HMAC(hashes.SHA256(), 32, salt, iters, default_backend())
            return ctx.derive(password)

    except ImportError:
        from Crypto.Cipher import AES
        from Crypto.Protocol import KDF

        class AES_CBC_Decrypt(object):
            """Decrypt API"""
            def __init__(self, key, iv):
                self.decrypt = AES.new(key, AES.MODE_CBC, iv).decrypt

        def pbkdf2_sha256(password, salt, iters):
            """PBKDF2 with HMAC-SHA256"""
            return KDF.PBKDF2(password, salt, 32, iters, hmac_sha256)

    _have_crypto = 1
except ImportError:
    _have_crypto = 0

try:
    try:
        from hashlib import blake2s
        _have_blake2 = True
    except ImportError:
        from pyblake2 import blake2s
        _have_blake2 = True
except ImportError:
    _have_blake2 = False

# compat with 2.x
if sys.hexversion < 0x3000000:
    def rar_crc32(data, prev=0):
        """CRC32 with unsigned values.
        """
        if (prev > 0) and (prev & 0x80000000):
            prev -= (1 << 32)
        res = crc32(data, prev)
        if res < 0:
            res += (1 << 32)
        return res
    tohex = hexlify
    _byte_code = ord
else:  # pragma: no cover
    def tohex(data):
        """Return hex string."""
        return hexlify(data).decode('ascii')
    rar_crc32 = crc32
    unicode = str
    _byte_code = int   # noqa


__version__ = '3.0'

# export only interesting items
__all__ = ['is_rarfile', 'RarInfo', 'RarFile', 'RarExtFile']

##
## Module configuration.  Can be tuned after importing.
##

#: default fallback charset
DEFAULT_CHARSET = "windows-1252"

#: list of encodings to try, with fallback to DEFAULT_CHARSET if none succeed
TRY_ENCODINGS = ('utf8', 'utf-16le')

#: 'unrar', 'rar' or full path to either one
UNRAR_TOOL = "unrar"

#: Command line args to use for opening file for reading.
OPEN_ARGS = ('p', '-inul')

#: Command line args to use for extracting file to disk.
EXTRACT_ARGS = ('x', '-y', '-idq')

#: args for testrar()
TEST_ARGS = ('t', '-idq')

#
# Allow use of tool that is not compatible with unrar.
#
# By default use 'bsdtar' which is 'tar' program that
# sits on top of libarchive.
#
# Problems with libarchive RAR backend:
# - Does not support solid archives.
# - Does not support password-protected archives.
#

ALT_TOOL = 'bsdtar'
ALT_OPEN_ARGS = ('-x', '--to-stdout', '-f')
ALT_EXTRACT_ARGS = ('-x', '-f')
ALT_TEST_ARGS = ('-t', '-f')
ALT_CHECK_ARGS = ('--help',)

#: whether to speed up decompression by using tmp archive
USE_EXTRACT_HACK = 1

#: limit the filesize for tmp archive usage
HACK_SIZE_LIMIT = 20 * 1024 * 1024

#: Separator for path name components.  RAR internally uses '\\'.
#: Use '/' to be similar with zipfile.
PATH_SEP = '/'

##
## rar constants
##

# block types
RAR_BLOCK_MARK          = 0x72  # r
RAR_BLOCK_MAIN          = 0x73  # s
RAR_BLOCK_FILE          = 0x74  # t
RAR_BLOCK_OLD_COMMENT   = 0x75  # u
RAR_BLOCK_OLD_EXTRA     = 0x76  # v
RAR_BLOCK_OLD_SUB       = 0x77  # w
RAR_BLOCK_OLD_RECOVERY  = 0x78  # x
RAR_BLOCK_OLD_AUTH      = 0x79  # y
RAR_BLOCK_SUB           = 0x7a  # z
RAR_BLOCK_ENDARC        = 0x7b  # {

# flags for RAR_BLOCK_MAIN
RAR_MAIN_VOLUME         = 0x0001
RAR_MAIN_COMMENT        = 0x0002
RAR_MAIN_LOCK           = 0x0004
RAR_MAIN_SOLID          = 0x0008
RAR_MAIN_NEWNUMBERING   = 0x0010
RAR_MAIN_AUTH           = 0x0020
RAR_MAIN_RECOVERY       = 0x0040
RAR_MAIN_PASSWORD       = 0x0080
RAR_MAIN_FIRSTVOLUME    = 0x0100
RAR_MAIN_ENCRYPTVER     = 0x0200

# flags for RAR_BLOCK_FILE
RAR_FILE_SPLIT_BEFORE   = 0x0001
RAR_FILE_SPLIT_AFTER    = 0x0002
RAR_FILE_PASSWORD       = 0x0004
RAR_FILE_COMMENT        = 0x0008
RAR_FILE_SOLID          = 0x0010
RAR_FILE_DICTMASK       = 0x00e0
RAR_FILE_DICT64         = 0x0000
RAR_FILE_DICT128        = 0x0020
RAR_FILE_DICT256        = 0x0040
RAR_FILE_DICT512        = 0x0060
RAR_FILE_DICT1024       = 0x0080
RAR_FILE_DICT2048       = 0x00a0
RAR_FILE_DICT4096       = 0x00c0
RAR_FILE_DIRECTORY      = 0x00e0
RAR_FILE_LARGE          = 0x0100
RAR_FILE_UNICODE        = 0x0200
RAR_FILE_SALT           = 0x0400
RAR_FILE_VERSION        = 0x0800
RAR_FILE_EXTTIME        = 0x1000
RAR_FILE_EXTFLAGS       = 0x2000

# flags for RAR_BLOCK_ENDARC
RAR_ENDARC_NEXT_VOLUME  = 0x0001
RAR_ENDARC_DATACRC      = 0x0002
RAR_ENDARC_REVSPACE     = 0x0004
RAR_ENDARC_VOLNR        = 0x0008

# flags common to all blocks
RAR_SKIP_IF_UNKNOWN     = 0x4000
RAR_LONG_BLOCK          = 0x8000

# Host OS types
RAR_OS_MSDOS = 0
RAR_OS_OS2   = 1
RAR_OS_WIN32 = 2
RAR_OS_UNIX  = 3
RAR_OS_MACOS = 4
RAR_OS_BEOS  = 5

# Compression methods - '0'..'5'
RAR_M0 = 0x30
RAR_M1 = 0x31
RAR_M2 = 0x32
RAR_M3 = 0x33
RAR_M4 = 0x34
RAR_M5 = 0x35

#
# RAR5 constants
#

RAR5_BLOCK_MAIN = 1
RAR5_BLOCK_FILE = 2
RAR5_BLOCK_SERVICE = 3
RAR5_BLOCK_ENCRYPTION = 4
RAR5_BLOCK_ENDARC = 5

RAR5_BLOCK_FLAG_EXTRA_DATA = 0x01
RAR5_BLOCK_FLAG_DATA_AREA = 0x02
RAR5_BLOCK_FLAG_SKIP_IF_UNKNOWN = 0x04
RAR5_BLOCK_FLAG_SPLIT_BEFORE = 0x08
RAR5_BLOCK_FLAG_SPLIT_AFTER = 0x10
RAR5_BLOCK_FLAG_DEPENDS_PREV = 0x20
RAR5_BLOCK_FLAG_KEEP_WITH_PARENT = 0x40

RAR5_MAIN_FLAG_ISVOL = 0x01
RAR5_MAIN_FLAG_HAS_VOLNR = 0x02
RAR5_MAIN_FLAG_SOLID = 0x04
RAR5_MAIN_FLAG_RECOVERY = 0x08
RAR5_MAIN_FLAG_LOCKED = 0x10

RAR5_FILE_FLAG_ISDIR = 0x01
RAR5_FILE_FLAG_HAS_MTIME = 0x02
RAR5_FILE_FLAG_HAS_CRC32 = 0x04
RAR5_FILE_FLAG_UNKNOWN_SIZE = 0x08

RAR5_COMPR_SOLID = 0x40

RAR5_ENC_FLAG_HAS_CHECKVAL = 0x01

RAR5_ENDARC_FLAG_NEXT_VOL = 0x01

RAR5_XFILE_ENCRYPTION = 1
RAR5_XFILE_HASH = 2
RAR5_XFILE_TIME = 3
RAR5_XFILE_VERSION = 4
RAR5_XFILE_REDIR = 5
RAR5_XFILE_OWNER = 6
RAR5_XFILE_SERVICE = 7

RAR5_XTIME_UNIXTIME = 0x01
RAR5_XTIME_HAS_MTIME = 0x02
RAR5_XTIME_HAS_CTIME = 0x04
RAR5_XTIME_HAS_ATIME = 0x08

RAR5_XENC_CIPHER_AES256 = 0

RAR5_XENC_CHECKVAL = 0x01
RAR5_XENC_TWEAKED = 0x02

RAR5_XHASH_BLAKE2SP = 0

RAR5_XREDIR_UNIX_SYMLINK = 1
RAR5_XREDIR_WINDOWS_SYMLINK = 2
RAR5_XREDIR_WINDOWS_JUNCTION = 3
RAR5_XREDIR_HARD_LINK = 4
RAR5_XREDIR_FILE_COPY = 5

RAR5_XREDIR_ISDIR = 0x01

RAR5_XOWNER_UNAME = 0x01
RAR5_XOWNER_GNAME = 0x02
RAR5_XOWNER_UID = 0x04
RAR5_XOWNER_GID = 0x08

RAR5_OS_WINDOWS = 0
RAR5_OS_UNIX = 1

##
## internal constants
##

RAR_ID = b"Rar!\x1a\x07\x00"
RAR5_ID = b"Rar!\x1a\x07\x01\x00"
ZERO = b'\0'
EMPTY = b''
UTC = timezone(timedelta(0), 'UTC')
BSIZE = 32 * 1024

def _get_rar_version(xfile):
    """Check quickly whether file is rar archive.
    """
    with XFile(xfile) as fd:
        buf = fd.read(len(RAR5_ID))
    if buf.startswith(RAR_ID):
        return 3
    elif buf.startswith(RAR5_ID):
        return 5
    return 0

##
## Public interface
##

def is_rarfile(xfile):
    """Check quickly whether file is rar archive.
    """
    return _get_rar_version(xfile) > 0

class Error(Exception):
    """Base class for rarfile errors."""

class BadRarFile(Error):
    """Incorrect data in archive."""

class NotRarFile(Error):
    """The file is not RAR archive."""

class BadRarName(Error):
    """Cannot guess multipart name components."""

class NoRarEntry(Error):
    """File not found in RAR"""

class PasswordRequired(Error):
    """File requires password"""

class NeedFirstVolume(Error):
    """Need to start from first volume."""

class NoCrypto(Error):
    """Cannot parse encrypted headers - no crypto available."""

class RarExecError(Error):
    """Problem reported by unrar/rar."""

class RarWarning(RarExecError):
    """Non-fatal error"""

class RarFatalError(RarExecError):
    """Fatal error"""

class RarCRCError(RarExecError):
    """CRC error during unpacking"""

class RarLockedArchiveError(RarExecError):
    """Must not modify locked archive"""

class RarWriteError(RarExecError):
    """Write error"""

class RarOpenError(RarExecError):
    """Open error"""

class RarUserError(RarExecError):
    """User error"""

class RarMemoryError(RarExecError):
    """Memory error"""

class RarCreateError(RarExecError):
    """Create error"""

class RarNoFilesError(RarExecError):
    """No files that match pattern were found"""

class RarUserBreak(RarExecError):
    """User stop"""

class RarWrongPassword(RarExecError):
    """Incorrect password"""

class RarUnknownError(RarExecError):
    """Unknown exit code"""

class RarSignalExit(RarExecError):
    """Unrar exited with signal"""

class RarCannotExec(RarExecError):
    """Executable not found."""


class RarInfo(object):
    r"""An entry in rar archive.

    RAR3 extended timestamps are :class:`datetime.datetime` objects without timezone.
    RAR5 extended timestamps are :class:`datetime.datetime` objects with UTC timezone.

    Attributes:

        filename
            File name with relative path.
            Path separator is '/'.  Always unicode string.

        date_time
            File modification timestamp.   As tuple of (year, month, day, hour, minute, second).
            RAR5 allows archives where it is missing, it's None then.

        file_size
            Uncompressed size.

        compress_size
            Compressed size.

        compress_type
            Compression method: one of :data:`RAR_M0` .. :data:`RAR_M5` constants.

        extract_version
            Minimal Rar version needed for decompressing.  As (major*10 + minor),
            so 2.9 is 29.

            RAR3: 10, 20, 29

            RAR5 does not have such field in archive, it's simply set to 50.

        host_os
            Host OS type, one of RAR_OS_* constants.

            RAR3: :data:`RAR_OS_WIN32`, :data:`RAR_OS_UNIX`, :data:`RAR_OS_MSDOS`,
            :data:`RAR_OS_OS2`, :data:`RAR_OS_BEOS`.

            RAR5: :data:`RAR_OS_WIN32`, :data:`RAR_OS_UNIX`.

        mode
            File attributes. May be either dos-style or unix-style, depending on host_os.

        mtime
            File modification time.  Same value as :attr:`date_time`
            but as :class:`datetime.datetime` object with extended precision.

        ctime
            Optional time field: creation time.  As :class:`datetime.datetime` object.

        atime
            Optional time field: last access time.  As :class:`datetime.datetime` object.

        arctime
            Optional time field: archival time.  As :class:`datetime.datetime` object.
            (RAR3-only)

        CRC
            CRC-32 of uncompressed file, unsigned int.

            RAR5: may be None.

        blake2sp_hash
            Blake2SP hash over decompressed data.  (RAR5-only)

        comment
            Optional file comment field.  Unicode string.  (RAR3-only)

        file_redir
            If not None, file is link of some sort.  Contains tuple of (type, flags, target).
            (RAR5-only)

            Type is one of constants:

                :data:`RAR5_XREDIR_UNIX_SYMLINK`
                    unix symlink to target.
                :data:`RAR5_XREDIR_WINDOWS_SYMLINK`
                    windows symlink to target.
                :data:`RAR5_XREDIR_WINDOWS_JUNCTION`
                    windows junction.
                :data:`RAR5_XREDIR_HARD_LINK`
                    hard link to target.
                :data:`RAR5_XREDIR_FILE_COPY`
                    current file is copy of another archive entry.

            Flags may contain :data:`RAR5_XREDIR_ISDIR` bit.

        volume
            Volume nr, starting from 0.

        volume_file
            Volume file name, where file starts.

    """

    # zipfile-compatible fields
    filename = None
    file_size = None
    compress_size = None
    date_time = None
    comment = None
    CRC = None
    volume = None
    orig_filename = None

    # optional extended time fields, datetime() objects.
    mtime = None
    ctime = None
    atime = None

    extract_version = None
    mode = None
    host_os = None
    compress_type = None

    # rar3-only fields
    comment = None
    arctime = None

    # rar5-only fields
    blake2sp_hash = None
    file_redir = None

    # internal fields
    flags = 0
    type = None

    def isdir(self):
        """Returns True if entry is a directory.
        """
        if self.type == RAR_BLOCK_FILE:
            return (self.flags & RAR_FILE_DIRECTORY) == RAR_FILE_DIRECTORY
        return False

    def needs_password(self):
        """Returns True if data is stored password-protected.
        """
        if self.type == RAR_BLOCK_FILE:
            return (self.flags & RAR_FILE_PASSWORD) > 0
        return False


class RarFile(object):
    """Parse RAR structure, provide access to files in archive.
    """

    #: Archive comment.  Unicode string or None.
    comment = None

    def __init__(self, rarfile, mode="r", charset=None, info_callback=None,
                 crc_check=True, errors="stop"):
        """Open and parse a RAR archive.

        Parameters:

            rarfile
                archive file name
            mode
                only 'r' is supported.
            charset
                fallback charset to use, if filenames are not already Unicode-enabled.
            info_callback
                debug callback, gets to see all archive entries.
            crc_check
                set to False to disable CRC checks
            errors
                Either "stop" to quietly stop parsing on errors,
                or "strict" to raise errors.  Default is "stop".
        """
        self._rarfile = rarfile
        self._charset = charset or DEFAULT_CHARSET
        self._info_callback = info_callback
        self._crc_check = crc_check
        self._password = None
        self._file_parser = None

        if errors == "stop":
            self._strict = False
        elif errors == "strict":
            self._strict = True
        else:
            raise ValueError("Invalid value for 'errors' parameter.")

        if mode != "r":
            raise NotImplementedError("RarFile supports only mode=r")

        self._parse()

    def __enter__(self):
        """Open context."""
        return self

    def __exit__(self, typ, value, traceback):
        """Exit context"""
        self.close()

    def setpassword(self, password):
        """Sets the password to use when extracting.
        """
        self._password = password
        if self._file_parser:
            if self._file_parser.has_header_encryption():
                self._file_parser = None
        if not self._file_parser:
            self._parse()
        else:
            self._file_parser.setpassword(self._password)

    def needs_password(self):
        """Returns True if any archive entries require password for extraction.
        """
        return self._file_parser.needs_password()

    def namelist(self):
        """Return list of filenames in archive.
        """
        return [f.filename for f in self.infolist()]

    def infolist(self):
        """Return RarInfo objects for all files/directories in archive.
        """
        return self._file_parser.infolist()

    def volumelist(self):
        """Returns filenames of archive volumes.

        In case of single-volume archive, the list contains
        just the name of main archive file.
        """
        return self._file_parser.volumelist()

    def getinfo(self, fname):
        """Return RarInfo for file.
        """
        return self._file_parser.getinfo(fname)

    def open(self, fname, mode='r', psw=None):
        """Returns file-like object (:class:`RarExtFile`) from where the data can be read.

        The object implements :class:`io.RawIOBase` interface, so it can
        be further wrapped with :class:`io.BufferedReader`
        and :class:`io.TextIOWrapper`.

        On older Python where io module is not available, it implements
        only .read(), .seek(), .tell() and .close() methods.

        The object is seekable, although the seeking is fast only on
        uncompressed files, on compressed files the seeking is implemented
        by reading ahead and/or restarting the decompression.

        Parameters:

            fname
                file name or RarInfo instance.
            mode
                must be 'r'
            psw
                password to use for extracting.
        """

        if mode != 'r':
            raise NotImplementedError("RarFile.open() supports only mode=r")

        # entry lookup
        inf = self.getinfo(fname)
        if inf.isdir():
            raise TypeError("Directory does not have any data: " + inf.filename)

        # check password
        if inf.needs_password():
            psw = psw or self._password
            if psw is None:
                raise PasswordRequired("File %s requires password" % inf.filename)
        else:
            psw = None

        return self._file_parser.open(inf, psw)

    def read(self, fname, psw=None):
        """Return uncompressed data for archive entry.

        For longer files using :meth:`RarFile.open` may be better idea.

        Parameters:

            fname
                filename or RarInfo instance
            psw
                password to use for extracting.
        """

        with self.open(fname, 'r', psw) as f:
            return f.read()

    def close(self):
        """Release open resources."""
        pass

    def printdir(self):
        """Print archive file list to stdout."""
        for f in self.infolist():
            print(f.filename)

    def extract(self, member, path=None, pwd=None):
        """Extract single file into current directory.

        Parameters:

            member
                filename or :class:`RarInfo` instance
            path
                optional destination path
            pwd
                optional password to use
        """
        if isinstance(member, RarInfo):
            fname = member.filename
        else:
            fname = member
        self._extract([fname], path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        """Extract all files into current directory.

        Parameters:

            path
                optional destination path
            members
                optional filename or :class:`RarInfo` instance list to extract
            pwd
                optional password to use
        """
        fnlist = []
        if members is not None:
            for m in members:
                if isinstance(m, RarInfo):
                    fnlist.append(m.filename)
                else:
                    fnlist.append(m)
        self._extract(fnlist, path, pwd)

    def testrar(self):
        """Let 'unrar' test the archive.
        """
        cmd = [UNRAR_TOOL] + list(TEST_ARGS)
        add_password_arg(cmd, self._password)
        cmd.append('--')
        with XTempFile(self._rarfile) as rarfile:
            cmd.append(rarfile)
            p = custom_popen(cmd)
            output = p.communicate()[0]
            check_returncode(p, output)

    def strerror(self):
        """Return error string if parsing failed or None if no problems.
        """
        if not self._file_parser:
            return "Not a RAR file"
        return self._file_parser.strerror()

    ##
    ## private methods
    ##

    def _parse(self):
        ver = _get_rar_version(self._rarfile)
        if ver == 3:
            p3 = RAR3Parser(self._rarfile, self._password, self._crc_check,
                            self._charset, self._strict, self._info_callback)
            self._file_parser = p3  # noqa
        elif ver == 5:
            p5 = RAR5Parser(self._rarfile, self._password, self._crc_check,
                            self._charset, self._strict, self._info_callback)
            self._file_parser = p5  # noqa
        else:
            raise BadRarFile("Not a RAR file")

        self._file_parser.parse()
        self.comment = self._file_parser.comment

    # call unrar to extract a file
    def _extract(self, fnlist, path=None, psw=None):
        cmd = [UNRAR_TOOL] + list(EXTRACT_ARGS)

        # pasoword
        psw = psw or self._password
        add_password_arg(cmd, psw)
        cmd.append('--')

        # rar file
        with XTempFile(self._rarfile) as rarfn:
            cmd.append(rarfn)

            # file list
            for fn in fnlist:
                if os.sep != PATH_SEP:
                    fn = fn.replace(PATH_SEP, os.sep)
                cmd.append(fn)

            # destination path
            if path is not None:
                cmd.append(path + os.sep)

            # call
            p = custom_popen(cmd)
            output = p.communicate()[0]
            check_returncode(p, output)

#
# File format parsing
#

class CommonParser(object):
    """Shared parser parts."""
    _main = None
    _hdrenc_main = None
    _needs_password = False
    _fd = None
    _expect_sig = None
    _parse_error = None
    _password = None
    comment = None

    def __init__(self, rarfile, password, crc_check, charset, strict, info_cb):
        self._rarfile = rarfile
        self._password = password
        self._crc_check = crc_check
        self._charset = charset
        self._strict = strict
        self._info_callback = info_cb
        self._info_list = []
        self._info_map = {}
        self._vol_list = []

    def has_header_encryption(self):
        """Returns True if headers are encrypted
        """
        if self._hdrenc_main:
            return True
        if self._main:
            if self._main.flags & RAR_MAIN_PASSWORD:
                return True
        return False

    def setpassword(self, psw):
        """Set cached password."""
        self._password = psw

    def volumelist(self):
        """Volume files"""
        return self._vol_list

    def needs_password(self):
        """Is password required"""
        return self._needs_password

    def strerror(self):
        """Last error"""
        return self._parse_error

    def infolist(self):
        """List of RarInfo records.
        """
        return self._info_list

    def getinfo(self, member):
        """Return RarInfo for filename
        """
        if isinstance(member, RarInfo):
            fname = member.filename
        else:
            fname = member

        # accept both ways here
        if PATH_SEP == '/':
            fname2 = fname.replace("\\", "/")
        else:
            fname2 = fname.replace("/", "\\")

        try:
            return self._info_map[fname]
        except KeyError:
            try:
                return self._info_map[fname2]
            except KeyError:
                raise NoRarEntry("No such file: %s" % fname)

    # read rar
    def parse(self):
        """Process file."""
        self._fd = None
        try:
            self._parse_real()
        finally:
            if self._fd:
                self._fd.close()
                self._fd = None

    def _parse_real(self):
        fd = XFile(self._rarfile)
        self._fd = fd
        sig = fd.read(len(self._expect_sig))
        if sig != self._expect_sig:
            if isinstance(self._rarfile, (str, unicode)):
                raise NotRarFile("Not a Rar archive: {}".format(self._rarfile))
            raise NotRarFile("Not a Rar archive")

        volume = 0  # first vol (.rar) is 0
        more_vols = False
        endarc = False
        volfile = self._rarfile
        self._vol_list = [self._rarfile]
        while 1:
            if endarc:
                h = None    # don't read past ENDARC
            else:
                h = self._parse_header(fd)
            if not h:
                if more_vols:
                    volume += 1
                    fd.close()
                    try:
                        volfile = self._next_volname(volfile)
                        fd = XFile(volfile)
                    except IOError:
                        self._set_error("Cannot open next volume: %s", volfile)
                        break
                    self._fd = fd
                    sig = fd.read(len(self._expect_sig))
                    if sig != self._expect_sig:
                        self._set_error("Invalid volume sig: %s", volfile)
                        break
                    more_vols = False
                    endarc = False
                    self._vol_list.append(volfile)
                    continue
                break
            h.volume = volume
            h.volume_file = volfile

            if h.type == RAR_BLOCK_MAIN and not self._main:
                self._main = h
                if h.flags & RAR_MAIN_NEWNUMBERING:
                    # RAR 2.x does not set FIRSTVOLUME,
                    # so check it only if NEWNUMBERING is used
                    if (h.flags & RAR_MAIN_FIRSTVOLUME) == 0:
                        raise NeedFirstVolume("Need to start from first volume")
                if h.flags & RAR_MAIN_PASSWORD:
                    self._needs_password = True
                    if not self._password:
                        break
            elif h.type == RAR_BLOCK_ENDARC:
                more_vols = (h.flags & RAR_ENDARC_NEXT_VOLUME) > 0
                endarc = True
            elif h.type == RAR_BLOCK_FILE:
                # RAR 2.x does not write RAR_BLOCK_ENDARC
                if h.flags & RAR_FILE_SPLIT_AFTER:
                    more_vols = True
                # RAR 2.x does not set RAR_MAIN_FIRSTVOLUME
                if volume == 0 and h.flags & RAR_FILE_SPLIT_BEFORE:
                    raise NeedFirstVolume("Need to start from first volume")

            if h.needs_password():
                self._needs_password = True

            # store it
            self.process_entry(fd, h)

            if self._info_callback:
                self._info_callback(h)

            # go to next header
            if h.add_size > 0:
                fd.seek(h.data_offset + h.add_size, 0)

    def process_entry(self, fd, item):
        """Examine item, add into lookup cache."""
        raise NotImplementedError()

    def _decrypt_header(self, fd):
        raise NotImplementedError('_decrypt_header')

    def _parse_block_header(self, fd):
        raise NotImplementedError('_parse_block_header')

    def _open_hack(self, inf, psw):
        raise NotImplementedError('_open_hack')

    # read single header
    def _parse_header(self, fd):
        try:
            # handle encrypted headers
            if (self._main and self._main.flags & RAR_MAIN_PASSWORD) or self._hdrenc_main:
                if not self._password:
                    return
                fd = self._decrypt_header(fd)

            # now read actual header
            return self._parse_block_header(fd)
        except struct.error:
            self._set_error('Broken header in RAR file')
            return None

    # given current vol name, construct next one
    def _next_volname(self, volfile):
        if is_filelike(volfile):
            raise IOError("Working on single FD")
        if self._main.flags & RAR_MAIN_NEWNUMBERING:
            return _next_newvol(volfile)
        return _next_oldvol(volfile)

    def _set_error(self, msg, *args):
        if args:
            msg = msg % args
        self._parse_error = msg
        if self._strict:
            raise BadRarFile(msg)

    def open(self, inf, psw):
        """Return stream object for file data."""

        if inf.file_redir:
            # cannot leave to unrar as it expects copied file to exist
            if inf.file_redir[0] in (RAR5_XREDIR_FILE_COPY, RAR5_XREDIR_HARD_LINK):
                inf = self.getinfo(inf.file_redir[2])
                if not inf:
                    raise BadRarFile('cannot find copied file')

        if inf.flags & RAR_FILE_SPLIT_BEFORE:
            raise NeedFirstVolume("Partial file, please start from first volume: " + inf.filename)

        # is temp write usable?
        use_hack = 1
        if not self._main:
            use_hack = 0
        elif self._main._must_disable_hack():
            use_hack = 0
        elif inf._must_disable_hack():
            use_hack = 0
        elif is_filelike(self._rarfile):
            pass
        elif inf.file_size > HACK_SIZE_LIMIT:
            use_hack = 0
        elif not USE_EXTRACT_HACK:
            use_hack = 0

        # now extract
        if inf.compress_type == RAR_M0 and (inf.flags & RAR_FILE_PASSWORD) == 0 and inf.file_redir is None:
            return self._open_clear(inf)
        elif use_hack:
            return self._open_hack(inf, psw)
        elif is_filelike(self._rarfile):
            return self._open_unrar_membuf(self._rarfile, inf, psw)
        else:
            return self._open_unrar(self._rarfile, inf, psw)

    def _open_clear(self, inf):
        return DirectReader(self, inf)

    def _open_hack_core(self, inf, psw, prefix, suffix):

        size = inf.compress_size + inf.header_size
        rf = XFile(inf.volume_file, 0)
        rf.seek(inf.header_offset)

        tmpfd, tmpname = mkstemp(suffix='.rar')
        tmpf = os.fdopen(tmpfd, "wb")

        try:
            tmpf.write(prefix)
            while size > 0:
                if size > BSIZE:
                    buf = rf.read(BSIZE)
                else:
                    buf = rf.read(size)
                if not buf:
                    raise BadRarFile('read failed: ' + inf.filename)
                tmpf.write(buf)
                size -= len(buf)
            tmpf.write(suffix)
            tmpf.close()
            rf.close()
        except:
            rf.close()
            tmpf.close()
            os.unlink(tmpname)
            raise

        return self._open_unrar(tmpname, inf, psw, tmpname)

    # write in-memory archive to temp file - needed for solid archives
    def _open_unrar_membuf(self, memfile, inf, psw):
        tmpname = membuf_tempfile(memfile)
        return self._open_unrar(tmpname, inf, psw, tmpname, force_file=True)

    # extract using unrar
    def _open_unrar(self, rarfile, inf, psw=None, tmpfile=None, force_file=False):
        cmd = [UNRAR_TOOL] + list(OPEN_ARGS)
        add_password_arg(cmd, psw)
        cmd.append("--")
        cmd.append(rarfile)

        # not giving filename avoids encoding related problems
        if not tmpfile or force_file:
            fn = inf.filename
            if PATH_SEP != os.sep:
                fn = fn.replace(PATH_SEP, os.sep)
            cmd.append(fn)

        # read from unrar pipe
        return PipeReader(self, inf, cmd, tmpfile)

#
# RAR3 format
#

class Rar3Info(RarInfo):
    """RAR3 specific fields."""
    extract_version = 15
    salt = None
    add_size = 0
    header_crc = None
    header_size = None
    header_offset = None
    data_offset = None
    _md_class = None
    _md_expect = None

    # make sure some rar5 fields are always present
    file_redir = None
    blake2sp_hash = None

    def _must_disable_hack(self):
        if self.type == RAR_BLOCK_FILE:
            if self.flags & RAR_FILE_PASSWORD:
                return True
            elif self.flags & (RAR_FILE_SPLIT_BEFORE | RAR_FILE_SPLIT_AFTER):
                return True
        elif self.type == RAR_BLOCK_MAIN:
            if self.flags & (RAR_MAIN_SOLID | RAR_MAIN_PASSWORD):
                return True
        return False


class RAR3Parser(CommonParser):
    """Parse RAR3 file format.
    """
    _expect_sig = RAR_ID
    _last_aes_key = (None, None, None)   # (salt, key, iv)

    def _decrypt_header(self, fd):
        if not _have_crypto:
            raise NoCrypto('Cannot parse encrypted headers - no crypto')
        salt = fd.read(8)
        if self._last_aes_key[0] == salt:
            key, iv = self._last_aes_key[1:]
        else:
            key, iv = rar3_s2k(self._password, salt)
            self._last_aes_key = (salt, key, iv)
        return HeaderDecrypt(fd, key, iv)

    # common header
    def _parse_block_header(self, fd):
        h = Rar3Info()
        h.header_offset = fd.tell()

        # read and parse base header
        buf = fd.read(S_BLK_HDR.size)
        if not buf:
            return None
        t = S_BLK_HDR.unpack_from(buf)
        h.header_crc, h.type, h.flags, h.header_size = t

        # read full header
        if h.header_size > S_BLK_HDR.size:
            hdata = buf + fd.read(h.header_size - S_BLK_HDR.size)
        else:
            hdata = buf
        h.data_offset = fd.tell()

        # unexpected EOF?
        if len(hdata) != h.header_size:
            self._set_error('Unexpected EOF when reading header')
            return None

        pos = S_BLK_HDR.size

        # block has data assiciated with it?
        if h.flags & RAR_LONG_BLOCK:
            h.add_size, pos = load_le32(hdata, pos)
        else:
            h.add_size = 0

        # parse interesting ones, decide header boundaries for crc
        if h.type == RAR_BLOCK_MARK:
            return h
        elif h.type == RAR_BLOCK_MAIN:
            pos += 6
            if h.flags & RAR_MAIN_ENCRYPTVER:
                pos += 1
            crc_pos = pos
            if h.flags & RAR_MAIN_COMMENT:
                self._parse_subblocks(h, hdata, pos)
        elif h.type == RAR_BLOCK_FILE:
            pos = self._parse_file_header(h, hdata, pos - 4)
            crc_pos = pos
            if h.flags & RAR_FILE_COMMENT:
                pos = self._parse_subblocks(h, hdata, pos)
        elif h.type == RAR_BLOCK_SUB:
            pos = self._parse_file_header(h, hdata, pos - 4)
            crc_pos = h.header_size
        elif h.type == RAR_BLOCK_OLD_AUTH:
            pos += 8
            crc_pos = pos
        elif h.type == RAR_BLOCK_OLD_EXTRA:
            pos += 7
            crc_pos = pos
        else:
            crc_pos = h.header_size

        # check crc
        if h.type == RAR_BLOCK_OLD_SUB:
            crcdat = hdata[2:] + fd.read(h.add_size)
        else:
            crcdat = hdata[2:crc_pos]

        calc_crc = rar_crc32(crcdat) & 0xFFFF

        # return good header
        if h.header_crc == calc_crc:
            return h

        # header parsing failed.
        self._set_error('Header CRC error (%02x): exp=%x got=%x (xlen = %d)',
                        h.type, h.header_crc, calc_crc, len(crcdat))

        # instead panicing, send eof
        return None

    # read file-specific header
    def _parse_file_header(self, h, hdata, pos):
        fld = S_FILE_HDR.unpack_from(hdata, pos)
        pos += S_FILE_HDR.size

        h.compress_size = fld[0]
        h.file_size = fld[1]
        h.host_os = fld[2]
        h.CRC = fld[3]
        h.date_time = parse_dos_time(fld[4])
        h.mtime = to_datetime(h.date_time)
        h.extract_version = fld[5]
        h.compress_type = fld[6]
        name_size = fld[7]
        h.mode = fld[8]

        h._md_class = CRC32Context
        h._md_expect = h.CRC

        if h.flags & RAR_FILE_LARGE:
            h1, pos = load_le32(hdata, pos)
            h2, pos = load_le32(hdata, pos)
            h.compress_size |= h1 << 32
            h.file_size |= h2 << 32
            h.add_size = h.compress_size

        name, pos = load_bytes(hdata, name_size, pos)
        if h.flags & RAR_FILE_UNICODE:
            nul = name.find(ZERO)
            h.orig_filename = name[:nul]
            u = UnicodeFilename(h.orig_filename, name[nul + 1:])
            h.filename = u.decode()

            # if parsing failed fall back to simple name
            if u.failed:
                h.filename = self._decode(h.orig_filename)
        else:
            h.orig_filename = name
            h.filename = self._decode(name)

        # change separator, if requested
        if PATH_SEP != '\\':
            h.filename = h.filename.replace('\\', PATH_SEP)

        if h.flags & RAR_FILE_SALT:
            h.salt, pos = load_bytes(hdata, 8, pos)
        else:
            h.salt = None

        # optional extended time stamps
        if h.flags & RAR_FILE_EXTTIME:
            pos = _parse_ext_time(h, hdata, pos)
        else:
            h.mtime = h.atime = h.ctime = h.arctime = None

        return pos

    # find old-style comment subblock
    def _parse_subblocks(self, h, hdata, pos):
        while pos < len(hdata):
            # ordinary block header
            t = S_BLK_HDR.unpack_from(hdata, pos)
            ___scrc, stype, sflags, slen = t
            pos_next = pos + slen
            pos += S_BLK_HDR.size

            # corrupt header
            if pos_next < pos:
                break

            # followed by block-specific header
            if stype == RAR_BLOCK_OLD_COMMENT and pos + S_COMMENT_HDR.size <= pos_next:
                declen, ver, meth, crc = S_COMMENT_HDR.unpack_from(hdata, pos)
                pos += S_COMMENT_HDR.size
                data = hdata[pos : pos_next]
                cmt = rar3_decompress(ver, meth, data, declen, sflags,
                                      crc, self._password)
                if not self._crc_check:
                    h.comment = self._decode_comment(cmt)
                elif rar_crc32(cmt) & 0xFFFF == crc:
                    h.comment = self._decode_comment(cmt)

            pos = pos_next
        return pos

    def _read_comment_v3(self, inf, psw=None):

        # read data
        with XFile(inf.volume_file) as rf:
            rf.seek(inf.data_offset)
            data = rf.read(inf.compress_size)

        # decompress
        cmt = rar3_decompress(inf.extract_version, inf.compress_type, data,
                              inf.file_size, inf.flags, inf.CRC, psw, inf.salt)

        # check crc
        if self._crc_check:
            crc = rar_crc32(cmt)
            if crc != inf.CRC:
                return None

        return self._decode_comment(cmt)

    def _decode(self, val):
        for c in TRY_ENCODINGS:
            try:
                return val.decode(c)
            except UnicodeError:
                pass
        return val.decode(self._charset, 'replace')

    def _decode_comment(self, val):
        return self._decode(val)

    def process_entry(self, fd, item):
        if item.type == RAR_BLOCK_FILE:
            # use only first part
            if (item.flags & RAR_FILE_SPLIT_BEFORE) == 0:
                self._info_map[item.filename] = item
                self._info_list.append(item)
            elif len(self._info_list) > 0:
                # final crc is in last block
                old = self._info_list[-1]
                old.CRC = item.CRC
                old._md_expect = item._md_expect
                old.compress_size += item.compress_size

        # parse new-style comment
        if item.type == RAR_BLOCK_SUB and item.filename == 'CMT':
            if item.flags & (RAR_FILE_SPLIT_BEFORE | RAR_FILE_SPLIT_AFTER):
                pass
            elif item.flags & RAR_FILE_SOLID:
                # file comment
                cmt = self._read_comment_v3(item, self._password)
                if len(self._info_list) > 0:
                    old = self._info_list[-1]
                    old.comment = cmt
            else:
                # archive comment
                cmt = self._read_comment_v3(item, self._password)
                self.comment = cmt

        if item.type == RAR_BLOCK_MAIN:
            if item.flags & RAR_MAIN_COMMENT:
                self.comment = item.comment
            if item.flags & RAR_MAIN_PASSWORD:
                self._needs_password = True

    # put file compressed data into temporary .rar archive, and run
    # unrar on that, thus avoiding unrar going over whole archive
    def _open_hack(self, inf, psw):
        # create main header: crc, type, flags, size, res1, res2
        prefix = RAR_ID + S_BLK_HDR.pack(0x90CF, 0x73, 0, 13) + ZERO * (2 + 4)
        return self._open_hack_core(inf, psw, prefix, EMPTY)

#
# RAR5 format
#

class Rar5Info(RarInfo):
    """Shared fields for RAR5 records.
    """
    extract_version = 50
    header_crc = None
    header_size = None
    header_offset = None
    data_offset = None

    # type=all
    block_type = None
    block_flags = None
    add_size = 0
    block_extra_size = 0

    # type=MAIN
    volume_number = None
    _md_class = None
    _md_expect = None

    def _must_disable_hack(self):
        return False


class Rar5BaseFile(Rar5Info):
    """Shared sturct for file & service record.
    """
    type = -1
    file_flags = None
    file_encryption = (0, 0, 0, EMPTY, EMPTY, EMPTY)
    file_compress_flags = None
    file_redir = None
    file_owner = None
    file_version = None
    blake2sp_hash = None

    def _must_disable_hack(self):
        if self.flags & RAR_FILE_PASSWORD:
            return True
        if self.block_flags & (RAR5_BLOCK_FLAG_SPLIT_BEFORE | RAR5_BLOCK_FLAG_SPLIT_AFTER):
            return True
        if self.file_compress_flags & RAR5_COMPR_SOLID:
            return True
        if self.file_redir:
            return True
        return False


class Rar5FileInfo(Rar5BaseFile):
    """RAR5 file record.
    """
    type = RAR_BLOCK_FILE


class Rar5ServiceInfo(Rar5BaseFile):
    """RAR5 service record.
    """
    type = RAR_BLOCK_SUB


class Rar5MainInfo(Rar5Info):
    """RAR5 archive main record.
    """
    type = RAR_BLOCK_MAIN
    main_flags = None
    main_volume_number = None

    def _must_disable_hack(self):
        if self.main_flags & RAR5_MAIN_FLAG_SOLID:
            return True
        return False


class Rar5EncryptionInfo(Rar5Info):
    """RAR5 archive header encryption record.
    """
    type = RAR5_BLOCK_ENCRYPTION
    encryption_algo = None
    encryption_flags = None
    encryption_kdf_count = None
    encryption_salt = None
    encryption_check_value = None

    def needs_password(self):
        return True


class Rar5EndArcInfo(Rar5Info):
    """RAR5 end of archive record.
    """
    type = RAR_BLOCK_ENDARC
    endarc_flags = None


class RAR5Parser(CommonParser):
    """Parse RAR5 format.
    """
    _expect_sig = RAR5_ID
    _hdrenc_main = None

    # AES encrypted headers
    _last_aes256_key = (-1, None, None)   # (kdf_count, salt, key)

    def _gen_key(self, kdf_count, salt):
        if self._last_aes256_key[:2] == (kdf_count, salt):
            return self._last_aes256_key[2]
        if kdf_count > 24:
            raise BadRarFile('Too large kdf_count')
        psw = self._password
        if isinstance(psw, unicode):
            psw = psw.encode('utf8')
        key = pbkdf2_sha256(psw, salt, 1 << kdf_count)
        self._last_aes256_key = (kdf_count, salt, key)
        return key

    def _decrypt_header(self, fd):
        if not _have_crypto:
            raise NoCrypto('Cannot parse encrypted headers - no crypto')
        h = self._hdrenc_main
        key = self._gen_key(h.encryption_kdf_count, h.encryption_salt)
        iv = fd.read(16)
        return HeaderDecrypt(fd, key, iv)

    # common header
    def _parse_block_header(self, fd):
        header_offset = fd.tell()

        preload = 4 + 3
        start_bytes = fd.read(preload)
        header_crc, pos = load_le32(start_bytes, 0)
        hdrlen, pos = load_vint(start_bytes, pos)
        if hdrlen > 2 * 1024 * 1024:
            return None
        header_size = pos + hdrlen

        # read full header, check for EOF
        hdata = start_bytes + fd.read(header_size - len(start_bytes))
        if len(hdata) != header_size:
            self._set_error('Unexpected EOF when reading header')
            return None
        data_offset = fd.tell()

        calc_crc = rar_crc32(memoryview(hdata)[4:])
        if header_crc != calc_crc:
            # header parsing failed.
            self._set_error('Header CRC error: exp=%x got=%x (xlen = %d)',
                            header_crc, calc_crc, len(hdata))
            return None

        block_type, pos = load_vint(hdata, pos)

        if block_type == RAR5_BLOCK_MAIN:
            h, pos = self._parse_block_common(Rar5MainInfo(), hdata)
            h = self._parse_main_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_FILE:
            h, pos = self._parse_block_common(Rar5FileInfo(), hdata)
            h = self._parse_file_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_SERVICE:
            h, pos = self._parse_block_common(Rar5ServiceInfo(), hdata)
            h = self._parse_file_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_ENCRYPTION:
            h, pos = self._parse_block_common(Rar5EncryptionInfo(), hdata)
            h = self._parse_encryption_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_ENDARC:
            h, pos = self._parse_block_common(Rar5EndArcInfo(), hdata)
            h = self._parse_endarc_block(h, hdata, pos)
        else:
            h = None
        if h:
            h.header_offset = header_offset
            h.data_offset = data_offset
        return h

    def _parse_block_common(self, h, hdata):
        h.header_crc, pos = load_le32(hdata, 0)
        hdrlen, pos = load_vint(hdata, pos)
        h.header_size = hdrlen + pos
        h.block_type, pos = load_vint(hdata, pos)
        h.block_flags, pos = load_vint(hdata, pos)

        if h.block_flags & RAR5_BLOCK_FLAG_EXTRA_DATA:
            h.block_extra_size, pos = load_vint(hdata, pos)
        if h.block_flags & RAR5_BLOCK_FLAG_DATA_AREA:
            h.add_size, pos = load_vint(hdata, pos)

        h.compress_size = h.add_size

        if h.block_flags & RAR5_BLOCK_FLAG_SKIP_IF_UNKNOWN:
            h.flags |= RAR_SKIP_IF_UNKNOWN
        if h.block_flags & RAR5_BLOCK_FLAG_DATA_AREA:
            h.flags |= RAR_LONG_BLOCK
        return h, pos

    def _parse_main_block(self, h, hdata, pos):
        h.main_flags, pos = load_vint(hdata, pos)
        if h.main_flags & RAR5_MAIN_FLAG_HAS_VOLNR:
            h.main_volume_number = load_vint(hdata, pos)

        h.flags |= RAR_MAIN_NEWNUMBERING
        if h.main_flags & RAR5_MAIN_FLAG_SOLID:
            h.flags |= RAR_MAIN_SOLID
        if h.main_flags & RAR5_MAIN_FLAG_ISVOL:
            h.flags |= RAR_MAIN_VOLUME
        if h.main_flags & RAR5_MAIN_FLAG_RECOVERY:
            h.flags |= RAR_MAIN_RECOVERY
        if self._hdrenc_main:
            h.flags |= RAR_MAIN_PASSWORD
        if h.main_flags & RAR5_MAIN_FLAG_HAS_VOLNR == 0:
            h.flags |= RAR_MAIN_FIRSTVOLUME

        return h

    def _parse_file_block(self, h, hdata, pos):
        h.file_flags, pos = load_vint(hdata, pos)
        h.file_size, pos = load_vint(hdata, pos)
        h.mode, pos = load_vint(hdata, pos)

        if h.file_flags & RAR5_FILE_FLAG_HAS_MTIME:
            h.mtime, pos = load_unixtime(hdata, pos)
            h.date_time = h.mtime.timetuple()[:6]
        if h.file_flags & RAR5_FILE_FLAG_HAS_CRC32:
            h.CRC, pos = load_le32(hdata, pos)
            h._md_class = CRC32Context
            h._md_expect = h.CRC

        h.file_compress_flags, pos = load_vint(hdata, pos)
        h.file_host_os, pos = load_vint(hdata, pos)
        h.orig_filename, pos = load_vstr(hdata, pos)
        h.filename = h.orig_filename.decode('utf8', 'replace')

        # use compatible values
        if h.file_host_os == RAR5_OS_WINDOWS:
            h.host_os = RAR_OS_WIN32
        else:
            h.host_os = RAR_OS_UNIX
        h.compress_type = RAR_M0 + ((h.file_compress_flags >> 7) & 7)

        if h.block_extra_size:
            # allow 1 byte of garbage
            while pos < len(hdata) - 1:
                xsize, pos = load_vint(hdata, pos)
                xdata, pos = load_bytes(hdata, xsize, pos)
                self._process_file_extra(h, xdata)

        if h.block_flags & RAR5_BLOCK_FLAG_SPLIT_BEFORE:
            h.flags |= RAR_FILE_SPLIT_BEFORE
        if h.block_flags & RAR5_BLOCK_FLAG_SPLIT_AFTER:
            h.flags |= RAR_FILE_SPLIT_AFTER
        if h.file_flags & RAR5_FILE_FLAG_ISDIR:
            h.flags |= RAR_FILE_DIRECTORY
        if h.file_compress_flags & RAR5_COMPR_SOLID:
            h.flags |= RAR_FILE_SOLID

        return h

    def _parse_endarc_block(self, h, hdata, pos):
        h.endarc_flags, pos = load_vint(hdata, pos)
        if h.endarc_flags & RAR5_ENDARC_FLAG_NEXT_VOL:
            h.flags |= RAR_ENDARC_NEXT_VOLUME
        return h

    def _parse_encryption_block(self, h, hdata, pos):
        h.encryption_algo, pos = load_vint(hdata, pos)
        h.encryption_flags, pos = load_vint(hdata, pos)
        h.encryption_kdf_count, pos = load_byte(hdata, pos)
        h.encryption_salt, pos = load_bytes(hdata, 16, pos)
        if h.encryption_flags & RAR5_ENC_FLAG_HAS_CHECKVAL:
            h.encryption_check_value = load_bytes(hdata, 12, pos)
        if h.encryption_algo != RAR5_XENC_CIPHER_AES256:
            raise BadRarFile('Unsupported header encryption cipher')
        self._hdrenc_main = h
        return h

    # file extra record
    def _process_file_extra(self, h, xdata):
        xtype, pos = load_vint(xdata, 0)
        if xtype == RAR5_XFILE_TIME:
            self._parse_file_xtime(h, xdata, pos)
        elif xtype == RAR5_XFILE_ENCRYPTION:
            self._parse_file_encryption(h, xdata, pos)
        elif xtype == RAR5_XFILE_HASH:
            self._parse_file_hash(h, xdata, pos)
        elif xtype == RAR5_XFILE_VERSION:
            self._parse_file_version(h, xdata, pos)
        elif xtype == RAR5_XFILE_REDIR:
            self._parse_file_redir(h, xdata, pos)
        elif xtype == RAR5_XFILE_OWNER:
            self._parse_file_owner(h, xdata, pos)
        elif xtype == RAR5_XFILE_SERVICE:
            pass
        else:
            pass

    # extra block for file time record
    def _parse_file_xtime(self, h, xdata, pos):
        tflags, pos = load_vint(xdata, pos)
        ldr = load_windowstime
        if tflags & RAR5_XTIME_UNIXTIME:
            ldr = load_unixtime
        if tflags & RAR5_XTIME_HAS_MTIME:
            h.mtime, pos = ldr(xdata, pos)
            h.date_time = h.mtime.timetuple()[:6]
        if tflags & RAR5_XTIME_HAS_CTIME:
            h.ctime, pos = ldr(xdata, pos)
        if tflags & RAR5_XTIME_HAS_ATIME:
            h.atime, pos = ldr(xdata, pos)

    # just remember encryption info
    def _parse_file_encryption(self, h, xdata, pos):
        algo, pos = load_vint(xdata, pos)
        flags, pos = load_vint(xdata, pos)
        kdf_count, pos = load_byte(xdata, pos)
        salt, pos = load_bytes(xdata, 16, pos)
        iv, pos = load_bytes(xdata, 16, pos)
        checkval = None
        if flags & RAR5_XENC_CHECKVAL:
            checkval, pos = load_bytes(xdata, 12, pos)
        if flags & RAR5_XENC_TWEAKED:
            h._md_expect = None
            h._md_class = NoHashContext

        h.file_encryption = (algo, flags, kdf_count, salt, iv, checkval)
        h.flags |= RAR_FILE_PASSWORD

    def _parse_file_hash(self, h, xdata, pos):
        hash_type, pos = load_vint(xdata, pos)
        if hash_type == RAR5_XHASH_BLAKE2SP:
            h.blake2sp_hash, pos = load_bytes(xdata, 32, pos)
            if _have_blake2 and (h.file_encryption[1] & RAR5_XENC_TWEAKED) == 0:
                h._md_class = Blake2SP
                h._md_expect = h.blake2sp_hash

    def _parse_file_version(self, h, xdata, pos):
        flags, pos = load_vint(xdata, pos)
        version, pos = load_vint(xdata, pos)
        h.file_version = (flags, version)

    def _parse_file_redir(self, h, xdata, pos):
        redir_type, pos = load_vint(xdata, pos)
        redir_flags, pos = load_vint(xdata, pos)
        redir_name, pos = load_vstr(xdata, pos)
        redir_name = redir_name.decode('utf8', 'replace')
        h.file_redir = (redir_type, redir_flags, redir_name)

    def _parse_file_owner(self, h, xdata, pos):
        user_name = group_name = user_id = group_id = None

        flags, pos = load_vint(xdata, pos)
        if flags & RAR5_XOWNER_UNAME:
            user_name, pos = load_vstr(xdata, pos)
        if flags & RAR5_XOWNER_GNAME:
            group_name, pos = load_vstr(xdata, pos)
        if flags & RAR5_XOWNER_UID:
            user_id, pos = load_vint(xdata, pos)
        if flags & RAR5_XOWNER_GID:
            group_id, pos = load_vint(xdata, pos)

        h.file_owner = (user_name, group_name, user_id, group_id)

    def process_entry(self, fd, item):
        if item.block_type == RAR5_BLOCK_FILE:
            # use only first part
            if (item.block_flags & RAR5_BLOCK_FLAG_SPLIT_BEFORE) == 0:
                self._info_map[item.filename] = item
                self._info_list.append(item)
            elif len(self._info_list) > 0:
                # final crc is in last block
                old = self._info_list[-1]
                old.CRC = item.CRC
                old._md_expect = item._md_expect
                old.blake2sp_hash = item.blake2sp_hash
                old.compress_size += item.compress_size
        elif item.block_type == RAR5_BLOCK_SERVICE:
            if item.filename == 'CMT':
                self._load_comment(fd, item)

    def _load_comment(self, fd, item):
        if item.block_flags & (RAR5_BLOCK_FLAG_SPLIT_BEFORE | RAR5_BLOCK_FLAG_SPLIT_AFTER):
            return None
        if item.compress_type != RAR_M0:
            return None

        if item.flags & RAR_FILE_PASSWORD:
            algo, ___flags, kdf_count, salt, iv, ___checkval = item.file_encryption
            if algo != RAR5_XENC_CIPHER_AES256:
                return None
            key = self._gen_key(kdf_count, salt)
            f = HeaderDecrypt(fd, key, iv)
            cmt = f.read(item.file_size)
        else:
            # archive comment
            with self._open_clear(item) as cmtstream:
                cmt = cmtstream.read()

        # rar bug? - appends zero to comment
        cmt = cmt.split(ZERO, 1)[0]
        self.comment = cmt.decode('utf8')

    def _open_hack(self, inf, psw):
        # len, type, blk_flags, flags
        main_hdr = b'\x03\x01\x00\x00'
        endarc_hdr = b'\x03\x05\x00\x00'
        main_hdr = S_LONG.pack(rar_crc32(main_hdr)) + main_hdr
        endarc_hdr = S_LONG.pack(rar_crc32(endarc_hdr)) + endarc_hdr
        return self._open_hack_core(inf, psw, RAR5_ID + main_hdr, endarc_hdr)

##
## Utility classes
##

class UnicodeFilename(object):
    """Handle RAR3 unicode filename decompression.
    """
    def __init__(self, name, encdata):
        self.std_name = bytearray(name)
        self.encdata = bytearray(encdata)
        self.pos = self.encpos = 0
        self.buf = bytearray()
        self.failed = 0

    def enc_byte(self):
        """Copy encoded byte."""
        try:
            c = self.encdata[self.encpos]
            self.encpos += 1
            return c
        except IndexError:
            self.failed = 1
            return 0

    def std_byte(self):
        """Copy byte from 8-bit representation."""
        try:
            return self.std_name[self.pos]
        except IndexError:
            self.failed = 1
            return ord('?')

    def put(self, lo, hi):
        """Copy 16-bit value to result."""
        self.buf.append(lo)
        self.buf.append(hi)
        self.pos += 1

    def decode(self):
        """Decompress compressed UTF16 value."""
        hi = self.enc_byte()
        flagbits = 0
        while self.encpos < len(self.encdata):
            if flagbits == 0:
                flags = self.enc_byte()
                flagbits = 8
            flagbits -= 2
            t = (flags >> flagbits) & 3
            if t == 0:
                self.put(self.enc_byte(), 0)
            elif t == 1:
                self.put(self.enc_byte(), hi)
            elif t == 2:
                self.put(self.enc_byte(), self.enc_byte())
            else:
                n = self.enc_byte()
                if n & 0x80:
                    c = self.enc_byte()
                    for _ in range((n & 0x7f) + 2):
                        lo = (self.std_byte() + c) & 0xFF
                        self.put(lo, hi)
                else:
                    for _ in range(n + 2):
                        self.put(self.std_byte(), 0)
        return self.buf.decode("utf-16le", "replace")


class RarExtFile(RawIOBase):
    """Base class for file-like object that :meth:`RarFile.open` returns.

    Provides public methods and common crc checking.

    Behaviour:
     - no short reads - .read() and .readinfo() read as much as requested.
     - no internal buffer, use io.BufferedReader for that.
    """

    #: Filename of the archive entry
    name = None

    def __init__(self, parser, inf):
        """Open archive entry.
        """
        super(RarExtFile, self).__init__()

        # standard io.* properties
        self.name = inf.filename
        self.mode = 'rb'

        self._parser = parser
        self._inf = inf
        self._fd = None
        self._remain = 0
        self._returncode = 0

        self._md_context = None

        self._open()

    def _open(self):
        if self._fd:
            self._fd.close()
        md_class = self._inf._md_class or NoHashContext
        self._md_context = md_class()
        self._fd = None
        self._remain = self._inf.file_size

    def read(self, cnt=None):
        """Read all or specified amount of data from archive entry."""

        # sanitize cnt
        if cnt is None or cnt < 0:
            cnt = self._remain
        elif cnt > self._remain:
            cnt = self._remain
        if cnt == 0:
            return EMPTY

        # actual read
        data = self._read(cnt)
        if data:
            self._md_context.update(data)
            self._remain -= len(data)
        if len(data) != cnt:
            raise BadRarFile("Failed the read enough data")

        # done?
        if not data or self._remain == 0:
            # self.close()
            self._check()
        return data

    def _check(self):
        """Check final CRC."""
        final = self._md_context.digest()
        exp = self._inf._md_expect
        if exp is None:
            return
        if final is None:
            return
        if self._returncode:
            check_returncode(self, '')
        if self._remain != 0:
            raise BadRarFile("Failed the read enough data")
        if final != exp:
            raise BadRarFile("Corrupt file - CRC check failed: %s - exp=%r got=%r" % (
                self._inf.filename, exp, final))

    def _read(self, cnt):
        """Actual read that gets sanitized cnt."""

    def close(self):
        """Close open resources."""

        super(RarExtFile, self).close()

        if self._fd:
            self._fd.close()
            self._fd = None

    def __del__(self):
        """Hook delete to make sure tempfile is removed."""
        self.close()

    def readinto(self, buf):
        """Zero-copy read directly into buffer.

        Returns bytes read.
        """
        raise NotImplementedError('readinto')

    def tell(self):
        """Return current reading position in uncompressed data."""
        return self._inf.file_size - self._remain

    def seek(self, ofs, whence=0):
        """Seek in data.

        On uncompressed files, the seeking works by actual
        seeks so it's fast.  On compresses files its slow
        - forward seeking happends by reading ahead,
        backwards by re-opening and decompressing from the start.
        """

        # disable crc check when seeking
        self._md_context = NoHashContext()

        fsize = self._inf.file_size
        cur_ofs = self.tell()

        if whence == 0:     # seek from beginning of file
            new_ofs = ofs
        elif whence == 1:   # seek from current position
            new_ofs = cur_ofs + ofs
        elif whence == 2:   # seek from end of file
            new_ofs = fsize + ofs
        else:
            raise ValueError('Invalid value for whence')

        # sanity check
        if new_ofs < 0:
            new_ofs = 0
        elif new_ofs > fsize:
            new_ofs = fsize

        # do the actual seek
        if new_ofs >= cur_ofs:
            self._skip(new_ofs - cur_ofs)
        else:
            # reopen and seek
            self._open()
            self._skip(new_ofs)
        return self.tell()

    def _skip(self, cnt):
        """Read and discard data"""
        while cnt > 0:
            if cnt > 8192:
                buf = self.read(8192)
            else:
                buf = self.read(cnt)
            if not buf:
                break
            cnt -= len(buf)

    def readable(self):
        """Returns True"""
        return True

    def writable(self):
        """Returns False.

        Writing is not supported.
        """
        return False

    def seekable(self):
        """Returns True.

        Seeking is supported, although it's slow on compressed files.
        """
        return True

    def readall(self):
        """Read all remaining data"""
        # avoid RawIOBase default impl
        return self.read()


class PipeReader(RarExtFile):
    """Read data from pipe, handle tempfile cleanup."""

    def __init__(self, rf, inf, cmd, tempfile=None):
        self._cmd = cmd
        self._proc = None
        self._tempfile = tempfile
        super(PipeReader, self).__init__(rf, inf)

    def _close_proc(self):
        if not self._proc:
            return
        if self._proc.stdout:
            self._proc.stdout.close()
        if self._proc.stdin:
            self._proc.stdin.close()
        if self._proc.stderr:
            self._proc.stderr.close()
        self._proc.wait()
        self._returncode = self._proc.returncode
        self._proc = None

    def _open(self):
        super(PipeReader, self)._open()

        # stop old process
        self._close_proc()

        # launch new process
        self._returncode = 0
        self._proc = custom_popen(self._cmd)
        self._fd = self._proc.stdout

        # avoid situation where unrar waits on stdin
        if self._proc.stdin:
            self._proc.stdin.close()

    def _read(self, cnt):
        """Read from pipe."""

        # normal read is usually enough
        data = self._fd.read(cnt)
        if len(data) == cnt or not data:
            return data

        # short read, try looping
        buf = [data]
        cnt -= len(data)
        while cnt > 0:
            data = self._fd.read(cnt)
            if not data:
                break
            cnt -= len(data)
            buf.append(data)
        return EMPTY.join(buf)

    def close(self):
        """Close open resources."""

        self._close_proc()
        super(PipeReader, self).close()

        if self._tempfile:
            try:
                os.unlink(self._tempfile)
            except OSError:
                pass
            self._tempfile = None

    def readinto(self, buf):
        """Zero-copy read directly into buffer."""
        cnt = len(buf)
        if cnt > self._remain:
            cnt = self._remain
        vbuf = memoryview(buf)
        res = got = 0
        while got < cnt:
            res = self._fd.readinto(vbuf[got : cnt])
            if not res:
                break
            self._md_context.update(vbuf[got : got + res])
            self._remain -= res
            got += res
        return got


class DirectReader(RarExtFile):
    """Read uncompressed data directly from archive.
    """
    _cur = None
    _cur_avail = None
    _volfile = None

    def _open(self):
        super(DirectReader, self)._open()

        self._volfile = self._inf.volume_file
        self._fd = XFile(self._volfile, 0)
        self._fd.seek(self._inf.header_offset, 0)
        self._cur = self._parser._parse_header(self._fd)
        self._cur_avail = self._cur.add_size

    def _skip(self, cnt):
        """RAR Seek, skipping through rar files to get to correct position
        """

        while cnt > 0:
            # next vol needed?
            if self._cur_avail == 0:
                if not self._open_next():
                    break

            # fd is in read pos, do the read
            if cnt > self._cur_avail:
                cnt -= self._cur_avail
                self._remain -= self._cur_avail
                self._cur_avail = 0
            else:
                self._fd.seek(cnt, 1)
                self._cur_avail -= cnt
                self._remain -= cnt
                cnt = 0

    def _read(self, cnt):
        """Read from potentially multi-volume archive."""

        buf = []
        while cnt > 0:
            # next vol needed?
            if self._cur_avail == 0:
                if not self._open_next():
                    break

            # fd is in read pos, do the read
            if cnt > self._cur_avail:
                data = self._fd.read(self._cur_avail)
            else:
                data = self._fd.read(cnt)
            if not data:
                break

            # got some data
            cnt -= len(data)
            self._cur_avail -= len(data)
            buf.append(data)

        if len(buf) == 1:
            return buf[0]
        return EMPTY.join(buf)

    def _open_next(self):
        """Proceed to next volume."""

        # is the file split over archives?
        if (self._cur.flags & RAR_FILE_SPLIT_AFTER) == 0:
            return False

        if self._fd:
            self._fd.close()
            self._fd = None

        # open next part
        self._volfile = self._parser._next_volname(self._volfile)
        fd = open(self._volfile, "rb", 0)
        self._fd = fd
        sig = fd.read(len(self._parser._expect_sig))
        if sig != self._parser._expect_sig:
            raise BadRarFile("Invalid signature")

        # loop until first file header
        while 1:
            cur = self._parser._parse_header(fd)
            if not cur:
                raise BadRarFile("Unexpected EOF")
            if cur.type in (RAR_BLOCK_MARK, RAR_BLOCK_MAIN):
                if cur.add_size:
                    fd.seek(cur.add_size, 1)
                continue
            if cur.orig_filename != self._inf.orig_filename:
                raise BadRarFile("Did not found file entry")
            self._cur = cur
            self._cur_avail = cur.add_size
            return True

    def readinto(self, buf):
        """Zero-copy read directly into buffer."""
        got = 0
        vbuf = memoryview(buf)
        while got < len(buf):
            # next vol needed?
            if self._cur_avail == 0:
                if not self._open_next():
                    break

            # length for next read
            cnt = len(buf) - got
            if cnt > self._cur_avail:
                cnt = self._cur_avail

            # read into temp view
            res = self._fd.readinto(vbuf[got : got + cnt])
            if not res:
                break
            self._md_context.update(vbuf[got : got + res])
            self._cur_avail -= res
            self._remain -= res
            got += res
        return got


class HeaderDecrypt(object):
    """File-like object that decrypts from another file"""
    def __init__(self, f, key, iv):
        self.f = f
        self.ciph = AES_CBC_Decrypt(key, iv)
        self.buf = EMPTY

    def tell(self):
        """Current file pos - works only on block boundaries."""
        return self.f.tell()

    def read(self, cnt=None):
        """Read and decrypt."""
        if cnt > 8 * 1024:
            raise BadRarFile('Bad count to header decrypt - wrong password?')

        # consume old data
        if cnt <= len(self.buf):
            res = self.buf[:cnt]
            self.buf = self.buf[cnt:]
            return res
        res = self.buf
        self.buf = EMPTY
        cnt -= len(res)

        # decrypt new data
        blklen = 16
        while cnt > 0:
            enc = self.f.read(blklen)
            if len(enc) < blklen:
                break
            dec = self.ciph.decrypt(enc)
            if cnt >= len(dec):
                res += dec
                cnt -= len(dec)
            else:
                res += dec[:cnt]
                self.buf = dec[cnt:]
                cnt = 0

        return res


# handle (filename|filelike) object
class XFile(object):
    """Input may be filename or file object.
    """
    __slots__ = ('_fd', '_need_close')

    def __init__(self, xfile, bufsize=1024):
        if is_filelike(xfile):
            self._need_close = False
            self._fd = xfile
            self._fd.seek(0)
        else:
            self._need_close = True
            self._fd = open(xfile, 'rb', bufsize)

    def read(self, n=None):
        """Read from file."""
        return self._fd.read(n)

    def tell(self):
        """Return file pos."""
        return self._fd.tell()

    def seek(self, ofs, whence=0):
        """Move file pos."""
        return self._fd.seek(ofs, whence)

    def readinto(self, dst):
        """Read into buffer."""
        return self._fd.readinto(dst)

    def close(self):
        """Close file object."""
        if self._need_close:
            self._fd.close()

    def __enter__(self):
        return self

    def __exit__(self, typ, val, tb):
        self.close()


class NoHashContext(object):
    """No-op hash function."""
    def __init__(self, data=None):
        """Initialize"""
    def update(self, data):
        """Update data"""
    def digest(self):
        """Final hash"""
    def hexdigest(self):
        """Hexadecimal digest."""


class CRC32Context(object):
    """Hash context that uses CRC32."""
    __slots__ = ['_crc']

    def __init__(self, data=None):
        self._crc = 0
        if data:
            self.update(data)

    def update(self, data):
        """Process data."""
        self._crc = rar_crc32(data, self._crc)

    def digest(self):
        """Final hash."""
        return self._crc

    def hexdigest(self):
        """Hexadecimal digest."""
        return '%08x' % self.digest()


class Blake2SP(object):
    """Blake2sp hash context.
    """
    __slots__ = ['_thread', '_buf', '_cur', '_digest']
    digest_size = 32
    block_size = 64
    parallelism = 8

    def __init__(self, data=None):
        self._buf = b''
        self._cur = 0
        self._digest = None
        self._thread = []

        for i in range(self.parallelism):
            ctx = self._blake2s(i, 0, i == (self.parallelism - 1))
            self._thread.append(ctx)

        if data:
            self.update(data)

    def _blake2s(self, ofs, depth, is_last):
        return blake2s(node_offset=ofs, node_depth=depth, last_node=is_last,
                       depth=2, inner_size=32, fanout=self.parallelism)

    def _add_block(self, blk):
        self._thread[self._cur].update(blk)
        self._cur = (self._cur + 1) % self.parallelism

    def update(self, data):
        """Hash data.
        """
        view = memoryview(data)
        bs = self.block_size
        if self._buf:
            need = bs - len(self._buf)
            if len(view) < need:
                self._buf += view.tobytes()
                return
            self._add_block(self._buf + view[:need].tobytes())
            view = view[need:]
        while len(view) >= bs:
            self._add_block(view[:bs])
            view = view[bs:]
        self._buf = view.tobytes()

    def digest(self):
        """Return final digest value.
        """
        if self._digest is None:
            if self._buf:
                self._add_block(self._buf)
                self._buf = EMPTY
            ctx = self._blake2s(0, 1, True)
            for t in self._thread:
                ctx.update(t.digest())
            self._digest = ctx.digest()
        return self._digest

    def hexdigest(self):
        """Hexadecimal digest."""
        return tohex(self.digest())

##
## Utility functions
##

S_LONG = Struct('<L')
S_SHORT = Struct('<H')
S_BYTE = Struct('<B')

S_BLK_HDR = Struct('<HBHH')
S_FILE_HDR = Struct('<LLBLLBBHL')
S_COMMENT_HDR = Struct('<HBBH')

def load_vint(buf, pos):
    """Load variable-size int."""
    limit = min(pos + 11, len(buf))
    res = ofs = 0
    while pos < limit:
        b = _byte_code(buf[pos])
        res += ((b & 0x7F) << ofs)
        pos += 1
        ofs += 7
        if b < 0x80:
            return res, pos
    raise BadRarFile('cannot load vint')

def load_byte(buf, pos):
    """Load single byte"""
    end = pos + 1
    if end > len(buf):
        raise BadRarFile('cannot load byte')
    return S_BYTE.unpack_from(buf, pos)[0], end

def load_le32(buf, pos):
    """Load little-endian 32-bit integer"""
    end = pos + 4
    if end > len(buf):
        raise BadRarFile('cannot load le32')
    return S_LONG.unpack_from(buf, pos)[0], pos + 4

def load_bytes(buf, num, pos):
    """Load sequence of bytes"""
    end = pos + num
    if end > len(buf):
        raise BadRarFile('cannot load bytes')
    return buf[pos : end], end

def load_vstr(buf, pos):
    """Load bytes prefixed by vint length"""
    slen, pos = load_vint(buf, pos)
    return load_bytes(buf, slen, pos)

def load_dostime(buf, pos):
    """Load LE32 dos timestamp"""
    stamp, pos = load_le32(buf, pos)
    tup = parse_dos_time(stamp)
    return to_datetime(tup), pos

def load_unixtime(buf, pos):
    """Load LE32 unix timestamp"""
    secs, pos = load_le32(buf, pos)
    dt = datetime.fromtimestamp(secs, UTC)
    return dt, pos

def load_windowstime(buf, pos):
    """Load LE64 windows timestamp"""
    # unix epoch (1970) in seconds from windows epoch (1601)
    unix_epoch = 11644473600
    val1, pos = load_le32(buf, pos)
    val2, pos = load_le32(buf, pos)
    secs, n1secs = divmod((val2 << 32) | val1, 10000000)
    dt = datetime.fromtimestamp(secs - unix_epoch, UTC)
    dt = dt.replace(microsecond=n1secs // 10)
    return dt, pos

# new-style next volume
def _next_newvol(volfile):
    i = len(volfile) - 1
    while i >= 0:
        if volfile[i] >= '0' and volfile[i] <= '9':
            return _inc_volname(volfile, i)
        i -= 1
    raise BadRarName("Cannot construct volume name: " + volfile)

# old-style next volume
def _next_oldvol(volfile):
    # rar -> r00
    if volfile[-4:].lower() == '.rar':
        return volfile[:-2] + '00'
    return _inc_volname(volfile, len(volfile) - 1)

# increase digits with carry, otherwise just increment char
def _inc_volname(volfile, i):
    fn = list(volfile)
    while i >= 0:
        if fn[i] != '9':
            fn[i] = chr(ord(fn[i]) + 1)
            break
        fn[i] = '0'
        i -= 1
    return ''.join(fn)

# rar3 extended time fields
def _parse_ext_time(h, data, pos):
    # flags and rest of data can be missing
    flags = 0
    if pos + 2 <= len(data):
        flags = S_SHORT.unpack_from(data, pos)[0]
        pos += 2

    mtime, pos = _parse_xtime(flags >> 3 * 4, data, pos, h.mtime)
    h.ctime, pos = _parse_xtime(flags >> 2 * 4, data, pos)
    h.atime, pos = _parse_xtime(flags >> 1 * 4, data, pos)
    h.arctime, pos = _parse_xtime(flags >> 0 * 4, data, pos)
    if mtime:
        h.mtime = mtime
        h.date_time = mtime.timetuple()[:6]
    return pos

# rar3 one extended time field
def _parse_xtime(flag, data, pos, basetime=None):
    res = None
    if flag & 8:
        if not basetime:
            basetime, pos = load_dostime(data, pos)

        # load second fractions
        rem = 0
        cnt = flag & 3
        for _ in range(cnt):
            b, pos = load_byte(data, pos)
            rem = (b << 16) | (rem >> 8)

        # convert 100ns units to microseconds
        usec = rem // 10
        if usec > 1000000:
            usec = 999999

        # dostime has room for 30 seconds only, correct if needed
        if flag & 4 and basetime.second < 59:
            res = basetime.replace(microsecond=usec, second=basetime.second + 1)
        else:
            res = basetime.replace(microsecond=usec)
    return res, pos

def is_filelike(obj):
    """Filename or file object?
    """
    if isinstance(obj, str) or isinstance(obj, unicode):
        return False
    res = True
    for a in ('read', 'tell', 'seek'):
        res = res and hasattr(obj, a)
    if not res:
        raise ValueError("Invalid object passed as file")
    return True

def rar3_s2k(psw, salt):
    """String-to-key hash for RAR3.
    """
    if not isinstance(psw, unicode):
        psw = psw.decode('utf8')
    seed = psw.encode('utf-16le') + salt
    iv = EMPTY
    h = sha1()
    for i in range(16):
        for j in range(0x4000):
            cnt = S_LONG.pack(i * 0x4000 + j)
            h.update(seed + cnt[:3])
            if j == 0:
                iv += h.digest()[19:20]
    key_be = h.digest()[:16]
    key_le = pack("<LLLL", *unpack(">LLLL", key_be))
    return key_le, iv

def rar3_decompress(vers, meth, data, declen=0, flags=0, crc=0, psw=None, salt=None):
    """Decompress blob of compressed data.

    Used for data with non-standard header - eg. comments.
    """
    # already uncompressed?
    if meth == RAR_M0 and (flags & RAR_FILE_PASSWORD) == 0:
        return data

    # take only necessary flags
    flags = flags & (RAR_FILE_PASSWORD | RAR_FILE_SALT | RAR_FILE_DICTMASK)
    flags |= RAR_LONG_BLOCK

    # file header
    fname = b'data'
    date = 0
    mode = 0x20
    fhdr = S_FILE_HDR.pack(len(data), declen, RAR_OS_MSDOS, crc,
                           date, vers, meth, len(fname), mode)
    fhdr += fname
    if flags & RAR_FILE_SALT:
        if not salt:
            return EMPTY
        fhdr += salt

    # full header
    hlen = S_BLK_HDR.size + len(fhdr)
    hdr = S_BLK_HDR.pack(0, RAR_BLOCK_FILE, flags, hlen) + fhdr
    hcrc = rar_crc32(hdr[2:]) & 0xFFFF
    hdr = S_BLK_HDR.pack(hcrc, RAR_BLOCK_FILE, flags, hlen) + fhdr

    # archive main header
    mh = S_BLK_HDR.pack(0x90CF, RAR_BLOCK_MAIN, 0, 13) + ZERO * (2 + 4)

    # decompress via temp rar
    tmpfd, tmpname = mkstemp(suffix='.rar')
    tmpf = os.fdopen(tmpfd, "wb")
    try:
        tmpf.write(RAR_ID + mh + hdr + data)
        tmpf.close()

        cmd = [UNRAR_TOOL] + list(OPEN_ARGS)
        add_password_arg(cmd, psw, (flags & RAR_FILE_PASSWORD))
        cmd.append(tmpname)

        p = custom_popen(cmd)
        return p.communicate()[0]
    finally:
        tmpf.close()
        os.unlink(tmpname)

def to_datetime(t):
    """Convert 6-part time tuple into datetime object.
    """
    if t is None:
        return None

    # extract values
    year, mon, day, h, m, s = t

    # assume the values are valid
    try:
        return datetime(year, mon, day, h, m, s)
    except ValueError:
        pass

    # sanitize invalid values
    mday = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if mon < 1:
        mon = 1
    if mon > 12:
        mon = 12
    if day < 1:
        day = 1
    if day > mday[mon]:
        day = mday[mon]
    if h > 23:
        h = 23
    if m > 59:
        m = 59
    if s > 59:
        s = 59
    if mon == 2 and day == 29:
        try:
            return datetime(year, mon, day, h, m, s)
        except ValueError:
            day = 28
    return datetime(year, mon, day, h, m, s)

def parse_dos_time(stamp):
    """Parse standard 32-bit DOS timestamp.
    """
    sec, stamp = stamp & 0x1F, stamp >> 5
    mn,  stamp = stamp & 0x3F, stamp >> 6
    hr,  stamp = stamp & 0x1F, stamp >> 5
    day, stamp = stamp & 0x1F, stamp >> 5
    mon, stamp = stamp & 0x0F, stamp >> 4
    yr = (stamp & 0x7F) + 1980
    return (yr, mon, day, hr, mn, sec * 2)

def custom_popen(cmd):
    """Disconnect cmd from parent fds, read only from stdout.
    """
    # needed for py2exe
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = 0x08000000   # CREATE_NO_WINDOW

    # run command
    try:
        p = Popen(cmd, bufsize=0, stdout=PIPE, stdin=PIPE, stderr=STDOUT,
                  creationflags=creationflags)
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            raise RarCannotExec("Unrar not installed? (rarfile.UNRAR_TOOL=%r)" % UNRAR_TOOL)
        raise
    return p

def custom_check(cmd, ignore_retcode=False):
    """Run command, collect output, raise error if needed.
    """
    p = custom_popen(cmd)
    out, _ = p.communicate()
    if p.returncode and not ignore_retcode:
        raise RarExecError("Check-run failed")
    return out

def add_password_arg(cmd, psw, ___required=False):
    """Append password switch to commandline.
    """
    if UNRAR_TOOL == ALT_TOOL:
        return
    if psw is not None:
        cmd.append('-p' + psw)
    else:
        cmd.append('-p-')

def check_returncode(p, out):
    """Raise exception according to unrar exit code.
    """
    code = p.returncode
    if code == 0:
        return

    # map return code to exception class, codes from rar.txt
    errmap = [None,
              RarWarning, RarFatalError, RarCRCError, RarLockedArchiveError,    # 1..4
              RarWriteError, RarOpenError, RarUserError, RarMemoryError,        # 5..8
              RarCreateError, RarNoFilesError, RarWrongPassword]                # 9..11
    if UNRAR_TOOL == ALT_TOOL:
        errmap = [None]
    if code > 0 and code < len(errmap):
        exc = errmap[code]
    elif code == 255:
        exc = RarUserBreak
    elif code < 0:
        exc = RarSignalExit
    else:
        exc = RarUnknownError

    # format message
    if out:
        msg = "%s [%d]: %s" % (exc.__doc__, p.returncode, out)
    else:
        msg = "%s [%d]" % (exc.__doc__, p.returncode)

    raise exc(msg)

def hmac_sha256(key, data):
    """HMAC-SHA256"""
    return HMAC(key, data, sha256).digest()

def membuf_tempfile(memfile):
    """Write in-memory file object to real file."""
    memfile.seek(0, 0)

    tmpfd, tmpname = mkstemp(suffix='.rar')
    tmpf = os.fdopen(tmpfd, "wb")

    try:
        while True:
            buf = memfile.read(BSIZE)
            if not buf:
                break
            tmpf.write(buf)
        tmpf.close()
    except:
        tmpf.close()
        os.unlink(tmpname)
        raise
    return tmpname

class XTempFile(object):
    """Real file for archive.
    """
    __slots__ = ('_tmpfile', '_filename')

    def __init__(self, rarfile):
        if is_filelike(rarfile):
            self._tmpfile = membuf_tempfile(rarfile)
            self._filename = self._tmpfile
        else:
            self._tmpfile = None
            self._filename = rarfile

    def __enter__(self):
        return self._filename

    def __exit__(self, exc_type, exc_value, tb):
        if self._tmpfile:
            try:
                os.unlink(self._tmpfile)
            except OSError:
                pass
            self._tmpfile = None

#
# Check if unrar works
#

ORIG_UNRAR_TOOL = UNRAR_TOOL
ORIG_OPEN_ARGS = OPEN_ARGS
ORIG_EXTRACT_ARGS = EXTRACT_ARGS
ORIG_TEST_ARGS = TEST_ARGS

def _check_unrar_tool():
    global UNRAR_TOOL, OPEN_ARGS, EXTRACT_ARGS, TEST_ARGS
    try:
        # does UNRAR_TOOL work?
        custom_check([ORIG_UNRAR_TOOL], True)

        UNRAR_TOOL = ORIG_UNRAR_TOOL
        OPEN_ARGS = ORIG_OPEN_ARGS
        EXTRACT_ARGS = ORIG_EXTRACT_ARGS
        TEST_ARGS = ORIG_TEST_ARGS
    except RarCannotExec:
        try:
            # does ALT_TOOL work?
            custom_check([ALT_TOOL] + list(ALT_CHECK_ARGS), True)
            # replace config
            UNRAR_TOOL = ALT_TOOL
            OPEN_ARGS = ALT_OPEN_ARGS
            EXTRACT_ARGS = ALT_EXTRACT_ARGS
            TEST_ARGS = ALT_TEST_ARGS
        except RarCannotExec:
            # no usable tool, only uncompressed archives work
            pass

_check_unrar_tool()

