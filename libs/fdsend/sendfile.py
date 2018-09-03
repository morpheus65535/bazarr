"""
sendfile.py: functions for sending static files

Copyright 2014-2015, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import time
import mimetypes

from bottle import (HTTPResponse, HTTPError, parse_date, parse_range_header,
                    request)

from .rangewrapper import range_iter


CHARSET = 'UTF-8'
TIMESTAMP_FMT = '%a, %d %b %Y %H:%M:%S GMT'
DEFAULT_WRAPPER = range_iter


def format_ts(seconds=None):
    """ Format timestamp expressed as seconds from epoch in RFC format

    The ``seconds`` are expected to be in seconds since Unix epoch.

    If the ``seconds`` argument is omitted, or is ``None``, the current time is
    used.
    """
    return time.strftime(TIMESTAMP_FMT, time.gmtime(seconds))


def send_file(fd, filename=None, size=None, timestamp=None, ctype=None,
              charset=CHARSET, attachment=False, wrapper=DEFAULT_WRAPPER):
    """ Send a file represented by file object

    This function constcuts a HTTPResponse object that uses a file descriptor
    as response body. The file descriptor is suppled as ``fd`` argument and it
    must have a ``read()`` method. ``ValueError`` is raised when this is not
    the case. It supports `byte serving`_ using Range header, and makes the
    best effort to set all appropriate headers. It also supports HEAD queries.

    Because we are dealing with file descriptors and not physical files, the
    user must also supply the file metadata such as filename, size, and
    timestamp.

    The ``filename`` argument is an arbitrary filename. It is used to guess the
    content type, and also to set the content disposition in case of
    attachments.

    The ``size`` argument is the payload size in bytes. If it is omitted, the
    content length header is not set, and byte serving does not work.

    The ``timestamp`` argument is the number of seconds since Unix epoch when
    the file was created or last modified. If this argument is omitted,
    If-Modified-Since request headers cannot be honored.

    To explicitly specify the content type, the ``ctype`` argument can be used.
    This should be a valid MIME type of the payload.

    Default encoding (used as charset parameter in Content-Type header) is
    'UTF-8'. This can be overridden by using the ``charset`` argument.

    The ``attachment`` argumnet can be set to ``True`` to add the
    Content-Dispositon response header. Value of the header is then set to the
    filename.

    The ``wrapper`` argument is used to wrap the file descriptor when doing
    byte serving. The default is to use ``fdsend.rangewrapper.RangeWrapper``
    class, but there are alternatives as ``fdsend.rangewrapper.range_iter`` and
    ``bottle._file_iter_range``. The wrappers provided by this package are
    written to specifically handle file handles that do not have a ``seek()``
    method. If this is not your case, you may safely use the bottle's wrapper.

    The primary difference between ``fdsend.rangewrapper.RangeWrapper`` and
    ``fdsend.rangewrapper.range_iter`` is that the former returns a file-like
    object with ``read()`` method, which may or may not increase performance
    when used on a WSGI server that supports ``wsgi.file_wrapper`` feature. The
    latter returns an iterator and the response is returned as is without the
    use of a ``file_wrapper``. This may have some benefits when it comes to
    memory usage.

    Benchmarking and profiling is the best way to determine which wrapper you
    want to use, or you need to implement your own.

    To implement your own wrapper, you need to create a callable or a class
    that takes the following arguments:

    - file descriptor
    - offset (in bytes from start of the file)
    - length (total number of bytes in the range)

    The return value of the wrapper must be either an iterable or file-like
    object that implements ``read()`` and ``close()`` methods with the usual
    semantics.

    The code is partly based on ``bottle.static_file``.

    .. _byte serving: https://tools.ietf.org/html/rfc2616#page-138
    """
    if not hasattr(fd, 'read'):
        raise ValueError("Object '{}' has no read() method".format(fd))

    headers = {}
    status = 200

    if not ctype and filename is not None:
        ctype, enc = mimetypes.guess_type(filename)
        if enc:
            headers['Content-Encoding'] = enc

    if ctype:
        if ctype.startswith('text/'):
            # We expect and assume all text files are encoded UTF-8. It's
            # broadcaster's job to ensure this is true.
            ctype += '; charset=%s' % charset
        headers['Content-Type'] = ctype

    if size:
        headers['Content-Length'] = size
        headers['Accept-Ranges'] = 'bytes'

    if timestamp:
        headers['Last-Modified'] = format_ts(timestamp)

        # Check if If-Modified-Since header is in request and respond early
        modsince = request.environ.get('HTTP_IF_MODIFIED_SINCE')
        modsince = modsince and parse_date(modsince.split(';')[0].strip())
        if modsince is not None and modsince >= timestamp:
            headers['Date'] = format_ts()
            return HTTPResponse(status=304, **headers)

    if attachment and filename:
        headers['Content-Disposition'] = 'attachment; filename="%s"' % filename

    if request.method == 'HEAD':
        # Request is a HEAD, so remove any fd body
        fd = ''

    ranges = request.environ.get('HTTP_RANGE')
    if size and ranges:
        ranges = list(parse_range_header(ranges, size))
        if not ranges:
            return HTTPError(416, 'Request Range Not Satisfiable')
        start, end = ranges[0]
        headers['Content-Range'] = 'bytes %d-%d/%d' % (start, end - 1, size)
        length = end - start
        headers['Content-Length'] = str(length)
        fd = wrapper(fd, start, length)
        status = 206

    return HTTPResponse(fd, status=status, **headers)
