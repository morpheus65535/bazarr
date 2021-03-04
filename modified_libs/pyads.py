# -*- coding: utf-8 -*-
'''
Copyright © 2015, Robin David - MIT-Licensed
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
The Software is provided "as is", without warranty of any kind, express or implied, including but not limited
to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall
the authors or copyright holders X be liable for any claim, damages or other liability, whether in an action
of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other
dealings in the Software.
Except as contained in this notice, the name of the Robin David shall not be used in advertising or otherwise
to promote the sale, use or other dealings in this Software without prior written authorization from the Robin David.
'''
from ctypes import *

import sys, os
kernel32 = windll.kernel32

LPSTR     = c_wchar_p
DWORD     = c_ulong
LONG      = c_ulong
WCHAR     = c_wchar * 296
LONGLONG  = c_longlong

class LARGE_INTEGER_UNION(Structure):
    _fields_ = [
        ("LowPart", DWORD),
        ("HighPart", LONG),]

class LARGE_INTEGER(Union):
    _fields_ = [
        ("large1", LARGE_INTEGER_UNION),
        ("large2", LARGE_INTEGER_UNION),
        ("QuadPart",    LONGLONG),
    ]

class WIN32_FIND_STREAM_DATA(Structure):
    _fields_ = [
        ("StreamSize", LARGE_INTEGER),
        ("cStreamName", WCHAR),
    ]
    '''
    typedef struct _WIN32_FIND_STREAM_DATA {
      LARGE_INTEGER StreamSize;
      WCHAR         cStreamName[MAX_PATH + 36];
    } WIN32_FIND_STREAM_DATA, *PWIN32_FIND_STREAM_DATA;
    '''

class ADS():
    def __init__(self, filename):
        self.filename = filename
        self.streams = self.init_streams()

    def init_streams(self):
        file_infos = WIN32_FIND_STREAM_DATA()
        streamlist = list()
        myhandler = kernel32.FindFirstStreamW (LPSTR(self.filename), 0, byref(file_infos), 0)
        '''
        HANDLE WINAPI FindFirstStreamW(
          __in        LPCWSTR lpFileName,
          __in        STREAM_INFO_LEVELS InfoLevel, (0 standard, 1 max infos)
          __out       LPVOID lpFindStreamData, (return information about file in a WIN32_FIND_STREAM_DATA if 0 is given in infos_level
          __reserved  DWORD dwFlags (Reserved for future use. This parameter must be zero.) cf: doc
        );
        https://msdn.microsoft.com/en-us/library/aa364424(v=vs.85).aspx
        '''

        if file_infos.cStreamName:
            streamname = file_infos.cStreamName.split(":")[1]
            if streamname: streamlist.append(streamname)

            while kernel32.FindNextStreamW(myhandler, byref(file_infos)):
                streamlist.append(file_infos.cStreamName.split(":")[1])

        kernel32.FindClose(myhandler) #Close the handle

        return streamlist

    def __iter__(self):
        return iter(self.streams)

    def has_streams(self):
        return len(self.streams) > 0

    def full_filename(self, stream):
        return "%s:%s" % (self.filename, stream)

    def add_stream_from_file(self, filename):
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                content = f.read()
            return self.add_stream_from_string(filename, content)
        else:
            print("Could not find file: {0}".format(filename))
            return False

    def add_stream_from_string(self, stream_name, string):
        fullname = self.full_filename(os.path.basename(stream_name))
        if os.path.exists(fullname):
            print("Stream name already exists")
            return False
        else:
            fd = open(fullname, "wb")
            fd.write(string)
            fd.close()
            self.streams.append(stream_name)
            return True

    def delete_stream(self, stream):
        try:
            os.remove(self.full_filename(stream))
            self.streams.remove(stream)
            return True
        except:
            return False

    def get_stream_content(self, stream):
        fd = open(self.full_filename(stream), "rb")
        content = fd.read()
        fd.close()
        return content
