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

import os


NULL = 0

if os.name == 'nt':
    from asio.interfaces.windows.interop import WindowsInterop


class WindowsInterface(Interface):
    @classmethod
    def open(cls, file_path, parameters=None):
        """
        :type file_path: str
        :rtype: asio.interfaces.windows.WindowsFile
        """
        if not parameters:
            parameters = {}

        return WindowsFile(WindowsInterop.create_file(
            file_path,
            parameters.get('desired_access', WindowsInterface.GenericAccess.READ),
            parameters.get('share_mode', WindowsInterface.ShareMode.ALL),
            parameters.get('creation_disposition', WindowsInterface.CreationDisposition.OPEN_EXISTING),
            parameters.get('flags_and_attributes', NULL)
        ))

    @classmethod
    def get_size(cls, fp):
        """
        :type fp: asio.interfaces.windows.WindowsFile
        :rtype: int
        """
        return WindowsInterop.get_file_size(fp.handle)

    @classmethod
    def get_path(cls, fp):
        """
        :type fp: asio.interfaces.windows.WindowsFile
        :rtype: str
        """

        if not fp.file_map:
            fp.file_map = WindowsInterop.create_file_mapping(fp.handle, WindowsInterface.Protection.READONLY)

        if not fp.map_view:
            fp.map_view = WindowsInterop.map_view_of_file(fp.file_map, WindowsInterface.FileMapAccess.READ, 1)

        file_name = WindowsInterop.get_mapped_file_name(fp.map_view)

        return file_name

    @classmethod
    def seek(cls, fp, offset, origin):
        """
        :type fp: asio.interfaces.windows.WindowsFile
        :type offset: int
        :type origin: int
        :rtype: int
        """

        return WindowsInterop.set_file_pointer(
            fp.handle,
            offset,
            origin
        )

    @classmethod
    def read(cls, fp, n=DEFAULT_BUFFER_SIZE):
        """
        :type fp: asio.interfaces.windows.WindowsFile
        :type n: int
        :rtype: str
        """
        return WindowsInterop.read(fp.handle, n)

    @classmethod
    def read_into(cls, fp, b):
        """
        :type fp: asio.interfaces.windows.WindowsFile
        :type b: str
        :rtype: int
        """
        return WindowsInterop.read_into(fp.handle, b)

    @classmethod
    def close(cls, fp):
        """
        :type fp: asio.interfaces.windows.WindowsFile
        :rtype: bool
        """
        if fp.map_view:
            WindowsInterop.unmap_view_of_file(fp.map_view)

        if fp.file_map:
            WindowsInterop.close_handle(fp.file_map)

        return bool(WindowsInterop.close_handle(fp.handle))

    class GenericAccess(object):
        READ = 0x80000000
        WRITE = 0x40000000
        EXECUTE = 0x20000000
        ALL = 0x10000000

    class ShareMode(object):
        READ = 0x00000001
        WRITE = 0x00000002
        DELETE = 0x00000004
        ALL = READ | WRITE | DELETE

    class CreationDisposition(object):
        CREATE_NEW = 1
        CREATE_ALWAYS = 2
        OPEN_EXISTING = 3
        OPEN_ALWAYS = 4
        TRUNCATE_EXISTING = 5

    class Attribute(object):
        READONLY = 0x00000001
        HIDDEN = 0x00000002
        SYSTEM = 0x00000004
        DIRECTORY = 0x00000010
        ARCHIVE = 0x00000020
        DEVICE = 0x00000040
        NORMAL = 0x00000080
        TEMPORARY = 0x00000100
        SPARSE_FILE = 0x00000200
        REPARSE_POINT = 0x00000400
        COMPRESSED = 0x00000800
        OFFLINE = 0x00001000
        NOT_CONTENT_INDEXED = 0x00002000
        ENCRYPTED = 0x00004000

    class Flag(object):
        WRITE_THROUGH = 0x80000000
        OVERLAPPED = 0x40000000
        NO_BUFFERING = 0x20000000
        RANDOM_ACCESS = 0x10000000
        SEQUENTIAL_SCAN = 0x08000000
        DELETE_ON_CLOSE = 0x04000000
        BACKUP_SEMANTICS = 0x02000000
        POSIX_SEMANTICS = 0x01000000
        OPEN_REPARSE_POINT = 0x00200000
        OPEN_NO_RECALL = 0x00100000
        FIRST_PIPE_INSTANCE = 0x00080000

    class Protection(object):
        NOACCESS = 0x01
        READONLY = 0x02
        READWRITE = 0x04
        WRITECOPY = 0x08
        EXECUTE = 0x10
        EXECUTE_READ = 0x20,
        EXECUTE_READWRITE = 0x40
        EXECUTE_WRITECOPY = 0x80
        GUARD = 0x100
        NOCACHE = 0x200
        WRITECOMBINE = 0x400

    class FileMapAccess(object):
        COPY = 0x0001
        WRITE = 0x0002
        READ = 0x0004
        ALL_ACCESS = 0x001f
        EXECUTE = 0x0020


class WindowsFile(File):
    platform_handler = WindowsInterface

    def __init__(self, handle, *args, **kwargs):
        super(WindowsFile, self).__init__(*args, **kwargs)

        self.handle = handle

        self.file_map = None
        self.map_view = None

    def readinto(self, b):
        return self.get_handler().read_into(self, b)

    def __str__(self):
        return "<asio_windows.WindowsFile file: %s>" % self.handle
