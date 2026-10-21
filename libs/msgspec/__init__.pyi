import enum
from collections.abc import Callable, Iterable, Mapping
from inspect import Signature
from typing import (
    Any,
    ClassVar,
    Final,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    final,
    overload,
)

from typing_extensions import (
    Buffer,
    Self,
    TypeAlias,
    dataclass_transform,
    disjoint_base,
)

from . import inspect, json, msgpack, structs, toml, yaml

# PEP 673 explicitly rejects using Self in metaclass definitions:
# https://peps.python.org/pep-0673/#valid-locations-for-self
#
# Typeshed works around this by using a type variable as well:
# https://github.com/python/typeshed/blob/17bde1bd5e556de001adde3c2f340ba1c3581bd2/stdlib/abc.pyi#L14-L19
_SM = TypeVar("_SM", bound="StructMeta")

@disjoint_base
class StructMeta(type):
    __struct_fields__: ClassVar[tuple[str, ...]]
    __struct_defaults__: ClassVar[tuple[Any, ...]]
    __struct_encode_fields__: ClassVar[tuple[str, ...]]
    __match_args__: ClassVar[tuple[str, ...]]
    @property
    def __signature__(self) -> Signature: ...
    @property
    def __struct_config__(self) -> structs.StructConfig: ...
    def __new__(
        mcls: type[_SM],
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        *,
        tag: bool | str | int | Callable[[str], str | int] | None = None,
        tag_field: str | None = None,
        rename: (
            None
            | Literal["lower", "upper", "camel", "pascal", "kebab"]
            | Callable[[str], str | None]
            | Mapping[str, str]
        ) = None,
        omit_defaults: bool = False,
        forbid_unknown_fields: bool = False,
        frozen: bool = False,
        eq: bool = True,
        order: bool = False,
        kw_only: bool = False,
        repr_omit_defaults: bool = False,
        array_like: bool = False,
        gc: bool = True,
        weakref: bool = False,
        dict: bool = False,
        cache_hash: bool = False,
    ) -> _SM: ...

_T = TypeVar("_T")

@final
class UnsetType(enum.Enum):
    UNSET = "UNSET"
    def __bool__(self, /) -> Literal[False]: ...

UNSET: Final = UnsetType.UNSET

@final
class _NoDefault(enum.Enum):
    NODEFAULT = "NODEFAULT"

NODEFAULT: Final = _NoDefault.NODEFAULT

@overload
def field(*, default: _T, name: str | None = None) -> _T: ...
@overload
def field(*, default_factory: Callable[[], _T], name: str | None = None) -> _T: ...
@overload
def field(*, name: str | None = None) -> Any: ...

@dataclass_transform(field_specifiers=(field,))
class Struct(metaclass=StructMeta):
    __struct_fields__: ClassVar[tuple[str, ...]]
    __struct_defaults__: ClassVar[tuple[Any, ...]]
    __struct_config__: ClassVar[structs.StructConfig]
    __struct_encode_fields__: ClassVar[tuple[str, ...]]
    __match_args__: ClassVar[tuple[str, ...]]
    # A default __init__ so that Structs with unknown field types (say
    # constructed by `defstruct`) won't error on every call to `__init__`
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __init_subclass__(
        cls,
        tag: bool | str | int | Callable[[str], str | int] | None = None,
        tag_field: str | None = None,
        rename: (
            None
            | Literal["lower", "upper", "camel", "pascal", "kebab"]
            | Callable[[str], str | None]
            | Mapping[str, str]
        ) = None,
        omit_defaults: bool = False,
        forbid_unknown_fields: bool = False,
        frozen: bool = False,
        eq: bool = True,
        order: bool = False,
        kw_only: bool = False,
        repr_omit_defaults: bool = False,
        array_like: bool = False,
        gc: bool = True,
        weakref: bool = False,
        dict: bool = False,
        cache_hash: bool = False,
    ) -> None: ...
    def __rich_repr__(self, /) -> list[tuple[str, Any]]: ...
    def __replace__(self, /, **changes: Any) -> Self: ...

