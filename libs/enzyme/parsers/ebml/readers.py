# -*- coding: utf-8 -*-
from ...compat import bytes
from ...exceptions import ReadError, SizeError
from datetime import datetime, timedelta
from io import BytesIO
from struct import unpack


__all__ = ['read_element_id', 'read_element_size', 'read_element_integer', 'read_element_uinteger',
           'read_element_float', 'read_element_string', 'read_element_unicode', 'read_element_date',
           'read_element_binary']


def _read(stream, size):
    """Read the `stream` for *exactly* `size` bytes and raise an exception if
    less than `size` bytes are actually read

    :param stream: file-like object from which to read
    :param int size: number of bytes to read
    :raise ReadError: when less than `size` bytes are actually read
    :return: read data from the `stream`
    :rtype: bytes

    """
    data = stream.read(size)
    if len(data) < size:
        raise ReadError('Less than %d bytes read (%d)' % (size, len(data)))
    return data


def read_element_id(stream):
    """Read the Element ID

    :param stream: file-like object from which to read
    :raise ReadError: when not all the required bytes could be read
    :return: the id of the element
    :rtype: int

    """
    char = _read(stream, 1)
    byte = ord(char)
    if byte & 0x80:
        return byte
    elif byte & 0x40:
        return unpack('>H', char + _read(stream, 1))[0]
    elif byte & 0x20:
        b, h = unpack('>BH', char + _read(stream, 2))
        return b * 2 ** 16 + h
    elif byte & 0x10:
        return unpack('>L', char + _read(stream, 3))[0]
    else:
        ValueError('Not an Element ID')


def read_element_size(stream):
    """Read the Element Size

    :param stream: file-like object from which to read
    :raise ReadError: when not all the required bytes could be read
    :return: the size of element's data
    :rtype: int

    """
    char = _read(stream, 1)
    byte = ord(char)
    if byte & 0x80:
        return unpack('>B', bytes((byte ^ 0x80,)))[0]
    elif byte & 0x40:
        return unpack('>H', bytes((byte ^ 0x40,)) + _read(stream, 1))[0]
    elif byte & 0x20:
        b, h = unpack('>BH', bytes((byte ^ 0x20,)) + _read(stream, 2))
        return b * 2 ** 16 + h
    elif byte & 0x10:
        return unpack('>L', bytes((byte ^ 0x10,)) + _read(stream, 3))[0]
    elif byte & 0x08:
        b, l = unpack('>BL', bytes((byte ^ 0x08,)) + _read(stream, 4))
        return b * 2 ** 32 + l
    elif byte & 0x04:
        h, l = unpack('>HL', bytes((byte ^ 0x04,)) + _read(stream, 5))
        return h * 2 ** 32 + l
    elif byte & 0x02:
        b, h, l = unpack('>BHL', bytes((byte ^ 0x02,)) + _read(stream, 6))
        return b * 2 ** 48 + h * 2 ** 32 + l
    elif byte & 0x01:
        return unpack('>Q', bytes((byte ^ 0x01,)) + _read(stream, 7))[0]
    else:
        ValueError('Not an Element Size')


def read_element_integer(stream, size):
    """Read the Element Data of type :data:`INTEGER`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: the read integer
    :rtype: int

    """
    if size == 1:
        return unpack('>b', _read(stream, 1))[0]
    elif size == 2:
        return unpack('>h', _read(stream, 2))[0]
    elif size == 3:
        b, h = unpack('>bH', _read(stream, 3))
        return b * 2 ** 16 + h
    elif size == 4:
        return unpack('>l', _read(stream, 4))[0]
    elif size == 5:
        b, l = unpack('>bL', _read(stream, 5))
        return b * 2 ** 32 + l
    elif size == 6:
        h, l = unpack('>hL', _read(stream, 6))
        return h * 2 ** 32 + l
    elif size == 7:
        b, h, l = unpack('>bHL', _read(stream, 7))
        return b * 2 ** 48 + h * 2 ** 32 + l
    elif size == 8:
        return unpack('>q', _read(stream, 8))[0]
    else:
        raise SizeError(size)


def read_element_uinteger(stream, size):
    """Read the Element Data of type :data:`UINTEGER`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: the read unsigned integer
    :rtype: int

    """
    if size == 1:
        return unpack('>B', _read(stream, 1))[0]
    elif size == 2:
        return unpack('>H', _read(stream, 2))[0]
    elif size == 3:
        b, h = unpack('>BH', _read(stream, 3))
        return b * 2 ** 16 + h
    elif size == 4:
        return unpack('>L', _read(stream, 4))[0]
    elif size == 5:
        b, l = unpack('>BL', _read(stream, 5))
        return b * 2 ** 32 + l
    elif size == 6:
        h, l = unpack('>HL', _read(stream, 6))
        return h * 2 ** 32 + l
    elif size == 7:
        b, h, l = unpack('>BHL', _read(stream, 7))
        return b * 2 ** 48 + h * 2 ** 32 + l
    elif size == 8:
        return unpack('>Q', _read(stream, 8))[0]
    else:
        raise SizeError(size)


def read_element_float(stream, size):
    """Read the Element Data of type :data:`FLOAT`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: the read float
    :rtype: float

    """
    if size == 4:
        return unpack('>f', _read(stream, 4))[0]
    elif size == 8:
        return unpack('>d', _read(stream, 8))[0]
    else:
        raise SizeError(size)


def read_element_string(stream, size):
    """Read the Element Data of type :data:`STRING`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: the read ascii-decoded string
    :rtype: unicode

    """
    return _read(stream, size).decode('ascii')


def read_element_unicode(stream, size):
    """Read the Element Data of type :data:`UNICODE`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: the read utf-8-decoded string
    :rtype: unicode

    """
    return _read(stream, size).decode('utf-8')


def read_element_date(stream, size):
    """Read the Element Data of type :data:`DATE`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: the read date
    :rtype: datetime

    """
    if size != 8:
        raise SizeError(size)
    nanoseconds = unpack('>q', _read(stream, 8))[0]
    return datetime(2001, 1, 1, 0, 0, 0, 0, None) + timedelta(microseconds=nanoseconds // 1000)


def read_element_binary(stream, size):
    """Read the Element Data of type :data:`BINARY`

    :param stream: file-like object from which to read
    :param int size: size of element's data
    :raise ReadError: when not all the required bytes could be read
    :raise SizeError: if size is incorrect
    :return: raw binary data
    :rtype: bytes

    """
    return BytesIO(stream.read(size))
