"""
rangewrapper.py: produce file-like objects for reading file ranges

Copyright 2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import io


CHUNK = 1024 * 8


def emulate_seek(fd, offset, chunk=CHUNK):
    """ Emulates a seek on an object that does not support it

    The seek is emulated by reading and discarding bytes until specified offset
    is reached.

    The ``offset`` argument is in bytes from start of file. The ``chunk``
    argument can be used to adjust the size of the chunks in which read
    operation is performed. Larger chunks will reach the offset in less reads
    and cost less CPU but use more memory. Conversely, smaller chunks will be
    more memory efficient, but cause more read operations and more CPU usage.

    If chunk is set to None, then the ``offset`` amount of bytes is read at
    once. This is fastest but depending on the offset size, may use a lot of
    memory.

    Default chunk size is controlled by the ``fsend.rangewrapper.CHUNK``
    constant, which is 8KB by default.

    This function has no return value.
    """
    while chunk and offset > CHUNK:
        fd.read(chunk)
        offset -= chunk
    fd.read(offset)


def force_seek(fd, offset, chunk=CHUNK):
    """ Force adjustment of read cursort to specified offset

    This function takes a file descriptor ``fd`` and tries to seek to position
    specified by ``offset`` argument. If the descriptor does not support the
    ``seek()`` method, it will fall back to ``emulate_seek()``.

    The optional ``chunk`` argument can be used to adjust the chunk size for
    ``emulate_seek()``.
    """
    try:
        fd.seek(offset)
    except (AttributeError, io.UnsupportedOperation):
        # This file handle probably has no seek()
        emulate_seek(fd, offset, chunk)


def range_iter(fd, offset, length, chunk=CHUNK):
    """ Iterator generator that iterates over chunks in specified range

    This generator is meant to be used when returning file descriptor as a
    response to Range request (byte serving). It limits the reads to the region
    specified by ``offset`` (in bytes form start of the file) and ``limit``
    (number of bytes to read), and returns the file contents in chunks of
    ``chunk`` bytes.

    The read offset is set either by using the file descriptor's ``seek()``
    method, or by using ``emulate_seek()`` function if file descriptor does not
    implement ``seek()``.

    The file descriptor is automatically closed when iteration is finished.
    """
    force_seek(fd, offset, chunk)
    while length > 0:
        ret = fd.read(chunk)
        if not ret:
            return
        length -= chunk
        yield ret
    fd.close()


class RangeWrapper(object):
    """ Wrapper around file-like object to provide reading within range

    This class is specifically crafted to take advantage of
    ``wsgi.file_wrapper`` feature which is available in some WSGI wervers. The
    class mimics the file objects and internally adjusts the reads for a
    specified range.
    """

    chunk = CHUNK

    def __init__(self, fd, offset, length):
        """
        The ``RangeWrapper`` constructor takes three arguments. ``fd`` is the
        file descriptor, usually representing a file to be served (though it
        can be a file-like object such as a ``StringIO`` instance).

        The only requirement for the ``fd`` object is that it supports a
        ``read()`` method which takes a single positional integer argument and
        returns the number of bytes matching the argument value.

        If the file descriptor supports ``seek()`` method, it will be used to
        adjust the start offset (continue reading for more information).

        ``offset`` and ``length`` represent the range to which the wrapper
        should confine its reads. Upon initialization, the file descriptor's
        ``seek()`` method is automatically invoked so that the reads can start
        from this offset. If call to ``seek()`` method fails with
        ``AttributeError`` or ``io.UnsupportedOperation`` exceptions, the
        ``emulate_seek()`` function is invoked as a fallback. This reads the
        file in chunks until the offset it reached, and read chunks are
        discarded. This may sound a bit wasteful (and it really is), but in
        some cases it is the only option (e.g., stream compression such as ZIP
        DEFLATE does not allow seeking).
        """
        self.fd = fd
        self.offset = offset
        self.remaining = length
        force_seek(self.fd, self.offset, self.chunk)

    def read(self, size=None):
        """ Read a specified number of bytes from the file descriptor

        This method emulates the normal file descriptor's ``read()`` method and
        restricts the total number of bytes readable.

        If file descriptor is not present (e.g., ``close()`` method had been
        called), ``ValueError`` is raised.

        If ``size`` is omitted, or ``None``, or any other falsy value, read
        will be done up to the remaining length (constructor's ``length``
        argument minus the bytes that have been read previously).

        This method internally invokes the file descriptor's ``read()`` method,
        and the method must accept a single integer positional argument.
        """
        if not self.fd:
            raise ValueError('I/O on closed file')
        if not size:
            size = self.remaining
        size = min([self.remaining, size])
        if not size:
            return ''
        data = self.fd.read(size)
        self.remaining -= size
        return data

    def close(self):
        """ Close the file descriptor and dereference it

        This method attempts to close the file descriptor and sets the
        internal reference to the file descriptor object to ``None``. If the
        call to file descriptor's ``close()`` method fails due to file
        descriptor not providing the ``close`` attribute, this condition is
        silently ignored. In all other cases, exception is propagated to the
        caller.
        """
        try:
            self.fd.close()
        except AttributeError:
            pass
        self.fd = None
