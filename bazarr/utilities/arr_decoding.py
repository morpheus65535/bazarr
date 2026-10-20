# coding=utf-8

from collections.abc import Callable
from typing import Generic, TypeAlias, TypeVar

import msgspec
import requests
from requests.compat import JSONDecodeError, json

from utilities.json_types import JsonValue
from utilities.arr_types import decode_display_text


Record = TypeVar('Record', bound=msgspec.Struct)
Invalid = TypeVar('Invalid')


CompleteResult: TypeAlias = Record | list[Record] | None
PartialResult: TypeAlias = Record | Invalid | list[Record | Invalid] | None


class ArrRecordDecoder(Generic[Record, Invalid]):
    def __init__(self, record_type: type[Record], invalid_record: Callable[[JsonValue], Invalid]) -> None:
        self.record_type = record_type
        self.invalid_record = invalid_record
        self._record = msgspec.json.Decoder(record_type, dec_hook=decode_display_text)
        self._payload = msgspec.json.Decoder(record_type | list[record_type] | None, dec_hook=decode_display_text)
        self._rows = msgspec.json.Decoder(list[msgspec.Raw])

    def _convert_record(self, value: JsonValue) -> Record | Invalid:
        try:
            return msgspec.convert(value, type=self.record_type, dec_hook=decode_display_text)
        except msgspec.ValidationError:
            return self.invalid_record(value)

    def from_value(self, value: JsonValue) -> PartialResult[Record, Invalid]:
        if value is None:
            return None
        if isinstance(value, list):
            return [self._convert_record(row) for row in value]
        return self._convert_record(value)

    @staticmethod
    def _json_value(data: bytes | str | msgspec.Raw) -> JsonValue:
        # Match Requests' UTF-8 replacement and selected JSON backend on the
        # exceptional path, including non-standard JSON accepted by that backend.
        text = data if isinstance(data, str) else bytes(data).decode('utf-8', errors='replace')
        try:
            value: JsonValue = json.loads(text)
        except JSONDecodeError as error:
            raise requests.exceptions.JSONDecodeError(error.msg, error.doc, error.pos) from error
        return value

    def decode(self, data: bytes | str) -> PartialResult[Record, Invalid]:
        try:
            return self._payload.decode(data)
        except msgspec.ValidationError:
            # Decode valid rows directly even when another row is incomplete.
            # Raw views avoid constructing the unused fields of the valid rows.
            prefix = data.lstrip()[:1]
            if prefix not in (b'[', '['):
                return self.from_value(self._json_value(data))
            try:
                rows = self._rows.decode(data)
            except (msgspec.DecodeError, UnicodeDecodeError):
                return self.from_value(self._json_value(data))
            result: list[Record | Invalid] = []
            for row in rows:
                try:
                    result.append(self._record.decode(row))
                except (msgspec.DecodeError, UnicodeDecodeError):
                    result.append(self._convert_record(self._json_value(row)))
            return result
        except (msgspec.DecodeError, UnicodeDecodeError):
            return self.from_value(self._json_value(data))

    def decode_response(self, response: requests.Response) -> PartialResult[Record, Invalid]:
        if response.encoding is None or response.encoding.lower() not in ('utf-8', 'utf8'):
            value: JsonValue = response.json()
            return self.from_value(value)
        return self.decode(response.content)

    def complete_from_value(self, value: JsonValue) -> CompleteResult[Record]:
        try:
            return msgspec.convert(value, type=self.record_type | list[self.record_type] | None,
                                   dec_hook=decode_display_text)
        except msgspec.ValidationError:
            return None

    def decode_complete(self, data: bytes | str) -> CompleteResult[Record]:
        try:
            return self._payload.decode(data)
        except (msgspec.DecodeError, UnicodeDecodeError):
            return self.complete_from_value(self._json_value(data))

    def decode_complete_response(self, response: requests.Response) -> CompleteResult[Record]:
        if response.encoding is None or response.encoding.lower() not in ('utf-8', 'utf8'):
            value: JsonValue = response.json()
            return self.complete_from_value(value)
        return self.decode_complete(response.content)
