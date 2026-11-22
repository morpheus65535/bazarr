#!/usr/bin/env python
"""
Quantities: Size
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from rebulk.remodule import re

from ..common import seps

if TYPE_CHECKING:
    from typing_extensions import Self


class Quantity:
    """
    Represent a quantity object with magnitude and units.
    """

    parser_re = re.compile(r"(?P<magnitude>\d+(?:[.]\d+)?)(?P<units>[^\d]+)?")

    def __init__(self, magnitude: int | float, units: str | None) -> None:
        self.magnitude = magnitude
        self.units = units

    @classmethod
    @abstractmethod
    def parse_units(cls, value: str | None) -> str:
        """
        Parse a string to a proper unit notation.
        """
        raise NotImplementedError

    @classmethod
    def fromstring(cls, string: str) -> Self:
        """
        Parse the string into a quantity object.
        :param string:
        :return:
        """
        match = cls.parser_re.match(string)
        assert match is not None
        values = match.groupdict()
        try:
            magnitude: int | float = int(values["magnitude"])
        except ValueError:
            magnitude = float(values["magnitude"])
        units = cls.parse_units(values["units"])

        return cls(magnitude, units)

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return str(self) == other
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.magnitude == other.magnitude and self.units == other.units

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} [{self}]>"

    def __str__(self) -> str:
        return f"{self.magnitude}{self.units}"


class Size(Quantity):
    """
    Represent size.

    e.g.: 1.1GB, 300MB
    """

    @classmethod
    def parse_units(cls, value: str | None) -> str:
        assert value is not None
        return value.strip(seps).upper()


class BitRate(Quantity):
    """
    Represent bit rate.

    e.g.: 320Kbps, 1.5Mbps
    """

    @classmethod
    def parse_units(cls, value: str | None) -> str:
        assert value is not None
        value = value.strip(seps).capitalize()
        for token in ("bits", "bit"):
            value = value.replace(token, "bps")

        return value


class FrameRate(Quantity):
    """
    Represent frame rate.

    e.g.: 24fps, 60fps
    """

    @classmethod
    def parse_units(cls, value: str | None) -> str:
        return "fps"