def defstruct(
    name: str,
    fields: Iterable[str | tuple[str, Any] | tuple[str, Any, Any]],
    *,
    bases: tuple[type[Any], ...] | None = None,
    module: str | None = None,
    namespace: dict[str, Any] | None = None,
    tag: bool | str | int | Callable[[str], str | int] | None = None,
    tag_field: str | None = None,
    rename: (
        None
        | Literal["lower", "upper", "camel", "pascal", "kebab"]
        | Callable[[str], str | None]
        | Mapping[str, str]
    ) = None,
    omit_defaults: bool = False,
    forbid_unknown_fields: bool = False,
    frozen: bool = False,
    eq: bool = True,
    order: bool = False,
    kw_only: bool = False,
    repr_omit_defaults: bool = False,
    array_like: bool = False,
    gc: bool = True,
    weakref: bool = False,
    dict: bool = False,
    cache_hash: bool = False,
) -> type[Struct]: ...

# Lie and say `Raw` is a subclass of `bytes`, so mypy will accept it in most
# places where an object that implements the buffer protocol is valid
@final
class Raw(bytes):
    @overload
    def __new__(cls) -> "Raw": ...
    @overload
    def __new__(cls, msg: Buffer | str, /) -> "Raw": ...
    def copy(self, /) -> "Raw": ...

#: We can't represent this in types, only via a name:
_NonNegativeInt: TypeAlias = int

@final
class Meta:
    # Numeric:
    # You can't mix:
    # - `gt` and `ge`
    # - `lt` and `le`
    @overload
    def __init__(
        self,
        *,
        gt: int | float | None = None,
        lt: int | float | None = None,
        multiple_of: int | float | None = None,
        title: str | None = None,
        description: str | None = None,
        examples: list[Any] | None = None,
        extra_json_schema: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        gt: int | float | None = None,
        le: int | float | None = None,
        multiple_of: int | float | None = None,
        title: str | None = None,
        description: str | None = None,
        examples: list[Any] | None = None,
        extra_json_schema: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        ge: int | float | None = None,
        lt: int | float | None = None,
        multiple_of: int | float | None = None,
        title: str | None = None,
        description: str | None = None,
        examples: list[Any] | None = None,
        extra_json_schema: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        ge: int | float | None = None,
        le: int | float | None = None,
        multiple_of: int | float | None = None,
        title: str | None = None,
        description: str | None = None,
        examples: list[Any] | None = None,
        extra_json_schema: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None: ...
    # Other:
    @overload
    def __init__(
        self,
        *,
        pattern: str | None = None,
        min_length: _NonNegativeInt | None = None,
        max_length: _NonNegativeInt | None = None,
        tz: bool | None = None,
        title: str | None = None,
        description: str | None = None,
        examples: list[Any] | None = None,
        extra_json_schema: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None: ...
    gt: Final[int | float | None]
    ge: Final[int | float | None]
    lt: Final[int | float | None]
    le: Final[int | float | None]
    multiple_of: Final[int | float | None]
    pattern: Final[str | None]
    min_length: Final[int | None]
    max_length: Final[int | None]
    tz: Final[bool | None]
    title: Final[str | None]
    description: Final[str | None]
    examples: Final[list[Any] | None]
    extra_json_schema: Final[dict[str, Any] | None]
    extra: Final[dict[str, Any] | None]
    def __rich_repr__(self, /) -> list[tuple[str, Any]]: ...

def to_builtins(
    obj: Any,
    *,
    str_keys: bool = False,
    builtin_types: Iterable[type[Any]] | None = None,
    enc_hook: Callable[[Any], Any] | None = None,
    order: Literal["deterministic", "sorted"] | None = None,
) -> Any: ...
@overload
def convert(
    obj: Any,
    type: type[_T],
    *,
    strict: bool = True,
    from_attributes: bool = False,
    dec_hook: Callable[[type[Any], Any], Any] | None = None,
    builtin_types: Iterable[type[Any]] | None = None,
    str_keys: bool = False,
) -> _T: ...
@overload
def convert(
    obj: Any,
    type: Any,
    *,
    strict: bool = True,
    from_attributes: bool = False,
    dec_hook: Callable[[type[Any], Any], Any] | None = None,
    builtin_types: Iterable[type[Any]] | None = None,
    str_keys: bool = False,
) -> Any: ...

class MsgspecError(Exception): ...
class EncodeError(MsgspecError): ...
class DecodeError(MsgspecError): ...
class ValidationError(DecodeError): ...

__version__: str
