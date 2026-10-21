# coding=utf-8

from typing import Protocol, TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list['JsonValue'] | dict[str, 'JsonValue']
JsonObject: TypeAlias = dict[str, JsonValue]


class JsonResponse(Protocol):
    def json(self) -> JsonValue: ...


class ArrResponse(JsonResponse, Protocol):
    @property
    def content(self) -> bytes: ...

    @property
    def encoding(self) -> str | None: ...


class JsonLoader(Protocol):
    def loads(self, text: str, /) -> JsonValue: ...
