from __future__ import annotations  # WARNING: remove this when debugging

from types import NoneType
from typing import Annotated
from typing import TypeVar
from typing import Union

from dynaconf.utils.functional import empty

from .compat import get_annotations

T = TypeVar("T")


class NotRequiredMarker:
    __slots__ = ()


NotRequired = Annotated[T, NotRequiredMarker()]
"""
This type will mark keys as NotRequired which means it can be completely
absent from the settings object.
This differs from Optional, as Optional requires T or None,
NotRequired requires T or simply nothing at all.
In practice this will make the generated Validator to have required=False
and skip the check for a default value, so settings.key will raise for
AttributeError.

When used as `NotRequired[T]`
    _type = T, _type_args = (_NotRequiredMarker(),)
When uses as `Annotated[NotRequired[T], Validator()]`
    _type = T
    _type_args (_NotRequiredMarker(), Validator())

"""


class DictValue:
    """DictValue represents a Typed Dict in the settings.

    When instantiating just returns a dict containing the default values only,
    this type does not performs any validation.
    """

    __slots__ = ()
    _dynaconf_dictvalue = True  # a marker for validator_conditions.is_type_of

    def __new__(cls, **kwargs):
        defaults = {}
        schema_annotations = get_annotations(cls)
        for name, annotation in schema_annotations.items():
            value = getattr(cls, name, empty)
            if value is not empty:
                defaults[name] = value
        defaults.update(kwargs)
        return defaults


"""
Aliases for supported types
That can be used with Annotated, Union and T[T]
These are defined here mainly to help with auto complete

    from dynaconf.typed import types as ts
    class Settings(Dynaconf):
        field: ts.Str
        # actually the same as
        field: str

"""
Str = str
Int = int
Float = float
Bool = bool
List = list
Tuple = tuple
Dict = dict
Numeric = Union[int, float]

SUPPORTED_TYPES = (
    Str,
    Int,
    Float,
    Bool,
    NoneType,
    List,
    Tuple,
    Dict,
    DictValue,
)
