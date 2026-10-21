import decimal
from collections.abc import Callable
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
_ExtHookSig: TypeAlias = Callable[[int, memoryview], Any] | None
_DecHookSig: TypeAlias = Callable[[type[Any], Any], Any] | None
_DecimalFormatSig: TypeAlias = (
    Callable[[decimal.Decimal], Any] | Literal["string", "number"]
)

@final
class Ext:
    code: int
    data: Buffer
    def __init__(self, code: int, data: Buffer, /) -> None: ...

@final
class Decoder(Generic[_T]):
    type: Type[_T]  # needed for mypy, because of the same name
    strict: bool
    dec_hook: _DecHookSig
    ext_hook: _ExtHookSig
    @overload
    def __init__(
        self: Decoder[_T],
        type: Type[_T],
        *,
        strict: bool = True,
        dec_hook: _DecHookSig = None,
        ext_hook: _ExtHookSig = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Decoder[Any],
        type: Any = ...,
        *,
        strict: bool = True,
        dec_hook: _DecHookSig = None,
        ext_hook: _ExtHookSig = None,
    ) -> None: ...
    def decode(self, buf: Buffer, /) -> _T: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

@final
class Encoder:
    enc_hook: _EncHookSig
    decimal_format: _DecimalFormatSig
    uuid_format: Literal["canonical", "hex", "bytes"]
    order: Literal["deterministic", "sorted"] | None
    def __init__(
        self,
        *,
        enc_hook: _EncHookSig = None,
        decimal_format: _DecimalFormatSig = "string",
        uuid_format: Literal["canonical", "hex", "bytes"] = "canonical",
        order: Literal["deterministic", "sorted"] | None = None,
    ) -> None: ...
    def encode(self, obj: Any, /) -> bytes: ...
    def encode_into(self, obj: Any, buffer: bytearray, offset: int = 0, /) -> None: ...

@overload
def decode(
    buf: Buffer,
    /,
    *,
    type: type[_T],
    strict: bool = True,
    dec_hook: _DecHookSig = None,
    ext_hook: _ExtHookSig = None,
) -> _T: ...
@overload
def decode(
    buf: Buffer,
    /,
    *,
    type: Any = ...,
    strict: bool = True,
    dec_hook: _DecHookSig = None,
    ext_hook: _ExtHookSig = None,
) -> Any: ...
def encode(
    obj: Any,
    /,
    *,
    enc_hook: _EncHookSig = None,
    order: Literal["deterministic", "sorted"] | None = None,
) -> bytes: ...
