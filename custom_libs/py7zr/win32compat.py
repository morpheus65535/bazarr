import pathlib
import stat
import sys
from logging import getLogger
from typing import Union

if sys.platform == "win32":
    import ctypes
    from ctypes.wintypes import BOOL, DWORD, HANDLE, LPCWSTR, LPDWORD, LPVOID, LPWSTR

    _stdcall_libraries = {}
    _stdcall_libraries['kernel32'] = ctypes.WinDLL('kernel32')
    CloseHandle = _stdcall_libraries['kernel32'].CloseHandle
    CreateFileW = _stdcall_libraries['kernel32'].CreateFileW
    DeviceIoControl = _stdcall_libraries['kernel32'].DeviceIoControl
    GetFileAttributesW = _stdcall_libraries['kernel32'].GetFileAttributesW
    OPEN_EXISTING = 3
    GENERIC_READ = 2147483648
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FSCTL_GET_REPARSE_POINT = 0x000900A8
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
    IO_REPARSE_TAG_SYMLINK = 0xA000000C
    MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16 * 1024

    def _check_bit(val: int, flag: int) -> bool:
        return bool(val & flag == flag)

    class SymbolicLinkReparseBuffer(ctypes.Structure):
        """ Implementing the below in Python:

        typedef struct _REPARSE_DATA_BUFFER {
            ULONG  ReparseTag;
            USHORT ReparseDataLength;
            USHORT Reserved;
            union {
                struct {
                    USHORT SubstituteNameOffset;
                    USHORT SubstituteNameLength;
                    USHORT PrintNameOffset;
                    USHORT PrintNameLength;
                    ULONG Flags;
                    WCHAR PathBuffer[1];
                } SymbolicLinkReparseBuffer;
                struct {
                    USHORT SubstituteNameOffset;
                    USHORT SubstituteNameLength;
                    USHORT PrintNameOffset;
                    USHORT PrintNameLength;
                    WCHAR PathBuffer[1];
                } MountPointReparseBuffer;
                struct {
                    UCHAR  DataBuffer[1];
                } GenericReparseBuffer;
            } DUMMYUNIONNAME;
        } REPARSE_DATA_BUFFER, *PREPARSE_DATA_BUFFER;
        """
        # See https://docs.microsoft.com/en-us/windows-hardware/drivers/ddi/content/ntifs/ns-ntifs-_reparse_data_buffer
        _fields_ = [
            ('flags', ctypes.c_ulong),
            ('path_buffer', ctypes.c_byte * (MAXIMUM_REPARSE_DATA_BUFFER_SIZE - 20))
        ]

    class MountReparseBuffer(ctypes.Structure):
        _fields_ = [
            ('path_buffer', ctypes.c_byte * (MAXIMUM_REPARSE_DATA_BUFFER_SIZE - 16)),
        ]

    class ReparseBufferField(ctypes.Union):
        _fields_ = [
            ('symlink', SymbolicLinkReparseBuffer),
            ('mount', MountReparseBuffer)
        ]

    class ReparseBuffer(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [
            ('reparse_tag', ctypes.c_ulong),
            ('reparse_data_length', ctypes.c_ushort),
            ('reserved', ctypes.c_ushort),
            ('substitute_name_offset', ctypes.c_ushort),
            ('substitute_name_length', ctypes.c_ushort),
            ('print_name_offset', ctypes.c_ushort),
            ('print_name_length', ctypes.c_ushort),
            ('u', ReparseBufferField)
        ]

    def is_reparse_point(path: Union[str, pathlib.Path]) -> bool:
        GetFileAttributesW.argtypes = [LPCWSTR]
        GetFileAttributesW.restype = DWORD
        return _check_bit(GetFileAttributesW(str(path)), stat.FILE_ATTRIBUTE_REPARSE_POINT)

    def readlink(path: Union[str, pathlib.Path]) -> Union[str, pathlib.WindowsPath]:
        # FILE_FLAG_OPEN_REPARSE_POINT alone is not enough if 'path'
        # is a symbolic link to a directory or a NTFS junction.
        # We need to set FILE_FLAG_BACKUP_SEMANTICS as well.
        # See https://docs.microsoft.com/en-us/windows/desktop/api/fileapi/nf-fileapi-createfilea

        # description from _winapi.c:601
        # /* REPARSE_DATA_BUFFER usage is heavily under-documented, especially for
        #  junction points. Here's what I've learned along the way:
        #  - A junction point has two components: a print name and a substitute
        #  name. They both describe the link target, but the substitute name is
        #  the physical target and the print name is shown in directory listings.
        #  - The print name must be a native name, prefixed with "\??\".
        #  - Both names are stored after each other in the same buffer (the
        #  PathBuffer) and both must be NUL-terminated.
        #  - There are four members defining their respective offset and length
        #  inside PathBuffer: SubstituteNameOffset, SubstituteNameLength,
        #  PrintNameOffset and PrintNameLength.
        #  - The total size we need to allocate for the REPARSE_DATA_BUFFER, thus,
        #  is the sum of:
        #  - the fixed header size (REPARSE_DATA_BUFFER_HEADER_SIZE)
        #  - the size of the MountPointReparseBuffer member without the PathBuffer
        #  - the size of the prefix ("\??\") in bytes
        #  - the size of the print name in bytes
        #  - the size of the substitute name in bytes
        #  - the size of two NUL terminators in bytes */

        target_is_path = isinstance(path, pathlib.Path)
        if target_is_path:
            target = str(path)
        else:
            target = path
        CreateFileW.argtypes = [LPWSTR, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE]
        CreateFileW.restype = HANDLE
        DeviceIoControl.argtypes = [HANDLE, DWORD, LPVOID, DWORD, LPVOID, DWORD, LPDWORD, LPVOID]
        DeviceIoControl.restype = BOOL
        handle = HANDLE(CreateFileW(target, GENERIC_READ, 0, None, OPEN_EXISTING,
                                    FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, 0))
        buf = ReparseBuffer()
        ret = DWORD(0)
        status = DeviceIoControl(handle, FSCTL_GET_REPARSE_POINT, None, 0, ctypes.byref(buf),
                                 MAXIMUM_REPARSE_DATA_BUFFER_SIZE, ctypes.byref(ret), None)
        CloseHandle(handle)
        if not status:
            logger = getLogger(__file__)
            logger.error("Failed IOCTL access to REPARSE_POINT {})".format(target))
            raise ValueError("not a symbolic link or access permission violation")

        if buf.reparse_tag == IO_REPARSE_TAG_SYMLINK:
            offset = buf.substitute_name_offset
            ending = offset + buf.substitute_name_length
            rpath = bytearray(buf.symlink.path_buffer)[offset:ending].decode('UTF-16-LE')
        elif buf.reparse_tag == IO_REPARSE_TAG_MOUNT_POINT:
            offset = buf.substitute_name_offset
            ending = offset + buf.substitute_name_length
            rpath = bytearray(buf.mount.path_buffer)[offset:ending].decode('UTF-16-LE')
        else:
            raise ValueError("not a symbolic link")
        # on posixmodule.c:7859 in py38, we do that
        # ```
        # else if (rdb->ReparseTag == IO_REPARSE_TAG_MOUNT_POINT)
        # {
        #    name = (wchar_t *)((char*)rdb->MountPointReparseBuffer.PathBuffer +
        #                       rdb->MountPointReparseBuffer.SubstituteNameOffset);
        #    nameLen = rdb->MountPointReparseBuffer.SubstituteNameLength / sizeof(wchar_t);
        # }
        # else
        # {
        #    PyErr_SetString(PyExc_ValueError, "not a symbolic link");
        # }
        # if (nameLen > 4 && wcsncmp(name, L"\\??\\", 4) == 0) {
        #             /* Our buffer is mutable, so this is okay */
        #             name[1] = L'\\';
        #         }
        # ```
        # so substitute prefix here.
        if rpath.startswith('\\??\\'):
            rpath = '\\\\' + rpath[2:]
        if target_is_path:
            return pathlib.WindowsPath(rpath)
        else:
            return rpath
