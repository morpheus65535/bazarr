from __future__ import annotations  # WARNING: remove this when debugging

from collections.abc import Callable
from typing import Annotated
from typing import get_args
from typing import get_origin
from typing import Union

from dynaconf.base import Settings as BaseDynaconfSettings
from dynaconf.validator import Validator as BaseValidator

from . import types as ty
from .compat import UnionType


def get_all_enclosed_types(inner_type):
    # # Handle list[Union...]
    if is_union(inner_type):
        all_types = get_args(inner_type)
    else:
        all_types = (inner_type,)
    return all_types


def get_type_name(_type):
    if name := getattr(_type, "__name__", None):
        return name
    return str(_type)


def get_type_and_args(annotation) -> tuple:
    """From annotation name: T[T, args] extract type, args."""
    _type_args: tuple = tuple()
    # _type from `field: T` or `field: list[T]`
    _type = get_origin(annotation) or annotation
    if _type is Annotated:
        _type, *_type_args = get_args(annotation)
    else:
        _type_args = get_args(annotation)
    return _type, _type_args


def is_notrequired(annotation):
    return is_annotated(annotation) and any(
        isinstance(item, ty.NotRequiredMarker) for item in get_args(annotation)
    )


def is_annotated(annotation):
    return get_origin(annotation) is Annotated


def is_dict_value(annotation):
    return isinstance(annotation, type) and issubclass(
        annotation, ty.DictValue
    )


def is_enclosed_list(_type, _type_args):
    return _type_args and _type in (list, tuple)


def is_union(annotation) -> bool:
    """Tell if an annotation is strictly Union."""
    return get_origin(annotation) in [Union, UnionType]


def is_optional(annotation) -> bool:
    """Tell if an annotation is strictly typing.Optional or Union[**, None]"""
    return is_union(annotation) and get_args(annotation)[1] is type(None)


def is_type(value) -> bool:
    _type = get_origin(value) or value
    return isinstance(_type, type) or is_union(value) or is_optional(value)


def condition_factory_for_list_items(validators, prefix, _type) -> Callable:
    """takes _type: T, generates a function to validate a value against it"""
    # IDEA:
    # Evaluate the possibility to replace this with a new attribute on a
    # validator that will validate against each internal item of a list
    # Validator("X", is_type_of=list, items=[Validator(is_type_of=int)])

    def validator_condition(values):
        if isinstance(_type, type) and issubclass(_type, ty.DictValue):
            for i, value in enumerate(values):
                for _validator in validators:
                    for k, v in _validator.messages.items():
                        _validator.messages[k] = v.replace(
                            "{name}", prefix + f"[{i}]." + "{name}"
                        )
                    _validator.validate(BaseDynaconfSettings(**value))
        else:
            for i, value in enumerate(values):
                _settings = BaseDynaconfSettings()
                _settings.set(prefix, value)
                _validator = BaseValidator(
                    prefix,
                    is_type_of=_type,
                )
                for k, v in _validator.messages.items():
                    _validator.messages[k] = v.replace(
                        "{name}", "{name}" + f"[{i}]"
                    )
                _validator.validate(_settings)

        # No validation error
        return True

    return validator_condition


def dict_merge(d1: dict, d2: dict) -> dict:
    """Takes two dictionaries d1 and d2 and merges their data

    Example:

        >>> d1 = {'name': 'John', 'profile': {'group': 1, 'team': 42}}
        >>> d2 = {'profile': {'username': 'jj', 'group': 2}}
        >>> d3 = dict_merge(d1, d2)
        >>> d3 == {'name': 'John', 'profile': {'group': 2, 'team': 42, 'username': 'jj'}}
    """
    if not isinstance(d2, dict):
        return d1

    merged = d1.copy()

    for key, value in d2.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = dict_merge(merged[key], value)
        else:
            merged[key] = value

    return merged


def dump_debug_info(init_options, validators):
    """Debug utility to be removed later"""
    dump = __builtins__["print"]  # cheat the linter

    dump("\n----- INIT DEFAULTS -----")
    __import__("pprint").pprint(init_options)
    dump("\n----- VALIDATORS -----")
    for i, validator in enumerate(validators, 1):
        dump("#" * 80)
        dump(validator.names[0].upper())
        dump(i, validator)

        def print_all_validators(v, prefix):
            if v.items_validators:
                dump(" " * len(prefix) + v.names[0].upper())
                dump(" " * len(prefix) + ("-" * 80))
            for n, item_v in enumerate(v.items_validators, 1):
                dump(" " * len(prefix), f"{prefix}.{n}", item_v)
                print_all_validators(item_v, f"{prefix}.{n}")

        print_all_validators(validator, prefix=str(i))
