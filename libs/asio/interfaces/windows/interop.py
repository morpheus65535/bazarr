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

from ctypes.wintypes import *
from ctypes import *
import logging

log = logging.getLogger(__name__)


CreateFileW = windll.kernel32.CreateFileW
CreateFileW.argtypes = (LPCWSTR, DWORD, DWORD, c_void_p, DWORD, DWORD, HANDLE)
CreateFileW.restype = HANDLE

ReadFile = windll.kernel32.ReadFile
ReadFile.argtypes = (HANDLE, c_void_p, DWORD, POINTER(DWORD), HANDLE)
ReadFile.restype = BOOL


NULL = 0
MAX_PATH = 260
DEFAULT_BUFFER_SIZE = 4096
LPSECURITY_ATTRIBUTES = c_void_p


class WindowsInterop(object):
    ri_buffer = None

    @classmethod
    def create_file(cls, path, desired_access, share_mode, creation_disposition, flags_and_attributes):
        h = CreateFileW(
            path,
            desired_access,
            share_mode,
            NULL,
            creation_disposition,
            flags_and_attributes,
            NULL
        )

        error = GetLastError()
        if error != 0:
            raise Exception('[WindowsASIO.open] "%s"' % FormatError(error))

        return h

    @classmethod
    def read(cls, handle, buf_size=DEFAULT_BUFFER_SIZE):
        buf = create_string_buffer(buf_size)
        bytes_read = c_ulong(0)

        success = ReadFile(handle, buf, buf_size, byref(bytes_read), NULL)

        error = GetLastError()
        if error:
            log.debug('read_file - error: (%s) "%s"', error, FormatError(error))

        if not success and error:
            raise Exception('[WindowsInterop.read_file] (%s) "%s"' % (error, FormatError(error)))

        # Return if we have a valid buffer
        if success and bytes_read.value:
            return buf.value

        return None

    @classmethod
    def read_into(cls, handle, b):
        if cls.ri_buffer is None or len(cls.ri_buffer) < len(b):
            cls.ri_buffer = create_string_buffer(len(b))

        bytes_read = c_ulong(0)

        success = ReadFile(handle, cls.ri_buffer, len(b), byref(bytes_read), NULL)
        bytes_read = int(bytes_read.value)

        b[:bytes_read] = cls.ri_buffer[:bytes_read]

        error = GetLastError()
        
        if not success and error:
            raise Exception('[WindowsInterop.read_file] (%s) "%s"' % (error, FormatError(error)))

        # Return if we have a valid buffer
        if success and bytes_read:
            return bytes_read

        return None

    @classmethod
    def set_file_pointer(cls, handle, distance, method):
        pos_high = DWORD(NULL)

        result = windll.kernel32.SetFilePointer(
            handle,
            c_ulong(distance),
            byref(pos_high),
            DWORD(method)
        )

        if result == -1:
            raise Exception('[WindowsASIO.seek] INVALID_SET_FILE_POINTER: "%s"' % FormatError(GetLastError()))

        return result

    @classmethod
    def get_file_size(cls, handle):
        return windll.kernel32.GetFileSize(
            handle,
            DWORD(NULL)
        )

    @classmethod
    def close_handle(cls, handle):
        return windll.kernel32.CloseHandle(handle)

    @classmethod
    def create_file_mapping(cls, handle, protect, maximum_size_high=0, maximum_size_low=1):
        return HANDLE(windll.kernel32.CreateFileMappingW(
            handle,
            LPSECURITY_ATTRIBUTES(NULL),
            DWORD(protect),
            DWORD(maximum_size_high),
            DWORD(maximum_size_low),
            LPCSTR(NULL)
        ))

    @classmethod
    def map_view_of_file(cls, map_handle, desired_access, num_bytes, file_offset_high=0, file_offset_low=0):
        return HANDLE(windll.kernel32.MapViewOfFile(
            map_handle,
            DWORD(desired_access),
            DWORD(file_offset_high),
            DWORD(file_offset_low),
            num_bytes
        ))

    @classmethod
    def unmap_view_of_file(cls, view_handle):
        return windll.kernel32.UnmapViewOfFile(view_handle)

    @classmethod
    def get_mapped_file_name(cls, view_handle, translate_device_name=True):
        buf = create_string_buffer(MAX_PATH + 1)

        result = windll.psapi.GetMappedFileNameW(
            cls.get_current_process(),
            view_handle,
            buf,
            MAX_PATH
        )

        # Raise exception on error
        error = GetLastError()
        if result == 0:
            raise Exception(FormatError(error))

        # Retrieve a clean file name (skipping over NUL bytes)
        file_name = cls.clean_buffer_value(buf)

        # If we are not translating the device name return here
        if not translate_device_name:
            return file_name

        drives = cls.get_logical_drive_strings()

        # Find the drive matching the file_name device name
        translated = False
        for drive in drives:
            device_name = cls.query_dos_device(drive)

            if file_name.startswith(device_name):
                file_name = drive + file_name[len(device_name):]
                translated = True
                break

        if not translated:
            raise Exception('Unable to translate device name')

        return file_name

    @classmethod
    def get_logical_drive_strings(cls, buf_size=512):
        buf = create_string_buffer(buf_size)

        result = windll.kernel32.GetLogicalDriveStringsW(buf_size, buf)

        error = GetLastError()
        if result == 0:
            raise Exception(FormatError(error))

        drive_strings = cls.clean_buffer_value(buf)
        return [dr for dr in drive_strings.split('\\') if dr != '']

    @classmethod
    def query_dos_device(cls, drive, buf_size=MAX_PATH):
        buf = create_string_buffer(buf_size)

        result = windll.kernel32.QueryDosDeviceA(
            drive,
            buf,
            buf_size
        )

        return cls.clean_buffer_value(buf)

    @classmethod
    def get_current_process(cls):
        return HANDLE(windll.kernel32.GetCurrentProcess())

    @classmethod
    def clean_buffer_value(cls, buf):
        value = ""

        for ch in buf.raw:
            if ord(ch) != 0:
                value += ch

        return value
