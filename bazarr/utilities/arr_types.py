# coding=utf-8

from typing import TypeAlias, TypedDict
import msgspec

from utilities.json_types import JsonValue


class Language(msgspec.Struct):
    name: str | None


class Quality(msgspec.Struct):
    name: str
    resolution: int | msgspec.UnsetType = msgspec.UNSET


class FileQuality(msgspec.Struct):
    quality: Quality


class ArrTag(TypedDict):
    id: int
    label: str


class DisplayText(str):
    """Preserve the existing string conversion of arbitrary JSON overview values."""

    __slots__: tuple[str, ...] = ()


class JsonInteger(int):
    __slots__: tuple[str, ...] = ()

    def __new__(cls, value: JsonValue) -> 'JsonInteger':
        return super().__new__(cls, msgspec.convert(value, type=int, strict=False))


Year: TypeAlias = JsonInteger


class RadarrFileSizeBytes(int):
    __slots__: tuple[str, ...] = ()

    def __new__(cls, value: JsonValue) -> 'RadarrFileSizeBytes':
        if isinstance(value, bool) or not isinstance(value, (int, str, float)):
            raise ValueError('File size must be a byte count')
        try:
            return super().__new__(cls, int(value))
        except (ValueError, OverflowError) as error:
            raise ValueError('Invalid file byte count') from error


def decode_arr_value(value_type: type[DisplayText] | type[JsonInteger] | type[RadarrFileSizeBytes], value: JsonValue) -> DisplayText | JsonInteger | RadarrFileSizeBytes:
    return value_type(value)
