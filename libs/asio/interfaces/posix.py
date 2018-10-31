# Copyright 2013 Dean Gardiner <gardiner91@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from asio.file import File, DEFAULT_BUFFER_SIZE
from asio.interfaces.base import Interface

import sys
import os

if os.name == 'posix':
    import select

    # fcntl is only required on darwin
    if sys.platform == 'darwin':
        import fcntl

F_GETPATH = 50


class PosixInterface(Interface):
    @classmethod
    def open(cls, file_path, parameters=None):
        """
        :type file_path: str
        :rtype: asio.interfaces.posix.PosixFile
        """
        if not parameters:
            parameters = {}

        if not parameters.get('mode'):
            parameters.pop('mode')

        if not parameters.get('buffering'):
            parameters.pop('buffering')

        fd = os.open(file_path, os.O_RDONLY | os.O_NONBLOCK)

        return PosixFile(fd)

    @classmethod
    def get_size(cls, fp):
        """
        :type fp: asio.interfaces.posix.PosixFile
        :rtype: int
        """
        return os.fstat(fp.fd).st_size

    @classmethod
    def get_path(cls, fp):
        """
        :type fp: asio.interfaces.posix.PosixFile
        :rtype: int
        """

        # readlink /dev/fd fails on darwin, so instead use fcntl F_GETPATH
        if sys.platform == 'darwin':
            return fcntl.fcntl(fp.fd, F_GETPATH, '\0' * 1024).rstrip('\0')

        # Use /proc/self/fd if available
        if os.path.lexists("/proc/self/fd/"):
            return os.readlink("/proc/self/fd/%s" % fp.fd)

        # Fallback to /dev/fd
        if os.path.lexists("/dev/fd/"):
            return os.readlink("/dev/fd/%s" % fp.fd)

        raise NotImplementedError('Environment not supported (fdescfs not mounted?)')

    @classmethod
    def seek(cls, fp, offset, origin):
        """
        :type fp: asio.interfaces.posix.PosixFile
        :type offset: int
        :type origin: int
        """
        os.lseek(fp.fd, offset, origin)

    @classmethod
    def read(cls, fp, n=DEFAULT_BUFFER_SIZE):
        """
        :type fp: asio.interfaces.posix.PosixFile
        :type n: int
        :rtype: str
        """
        r, w, x = select.select([fp.fd], [], [], 5)

        if r:
            return os.read(fp.fd, n)

        return None

    @classmethod
    def close(cls, fp):
        """
        :type fp: asio.interfaces.posix.PosixFile
        """
        os.close(fp.fd)


class PosixFile(File):
    platform_handler = PosixInterface

    def __init__(self, fd, *args, **kwargs):
        """
        :type fd: asio.file.File
        """
        super(PosixFile, self).__init__(*args, **kwargs)

        self.fd = fd

    def __str__(self):
        return "<asio_posix.PosixFile file: %s>" % self.fd
