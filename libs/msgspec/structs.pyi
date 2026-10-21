from typing import Any, TypeVar, final

from . import NODEFAULT, Struct

__all__ = (
    "FieldInfo",
    "StructConfig",
    "asdict",
    "astuple",
    "fields",
    "force_setattr",
    "replace",
)

_S = TypeVar("_S", bound=Struct)

def replace(struct: _S, /, **changes: Any) -> _S: ...
def asdict(struct: Struct, /) -> dict[str, Any]: ...
def astuple(struct: Struct, /) -> tuple[Any, ...]: ...
def force_setattr(struct: Struct, name: str, value: Any, /) -> None: ...

@final
class StructConfig:
    frozen: bool
    eq: bool
    order: bool
    array_like: bool
    gc: bool
    repr_omit_defaults: bool
    omit_defaults: bool
    forbid_unknown_fields: bool
    weakref: bool
    dict: bool
    cache_hash: bool
    tag: str | int | None
    tag_field: str | None

class FieldInfo(Struct):
    name: str
    encode_name: str
    type: Any
    default: Any = NODEFAULT
    default_factory: Any = NODEFAULT

    @property
    def required(self) -> bool: ...

def fields(type_or_instance: Struct | type[Struct]) -> tuple[FieldInfo, ...]: ...
