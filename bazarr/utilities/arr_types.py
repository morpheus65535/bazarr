# coding=utf-8

from typing import TypedDict
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

    __slots__ = ()


def decode_display_text(text_type: type[DisplayText], value: JsonValue) -> DisplayText:
    return text_type(value)
