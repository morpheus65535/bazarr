# coding=utf-8

import gzip
from zlib import Z_FINISH


__all__ = ["GeezipFile", "open", "Z_FINISH"]


def open(filename, mode="rb", compresslevel=9):
    """Shorthand for GzipFile(filename, mode, compresslevel).

    The filename argument is required; mode defaults to 'rb'
    and compresslevel defaults to 9.

    """
    return GeezipFile(filename, mode, compresslevel)


class GeezipFile(gzip.GzipFile):
    def close(self):
        fileobj = self.fileobj
        if fileobj is None:
            return
        self.fileobj = None
        try:
            if self.mode == gzip.WRITE:
                fileobj.write(self.compress.flush(Z_FINISH))
                gzip.write32u(fileobj, self.crc)
                # self.size may exceed 2GB, or even 4GB
                gzip.write32u(fileobj, self.size & 0xffffffffL)
                fileobj.flush()
        finally:
            myfileobj = self.myfileobj
            if myfileobj:
                self.myfileobj = None
                myfileobj.close()
