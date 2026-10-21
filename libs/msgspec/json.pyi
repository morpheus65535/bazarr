import decimal
from collections.abc import Callable, Iterable
from types import GenericAlias
from typing import (
    Any,
    Generic,
    Literal,
    Type,
    TypeAlias,
    TypeVar,
    final,
    overload,
)

from typing_extensions import Buffer

_T = TypeVar("_T")

_EncHookSig: TypeAlias = Callable[[Any], Any] | None
_DecHookSig: TypeAlias = Callable[[type, Any], Any] | None
_FloatHookSig: TypeAlias = Callable[[str], Any] | None
_SchemaHookSig: TypeAlias = Callable[[type], dict[str, Any]] | None
_DecimalFormatSig: TypeAlias = (
    Callable[[decimal.Decimal], Any] | Literal["string", "number"]
)

@final
class Encoder:
    enc_hook: _EncHookSig
    decimal_format: _DecimalFormatSig
    uuid_format: Literal["canonical", "hex"]
    order: Literal["deterministic", "sorted"] | None

    def __init__(
        self,
        *,
        enc_hook: _EncHookSig = None,
        decimal_format: _DecimalFormatSig = "string",
        uuid_format: Literal["canonical", "hex"] = "canonical",
        order: Literal["deterministic", "sorted"] | None = None,
    ): ...
    def encode(self, obj: Any, /) -> bytes: ...
    def encode_lines(self, items: Iterable[Any], /) -> bytes: ...
    def encode_into(self, obj: Any, buffer: bytearray, offset: int = 0, /) -> None: ...

@final
class Decoder(Generic[_T]):
    type: Type[_T]  # needed for mypy, because of the same name
    strict: bool
    dec_hook: _DecHookSig
    float_hook: _FloatHookSig

    @overload
    def __init__(
        self: Decoder[_T],
        type: Type[_T],
        *,
        strict: bool = True,
        dec_hook: _DecHookSig = None,
        float_hook: _FloatHookSig = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Decoder[Any],
        type: Any = ...,
        *,
        strict: bool = True,
        dec_hook: _DecHookSig = None,
        float_hook: _FloatHookSig = None,
    ) -> None: ...
    def decode(self, buf: Buffer | str, /) -> _T: ...
    def decode_lines(self, buf: Buffer | str, /) -> list[_T]: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

@overload
def decode(
    buf: Buffer | str,
    /,
    *,
    type: type[_T],
    strict: bool = True,
    dec_hook: _DecHookSig = None,
) -> _T: ...
@overload
def decode(
    buf: Buffer | str,
    /,
    *,
    type: Any = ...,
    strict: bool = True,
    dec_hook: _DecHookSig = None,
) -> Any: ...
def encode(
    obj: Any,
    /,
    *,
    enc_hook: _EncHookSig = None,
    order: Literal["deterministic", "sorted"] | None = None,
) -> bytes: ...
def schema(
    type: Any,
    *,
    schema_hook: _SchemaHookSig = None,
    ref_template: str = "#/$defs/{name}",
) -> dict[str, Any]: ...
def schema_components(
    types: Iterable[Any],
    *,
    schema_hook: _SchemaHookSig = None,
    ref_template: str = "#/$defs/{name}",
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]: ...
@overload
def format(buf: str, *, indent: int = 2) -> str: ...
@overload
def format(buf: Buffer, *, indent: int = 2) -> bytes: ...
