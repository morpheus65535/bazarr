# coding=utf-8

from dataclasses import dataclass
import re
from typing import Annotated, TypeAlias
from typing_extensions import TypedDict

from pydantic import BeforeValidator, Field, StrictInt, TypeAdapter

from utilities.json_types import JsonValue


def _present_integer(value: JsonValue) -> JsonValue:
    if value is None:
        raise ValueError('Expected an integer, got null')
    return value


# Omitted fields default to None; explicitly supplied nulls remain invalid.
OmittedInt: TypeAlias = Annotated[StrictInt | None, BeforeValidator(_present_integer)]


@dataclass(slots=True)
class Language:
    name: str | None


@dataclass(slots=True)
class Quality:
    name: str
    resolution: OmittedInt = None


@dataclass(slots=True)
class FileQuality:
    quality: Quality


class ArrTag(TypedDict):
    id: int
    label: str


_JSON_NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
_YEAR_NUMBER = TypeAdapter[int](int)


def _year_input(value: JsonValue) -> JsonValue:
    if isinstance(value, bool):
        raise ValueError('Year must be an integer')
    if isinstance(value, str):
        if not _JSON_NUMBER.fullmatch(value):
            raise ValueError('Year must be a JSON number')
        return _YEAR_NUMBER.validate_json(value)
    return value


def parse_file_size(value: JsonValue) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str, float)):
        raise ValueError('File size must be a byte count')
    try:
        return int(value)
    except (ValueError, OverflowError) as error:
        raise ValueError('Invalid file byte count') from error


DisplayText: TypeAlias = Annotated[str, BeforeValidator(str)]
Year: TypeAlias = Annotated[int, Field(strict=False), BeforeValidator(_year_input)]
RadarrFileSizeBytes: TypeAlias = Annotated[int, BeforeValidator(parse_file_size)]
