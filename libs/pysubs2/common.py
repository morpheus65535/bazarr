from collections import namedtuple
import sys

_Color = namedtuple("Color", "r g b a")

class Color(_Color):
    """
    (r, g, b, a) namedtuple for 8-bit RGB color with alpha channel.

    All values are ints from 0 to 255.
    """
    def __new__(cls, r, g, b, a=0):
        for value in r, g, b, a:
            if value not in range(256):
                raise ValueError("Color channels must have values 0-255")

        return _Color.__new__(cls, r, g, b, a)

#: Version of the pysubs2 library.
VERSION = "0.2.3"


PY3 = sys.version_info.major == 3

if PY3:
    text_type = str
    binary_string_type = bytes
else:
    text_type = unicode
    binary_string_type = str
