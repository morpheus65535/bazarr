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

from asio.file import DEFAULT_BUFFER_SIZE


class Interface(object):
    @classmethod
    def open(cls, file_path, parameters=None):
        raise NotImplementedError()

    @classmethod
    def get_size(cls, fp):
        raise NotImplementedError()

    @classmethod
    def get_path(cls, fp):
        raise NotImplementedError()

    @classmethod
    def seek(cls, fp, pointer, distance):
        raise NotImplementedError()

    @classmethod
    def read(cls, fp, n=DEFAULT_BUFFER_SIZE):
        raise NotImplementedError()

    @classmethod
    def close(cls, fp):
        raise NotImplementedError()
