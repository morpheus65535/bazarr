# coding=utf-8

from dataclasses import dataclass
from typing import Generic, TypeVar

import msgspec
import requests
from requests.compat import JSONDecodeError, json

from utilities.json_types import JsonValue
from utilities.arr_types import decode_display_text


Record = TypeVar('Record', bound=msgspec.Struct)


@dataclass(frozen=True, slots=True)
class InvalidArrRecord:
    value: JsonValue


class ArrRecordDecoder(Generic[Record]):
    def __init__(self, record_type: type[Record]) -> None:
        self.record_type = record_type
        self._record = msgspec.json.Decoder(record_type, dec_hook=decode_display_text)
        self._payload = msgspec.json.Decoder(record_type | list[record_type] | None, dec_hook=decode_display_text)
        self._rows = msgspec.json.Decoder(list[msgspec.Raw])

    def _convert_record(self, value: JsonValue) -> Record | InvalidArrRecord:
        try:
            return msgspec.convert(value, type=self.record_type, dec_hook=decode_display_text)
        except msgspec.ValidationError:
            return InvalidArrRecord(value)

    def from_value(self, value: JsonValue) -> Record | list[Record | InvalidArrRecord] | InvalidArrRecord | None:
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

    def decode(self, data: bytes | str) -> Record | list[Record | InvalidArrRecord] | InvalidArrRecord | None:
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
            result: list[Record | InvalidArrRecord] = []
            for row in rows:
                try:
                    result.append(self._record.decode(row))
                except (msgspec.DecodeError, UnicodeDecodeError):
                    result.append(self._convert_record(self._json_value(row)))
            return result
        except (msgspec.DecodeError, UnicodeDecodeError):
            return self.from_value(self._json_value(data))

    def decode_response(self, response: requests.Response) -> Record | list[Record | InvalidArrRecord] | InvalidArrRecord | None:
        if response.encoding is None or response.encoding.lower() not in ('utf-8', 'utf8'):
            value: JsonValue = response.json()
            return self.from_value(value)
        return self.decode(response.content)

    def complete_from_value(self, value: JsonValue) -> Record | list[Record] | None:
        try:
            return msgspec.convert(value, type=self.record_type | list[self.record_type] | None,
                                   dec_hook=decode_display_text)
        except msgspec.ValidationError:
            return None

    def decode_complete(self, data: bytes | str) -> Record | list[Record] | None:
        try:
            return self._payload.decode(data)
        except (msgspec.DecodeError, UnicodeDecodeError):
            return self.complete_from_value(self._json_value(data))

    def decode_complete_response(self, response: requests.Response) -> Record | list[Record] | None:
        if response.encoding is None or response.encoding.lower() not in ('utf-8', 'utf8'):
            value: JsonValue = response.json()
            return self.complete_from_value(value)
        return self.decode_complete(response.content)
