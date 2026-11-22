from __future__ import annotations

# WARNING: remove the import above when debugging on Python 3.12
# otherwise type annotations will be stringified.
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from dynaconf.base import LazySettings
from dynaconf.base import Settings as BaseDynaconfSettings
from dynaconf.utils.functional import Empty
from dynaconf.utils.functional import empty
from dynaconf.validator import Validator as BaseValidator

from . import guards as gu
from . import types as ty
from . import utils as ut
from .compat import get_annotations

dclass_args = {"kw_only": True}


@dataclass(**dclass_args)
class Options:
    """Options to configure the initialization of typed.Dynaconf Object.

    All options are just bypassed to the Dynaconf `__init__` method,
    except those starting with `_`.

    Options starting with `_` are only used on `__new__` when building the
    new Dynaconf object, those values assumes opinionated defaults and rarely
    needs to be changed.
    """

    # NOTE: On a dataclass the sentinel must be a Type not an instance

    env: str | type = Empty
    environments: bool | type = Empty
    envvar_prefix: str | type = Empty
    env_switcher: str | type = Empty
    root_path: str | Path | type = Empty
    settings_files: list[str] | type = Empty
    settings_file: str | type = Empty
    load_dotenv: bool | type = Empty

    _trigger_validation: bool = True

    def as_dict(self):
        options_dict = asdict(self)
        options_dict = {
            k: v
            for k, v in options_dict.items()
            if (not k.startswith("_")) and v is not Empty
        }
        return options_dict


class Dynaconf(BaseDynaconfSettings):
    """Interface to create an instance of Dynaconf based on typing.

    This class is a builder for a new instance of Dynaconf with validators
    and default values extracted from subclass type annotations and attributes.
    """

    dynaconf_options: Options

    def __new__(cls, *args, **kwargs):
        gu.raise_for_invalid_class_variable(cls)
        options = getattr(cls, "dynaconf_options", Options())
        if not isinstance(options, Options):
            raise TypeError(
                "dynaconf_options must be an instance of `Options`"
            )
        defaults, validators = extract_defaults_and_validators_from_typing(cls)
        passed_in_validators = kwargs.pop("validators", [])
        validators += passed_in_validators

        init_options = options.as_dict()
        merged_defaults = ut.dict_merge(defaults, kwargs)
        init_options.update(merged_defaults)

        # Useful while writing tests, to be removed later.
        if kwargs.pop("_debug_mode", None):
            ut.dump_debug_info(init_options, validators)

        new_cls = LazySettings(*args, **init_options)
        new_cls.__annotations__ = cls.__annotations__

        if validators:
            new_cls.validators.register(*validators)

        # Trigger validation if not explicitly disabled
        if options._trigger_validation:
            new_cls.validators.validate_all()

        return cast(cls, new_cls)


def extract_defaults_and_validators_from_typing(
    schema_cls,
    path: tuple | None = None,
) -> tuple[dict, list]:
    """Extract defaults and validators from class type annotations."""
    path = path or tuple()
    defaults = {}
    validators = []
    for name, annotation in get_annotations(schema_cls).items():
        if name == "dynaconf_options":
            # In case someone does dynaconf_options: Options = Options(...)
            # That value is kept out of the schema validation
            continue

        # paths for error reporting only
        full_path = path + (name,)  # E.g, ("path", "to", "name")
        full_name = ".".join(full_path)  # E.g, path.to.name

        default_value = getattr(schema_cls, name, empty)

        _type, _type_args = ut.get_type_and_args(annotation)
        gu.raise_for_unsupported_type(full_name, _type, _type_args, annotation)
        gu.raise_for_optional_without_none(
            full_name, _type, _type_args, default_value, annotation
        )
        extra_validators = []
        validator = BaseValidator(name, is_type_of=annotation)
        required = default_value is empty and not ut.is_notrequired(annotation)
        if required:
            validator.must_exist = True

        # field: DictValue
        if ut.is_dict_value(annotation):
            gu.raise_for_invalid_default_type(
                full_name, default_value, annotation
            )
            items_defaults, items_validators = (
                extract_defaults_and_validators_from_typing(
                    annotation, full_path
                )
            )
            validator.items_validators = items_validators
            if items_defaults and not isinstance(default_value, Empty):
                default_value = ut.dict_merge(items_defaults, default_value)

        # field: Annotated[T, Validator(...)] or field: NotRequired[T]
        elif ut.is_annotated(annotation):
            gu.raise_for_invalid_default_type(full_name, default_value, _type)
            gu.raise_for_invalid_annotated_args(full_name, _type, _type_args)
            # set the annotated type for type checking
            validator.is_type_of = _type
            # Add all the extra validators added via Annotated args
            marked_not_required = False
            for _validator in _type_args:
                # NotRequired adds a marker in the _type_args
                if isinstance(_validator, ty.NotRequiredMarker):
                    marked_not_required = True
                    continue
                _validator.names = (name,)
                extra_validators.append(_validator)

            if ut.is_dict_value(_type):
                items_defaults, items_validators = (
                    extract_defaults_and_validators_from_typing(
                        _type, full_path
                    )
                )
                validator.items_validators = items_validators
                if not marked_not_required:
                    if items_defaults and default_value is empty:
                        default_value = {}
                    if isinstance(default_value, dict) and isinstance(
                        items_defaults, dict
                    ):
                        default_value = ut.dict_merge(
                            items_defaults, default_value
                        )

        # field: list[T]
        elif ut.is_enclosed_list(_type, _type_args):
            # NOTE: Should we really avoid multi args? list[T, T, T] ?
            inner_type, *more_types = _type_args
            gu.raise_for_invalid_amount_of_enclosed_types(
                full_name, _type, inner_type, more_types
            )
            gu.raise_for_invalid_default_type(
                full_name, default_value, annotation
            )
            if ut.is_dict_value(inner_type):
                items_defaults, items_validators = (
                    extract_defaults_and_validators_from_typing(
                        inner_type, full_path
                    )
                )
                if isinstance(default_value, list):
                    inner_defaults = []
                    for item in default_value:
                        inner_defaults.append(
                            ut.dict_merge(items_defaults, item)
                        )
                    default_value = inner_defaults
                validator.items_validators = items_validators

        # field: Optional[T]
        elif ut.is_optional(annotation):
            if ut.is_dict_value(_type_args[0]):
                gu.raise_for_invalid_default_type(
                    full_name, default_value, annotation
                )
                _, items_validators = (
                    extract_defaults_and_validators_from_typing(
                        _type_args[0], full_path
                    )
                )
                extra_validator = BaseValidator(
                    name,
                    items_validators=items_validators,
                    when=BaseValidator(name, is_type_of=ty.DictValue),
                )
                extra_validators.append(extra_validator)

        # field: T
        else:
            # NOTE: hook creation of validators for
            # Optional and Notrequired here
            ...

        validators.append(validator)
        validators.extend(extra_validators)
        if default_value is not empty:
            defaults[name] = default_value

    return defaults, validators
