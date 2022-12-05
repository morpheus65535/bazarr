from dataclasses import dataclass
from typing import Union


@dataclass(init=False)
class Color:
    """
    8-bit RGB color with alpha channel.

    All values are ints from 0 to 255.
    """
    r: int
    g: int
    b: int
    a: int = 0

    def __init__(self, r: int, g: int, b: int, a: int = 0):
        for value in r, g, b, a:
            if value not in range(256):
                raise ValueError("Color channels must have values 0-255")

        self.r = r
        self.g = g
        self.b = b
        self.a = a


#: Version of the pysubs2 library.
VERSION = "1.4.4"


IntOrFloat = Union[int, float]
