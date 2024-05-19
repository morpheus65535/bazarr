from dataclasses import dataclass
from typing import Tuple, Union
from enum import IntEnum


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


class Alignment(IntEnum):
    """
    An integer enum specifying text alignment

    The integer values correspond to Advanced SubStation Alpha definition (like on numpad).
    Note that the older SubStation Alpha (SSA) specification used different numbering schema.

    """
    BOTTOM_LEFT = 1
    BOTTOM_CENTER = 2
    BOTTOM_RIGHT = 3
    MIDDLE_LEFT = 4
    MIDDLE_CENTER = 5
    MIDDLE_RIGHT = 6
    TOP_LEFT = 7
    TOP_CENTER = 8
    TOP_RIGHT = 9

    @classmethod
    def from_ssa_alignment(cls, alignment: int) -> "Alignment":
        """Convert SSA alignment to ASS alignment"""
        return Alignment(SSA_ALIGNMENT.index(alignment) + 1)

    def to_ssa_alignment(self) -> int:
        """Convert ASS alignment to SSA alignment"""
        return SSA_ALIGNMENT[self.value - 1]


SSA_ALIGNMENT: Tuple[int, ...] = (1, 2, 3, 9, 10, 11, 5, 6, 7)


#: Version of the pysubs2 library.
VERSION = "1.7.1"


IntOrFloat = Union[int, float]
