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

from asio.file import SEEK_ORIGIN_CURRENT
from asio.file_opener import FileOpener
from asio.open_parameters import OpenParameters
from asio.interfaces.posix import PosixInterface
from asio.interfaces.windows import WindowsInterface

import os


class ASIO(object):
    platform_handler = None

    @classmethod
    def get_handler(cls):
        if cls.platform_handler:
            return cls.platform_handler

        if os.name == 'nt':
            cls.platform_handler = WindowsInterface
        elif os.name == 'posix':
            cls.platform_handler = PosixInterface
        else:
            raise NotImplementedError()

        return cls.platform_handler

    @classmethod
    def open(cls, file_path, opener=True, parameters=None):
        """Open file

        :type file_path: str

        :param opener: Use FileOpener, for use with the 'with' statement
        :type opener: bool

        :rtype: asio.file.File
        """
        if not parameters:
            parameters = OpenParameters()

        if opener:
            return FileOpener(file_path, parameters)

        return ASIO.get_handler().open(
            file_path,
            parameters=parameters.handlers.get(ASIO.get_handler())
        )
