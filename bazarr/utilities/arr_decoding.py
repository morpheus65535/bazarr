# coding=utf-8

import re
from dataclasses import dataclass
from typing import Annotated, TYPE_CHECKING, Generic, Protocol, TypeAlias, TypeVar
from typing_extensions import TypeForm

from pydantic import Field, GetCoreSchemaHandler, TypeAdapter, ValidationError
from pydantic_core import CoreSchema, core_schema
import requests

from utilities.json_types import ArrResponse, JsonLoader, JsonValue


if TYPE_CHECKING:
    from json import JSONDecodeError as JSONDecodeError
    json: JsonLoader
else:
    from requests.compat import JSONDecodeError, json


def _json_accepts_nonstandard_numbers() -> bool:
    try:
        _ = json.loads('[NaN, Infinity, -Infinity]')
    except JSONDecodeError:
        return False
    return True


_CHECK_NONSTANDARD_NUMBERS = not _json_accepts_nonstandard_numbers()


class IncompleteRecord(Protocol):
    @property
    def id(self) -> int | None: ...


Record = TypeVar('Record')
Invalid = TypeVar('Invalid', bound=IncompleteRecord | None)


@dataclass(frozen=True)
class DefaultOnError(Generic[Record]):
    """Handle validation failures inside Pydantic without a Python callback."""

    default: Record

    def __get_pydantic_core_schema__(self, source_type: TypeForm[Record], handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.with_default_schema(handler(source_type), default=self.default, on_error='default')


CompleteResult: TypeAlias = list[Record] | Record | None
PartialResult: TypeAlias = Record | Invalid | list[Record | Invalid] | None
InvalidAsNone: TypeAlias = Annotated[Record | None, DefaultOnError[Record | None](None)]
# Try arrays before the fallback for an invalid individual record.
RecordPayload: TypeAlias = Annotated[
    CompleteResult[Record], Field(union_mode='left_to_right'), DefaultOnError[CompleteResult[Record]](None)]


JsonText = TypeVar('JsonText', str, bytes)

_NONSTANDARD_NUMBER = r'(?:NaN|Infinity)(?=\s*(?:$|[,\]}]))'
_NONSTANDARD_TEXT = re.compile(_NONSTANDARD_NUMBER)
_NONSTANDARD_BYTES = re.compile(_NONSTANDARD_NUMBER.encode('ascii'))


def _contains_nonstandard_number(data: JsonText, tokens: tuple[JsonText, ...], pattern: re.Pattern[JsonText]) -> bool:
    for token in tokens:
        offset = data.find(token)
        while offset != -1:
            if pattern.match(data, offset) is not None:
                return True
            offset = data.find(token, offset + len(token))
    return False


class ArrRecordDecoder(Generic[Record, Invalid]):
    def __init__(self, complete: TypeForm[CompleteResult[Record]],
                 partial: TypeForm[PartialResult[Record, Invalid]]) -> None:
        self._payload: TypeAdapter[CompleteResult[Record]] = TypeAdapter(complete)
        self._partial: TypeAdapter[PartialResult[Record, Invalid]] = TypeAdapter(partial)

    def from_value(self, value: JsonValue) -> PartialResult[Record, Invalid]:
        return self._partial.validate_python(value)

    @staticmethod
    def _json_value(data: bytes | str) -> JsonValue:
        # Preserve Requests' replacement decoding, JSON backend and error details.
        text = data if isinstance(data, str) else data.decode('utf-8', errors='replace')
        try:
            value: JsonValue = json.loads(text)
        except JSONDecodeError as error:
            raise requests.exceptions.JSONDecodeError(error.msg, error.doc, error.pos) from error
        return value

    @staticmethod
    def _may_have_nonstandard_number(data: bytes | str) -> bool:
        # Pydantic accepts these tokens even when Requests' JSON backend rejects them.
        if isinstance(data, bytes):
            return _contains_nonstandard_number(data, (b'NaN', b'Infinity'), _NONSTANDARD_BYTES)
        return _contains_nonstandard_number(data, ('NaN', 'Infinity'), _NONSTANDARD_TEXT)

    def decode(self, data: bytes | str) -> PartialResult[Record, Invalid]:
        if _CHECK_NONSTANDARD_NUMBERS and self._may_have_nonstandard_number(data):
            return self.from_value(self._json_value(data))
        try:
            return self._partial.validate_json(data)
        except ValidationError:
            return self.from_value(self._json_value(data))

    def decode_response(self, response: ArrResponse) -> PartialResult[Record, Invalid]:
        if response.encoding is None or response.encoding.lower() not in ('utf-8', 'utf8'):
            return self.from_value(response.json())
        return self.decode(response.content)

    def complete_from_value(self, value: JsonValue) -> CompleteResult[Record]:
        try:
            return self._payload.validate_python(value)
        except ValidationError:
            return None

    def decode_complete(self, data: bytes | str) -> CompleteResult[Record]:
        if _CHECK_NONSTANDARD_NUMBERS and self._may_have_nonstandard_number(data):
            return self.complete_from_value(self._json_value(data))
        try:
            return self._payload.validate_json(data)
        except ValidationError:
            return self.complete_from_value(self._json_value(data))

    def decode_complete_response(self, response: ArrResponse) -> CompleteResult[Record]:
        if response.encoding is None or response.encoding.lower() not in ('utf-8', 'utf8'):
            return self.complete_from_value(response.json())
        return self.decode_complete(response.content)
