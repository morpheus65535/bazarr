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

from io import RawIOBase
import time

DEFAULT_BUFFER_SIZE = 4096

SEEK_ORIGIN_BEGIN = 0
SEEK_ORIGIN_CURRENT = 1
SEEK_ORIGIN_END = 2


class ReadTimeoutError(Exception):
    pass


class File(RawIOBase):
    platform_handler = None

    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)

    def get_handler(self):
        """
        :rtype: asio.interfaces.base.Interface
        """
        if not self.platform_handler:
            raise ValueError()

        return self.platform_handler

    def get_size(self):
        """Get the current file size

        :rtype: int
        """
        return self.get_handler().get_size(self)

    def get_path(self):
        """Get the path of this file

        :rtype: str
        """
        return self.get_handler().get_path(self)

    def seek(self, offset, origin):
        """Sets a reference point of a file to the given value.

        :param offset: The point relative to origin to move
        :type offset: int

        :param origin: Reference point to seek (SEEK_ORIGIN_BEGIN, SEEK_ORIGIN_CURRENT, SEEK_ORIGIN_END)
        :type origin: int
        """
        return self.get_handler().seek(self, offset, origin)

    def read(self, n=-1):
        """Read up to n bytes from the object and return them.

        :type n: int
        :rtype: str
        """
        return self.get_handler().read(self, n)

    def readinto(self, b):
        """Read up to len(b) bytes into bytearray b and return the number of bytes read."""
        data = self.read(len(b))

        if data is None:
            return None

        b[:len(data)] = data
        return len(data)

    def close(self):
        """Close the file handle"""
        return self.get_handler().close(self)

    def readable(self, *args, **kwargs):
        return True
