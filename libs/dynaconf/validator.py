from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from collections.abc import Sequence
from contextlib import suppress
from copy import deepcopy
from itertools import chain
from types import MappingProxyType
from typing import Any
from typing import get_args
from typing import TYPE_CHECKING

from dynaconf import validator_conditions
from dynaconf.utils import ensure_a_list
from dynaconf.utils.functional import empty
from dynaconf.utils.parse_conf import Lazy

if TYPE_CHECKING:
    from dynaconf.base import LazySettings  # noqa: F401
    from dynaconf.base import Settings


DEFAULT_CAST = lambda value: value  # noqa


EQUALITY_ATTRS = (
    "names",
    "must_exist",
    "when",
    "condition",
    "operations",
    "envs",
    "cast",
)


class ValidationError(Exception):
    """Raised when a validation fails"""

    def __init__(self, message: str, *args, **kwargs):
        self.details = kwargs.pop("details", [])
        super().__init__(message, *args, **kwargs)
        self.message = message


class Validator:
    """Validators are conditions attached to settings variables names
    or patterns::

        Validator('MESSAGE', must_exist=True, eq='Hello World')

    The above ensure MESSAGE is available in default env and
    is equal to 'Hello World'

    `names` are a one (or more) names or patterns::

        Validator('NAME')
        Validator('NAME', 'OTHER_NAME', 'EVEN_OTHER')
        Validator(r'^NAME', r'OTHER./*')

    The `operations` are::

        eq: value == other
        ne: value != other
        gt: value > other
        lt: value < other
        gte: value >= other
        lte: value <= other
        is_type_of: isinstance(value, type)
        is_in:  value in sequence
        is_not_in: value not in sequence
        identity: value is other
        cont: contain value in
        len_eq: len(value) == other
        len_ne: len(value) != other
        len_min: len(value) > other
        len_max: len(value) < other
        startswith: value.startswith(term)
        endswith:  value.endswith(term)

    `env` is which env to be checked, can be a list or
    default is used.

    `when` holds a validator and its return decides if validator runs or not::

        Validator('NAME', must_exist=True, when=Validator('OTHER', eq=2))
        # NAME is required only if OTHER eq to 2
        # When the very first thing to be performed when passed.
        # if no env is passed to `when` it is inherited

    `must_exist` controls existence checking (executed after when)::

        must_exist=True  — variable must be present; raises if absent
        must_exist=False — variable must be absent; raises if present
        must_exist=None  — no existence rule (default); absent variables
                           skip all further checks on that name

    `required` is an alias for `must_exist`.

    condition is a callable to be executed and return boolean::

       Validator('NAME', condition=lambda x: x == 1)
       # it is executed before operations.

    """

    default_messages = MappingProxyType(
        {
            "must_exist_true": "{name} is required in env {env}",
            "must_exist_false": "{name} cannot exists in env {env}",
            "condition": "{name} invalid for {function}({value}) in env {env}",
            "operations": (
                "{name} must {operation} {op_value} "
                "but it is {value} in env {env}"
            ),
            "combined": "combined validators failed {errors}",
        }
    )

    def __init__(
        self,
        *names: str,
        must_exist: bool | None = None,
        required: bool | None = None,  # alias for `must_exist`
        condition: Callable[[Any], bool] | None = None,
        when: Validator | None = None,
        env: str | Sequence[str] | None = None,
        messages: dict[str, str] | None = None,
        cast: Callable[[Any], Any] | None = None,
        default: Any | Callable[[Any, Validator], Any] | None = empty,
        description: str | None = None,
        apply_default_on_none: bool | None = False,
        items_validators: list[Validator] | None = None,
        **operations: Any,
    ) -> None:
        # Copy immutable MappingProxyType as a mutable dict
        self.messages = dict(self.default_messages)
        if messages:
            self.messages.update(messages)

        if when is not None and not isinstance(when, Validator):
            raise TypeError("when must be Validator instance")

        if condition is not None and not callable(condition):
            raise TypeError("condition must be callable")

        # in the case that:
        # * default is a Lazy object AND
        # * there isnt any validate operation to perform (that would require knowing the lazy value)
        # Then we shouldnt trigger the Lazy evaluation
        self.should_call_lazy = not all(
            (
                default,
                isinstance(default, Lazy),
                not must_exist,
                not required,
                not cast,
                not items_validators,
                not operations,
            )
        )

        self.names = names
        self.must_exist = must_exist if must_exist is not None else required
        self.condition = condition
        self.when = when
        self.cast = cast or DEFAULT_CAST
        self.operations = operations
        self.default = default
        self.description = description
        self.envs: Sequence[str] | None = None
        self.apply_default_on_none = apply_default_on_none
        self.items_validators = items_validators or []

        if isinstance(env, str):
            self.envs = [env]
        elif isinstance(env, (list, tuple)):
            self.envs = env

    def __repr__(self):
        _repr = f"{self.__class__.__name__}("
        _elements = []
        if len(self.names) > 1:
            _elements.append(f"{list(self.names)}")
        elif self.names:
            _elements.append(f"'{self.names[0]}'")
        if self.is_type_of:
            type_name = str(self.is_type_of)
            if not get_args(self.is_type_of):
                with suppress(Exception):
                    type_name = (
                        str(self.is_type_of)
                        .replace("<class '", "")
                        .replace("'>", "")
                        .strip("<>'")
                        .split(".")[-1]
                    )
            _elements.append(f"type={type_name}")
        if self.must_exist is not None:
            _elements.append(f"required={self.must_exist}")
        operations = {
            k: v for k, v in self.operations.items() if k != "is_type_of"
        }
        if operations:
            _elements.append(f"operations={self.operations}")
        if self.cast is not DEFAULT_CAST:
            _elements.append(f"cast={self.cast}")
        if self.condition:
            _elements.append(f"condition={self.condition}")
        if self.envs:
            _elements.append(f"env={self.envs}")
        if self.when:
            _elements.append(f"when={self.when}")
        if self.items_validators:
            _elements.append(f"items_validators={self.items_validators}")
        _repr += ", ".join(_elements)
        _repr += ")"
        return _repr

    @property
    def required(self) -> bool | None:
        return self.must_exist

    @required.setter
    def required(self, value: bool | None):
        self.must_exist = value

    @property
    def is_type_of(self):
        # See #585
        return self.operations.get("is_type_of")

    @is_type_of.setter
    def is_type_of(self, value):
        self.operations["is_type_of"] = value

    def __or__(self, other: Validator) -> CombinedValidator:
        return OrValidator(self, other, description=self.description)

    def __and__(self, other: Validator) -> CombinedValidator:
        return AndValidator(self, other, description=self.description)

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True

        if type(self).__name__ != type(other).__name__:
            return False

        identical_attrs = (
            getattr(self, attr) == getattr(other, attr)
            for attr in EQUALITY_ATTRS
        )
        if all(identical_attrs):
            return True

        return False

    def validate(
        self,
        settings: Settings | dict,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        variable_path: tuple | None = None,
    ) -> None:
        """Raise ValidationError if invalid"""
        # If only or exclude are not set, this value always passes startswith
        only = ensure_a_list(only or [""])
        if only and not isinstance(only[0], str):
            raise ValueError("'only' must be a string or list of strings.")

        exclude = ensure_a_list(exclude)
        if exclude and not isinstance(exclude[0], str):
            raise ValueError("'exclude' must be a string or list of strings.")

        current_env = getattr(settings, "current_env", "main")
        envs = self.envs or [current_env]

        # NOTE: Smells bad, must not mutate a validator
        if self.when is not None:
            try:
                # inherit env if not defined
                if self.when.envs is None:
                    self.when.envs = envs

                self.when.validate(settings, only=only, exclude=exclude)
            except ValidationError:
                # if when is invalid, return canceling validation flow
                return

        if only_current_env:
            if current_env.upper() in [s.upper() for s in envs]:
                self._validate_names(
                    settings,
                    current_env,
                    only=only,
                    exclude=exclude,
                    variable_path=variable_path,
                )
            return

        # If only using current_env, skip using_env decoration (reload)
        if len(envs) == 1 and envs[0].upper() == current_env.upper():
            self._validate_names(
                settings,
                current_env,
                only=only,
                exclude=exclude,
                variable_path=variable_path,
            )
            return

        for env in envs:
            if from_env := getattr(settings, "from_env", None):
                env_settings: Settings | dict = from_env(env)
            else:
                env_settings = settings

            self._validate_names(
                env_settings,
                only=only,
                exclude=exclude,
                variable_path=variable_path,
            )
            # merge source metadata into original settings for history inspect
            # use getattr to cheat mypy
            if (d1 := getattr(settings, "loaded_by_loaders")) and (
                d2 := getattr(env_settings, "loaded_by_loaders")
            ):
                d1 = settings.loaded_by_loaders  # type: ignore
                d2 = env_settings.loaded_by_loaders  # type: ignore
                d1.update(d2)

    def _validate_names(
        self,
        settings: Settings | dict,
        env: str | None = None,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        variable_path: tuple | None = None,
    ) -> None:
        if env is None and (
            current_env := getattr(settings, "current_env", None)
        ):
            env = current_env

        for name in self.names:
            # Skip if only is set and name isn't in the only list
            if only and not any(name.startswith(sub) for sub in only):
                continue

            # Skip if exclude is set and name is in the exclude list
            if exclude and any(name.startswith(sub) for sub in exclude):
                continue

            if self.default is not empty:
                if callable(self.default) and self.should_call_lazy:
                    default_value = self.default(settings, self)
                else:
                    default_value = self.default
            else:
                default_value = empty

            # THIS IS A FIX FOR #585 in contrast with #799
            # toml considers signed strings "+-1" as integers
            # however existing users are passing strings
            # to default on validator (see #585)
            # The solution we added on #667 introduced a new problem
            # This fix here makes it to work for both cases.
            # This guard also fixes #1064 assuming that any validator
            # having is_type_of=str wants to bypass toml inference.
            if isinstance(default_value, str) and self.is_type_of is str:
                # avoid TOML from parsing "+-1" started strings as integer
                default_value = f"'{default_value}'"

            # NOTE: must stop mutating settings here
            is_dynaconf_settings = getattr(settings, "__core__", False)
            if is_dynaconf_settings:
                try:
                    # settings is a Dynaconf instance
                    _setdefault = getattr(settings, "setdefault")
                    value = _setdefault(  #  cheat mypy
                        name,
                        default_value,
                        apply_default_on_none=self.apply_default_on_none,
                        env=env,
                    )
                except AttributeError:  # dotted get/set on a non-dict type
                    raise ValidationError(f"Mismatched type for {name}")
            else:
                value = settings.get(name, default_value)

            # Existence checks
            if self.must_exist is None:  # must_exist is unset
                if value is empty:
                    continue  #  no further checks required, as there is nothing to check
                else:
                    pass  # proceed with further checks
            elif self.must_exist is True:
                if value is empty:
                    _message = self.messages["must_exist_true"].format(
                        name=name, env=env
                    )
                    raise ValidationError(_message, details=[(self, _message)])
                else:
                    pass
            elif self.must_exist is False:
                if value is empty:
                    continue  # value absent as required — nothing further to check
                else:
                    _message = self.messages["must_exist_false"].format(
                        name=name, env=env
                    )
                    raise ValidationError(_message, details=[(self, _message)])
            else:
                raise ValueError(
                    f"must_exist must be True, False, or None, got {self.must_exist!r}"
                )

            # value or default value already set
            # by settings.setdefault above
            # however we need to cast it
            # so we call .set again
            # NOTE: we must stop mutating settings here
            if self.should_call_lazy:
                value = self.cast(settings.get(name))
            if _set := getattr(settings, "set", None):
                # Settings is Dynaconf
                _set(
                    name, value, validate=False, loader_identifier="validator"
                )
            else:
                # settings is a dict
                settings[name] = value

            # reorder passed operations so type check is made first
            sorted_operations = sorted(
                self.operations.items(),
                key=lambda item: item[0] != "is_type_of",
            )
            for op_name, op_value in sorted_operations:
                op_function = getattr(validator_conditions, op_name)
                op_succeeded = False

                # 'is_type_of' special error handling - related to #879
                if op_name == "is_type_of":
                    # auto transform quoted types
                    if isinstance(op_value, str):
                        op_value = __builtins__.get(  # type: ignore
                            op_value, op_value
                        )

                    # invalid type (not in __builtins__) may raise TypeError
                    try:
                        op_succeeded = op_function(value, op_value)
                    except TypeError as e:
                        raise ValidationError(
                            f"Invalid type '{op_value}' for condition "
                            f"'is_type_of'. Should provide a valid type. {e}"
                        )
                else:
                    try:
                        op_succeeded = op_function(value, op_value)
                    except TypeError as e:
                        raise ValidationError(
                            f"Invalid Operation '{op_name}' "
                            f"for type {type(value)!r} "
                            f"on '{name}': {e}"
                        )

                if not op_succeeded:
                    _message = self.messages["operations"].format(
                        name=name,
                        operation=op_function.__name__,
                        op_value=op_value,
                        value=value,
                        env=env,
                    )
                    raise ValidationError(_message, details=[(self, _message)])

            # is there a callable condition?
            if self.condition is not None:
                if not self.condition(value):
                    _message = self.messages["condition"].format(
                        name=name,
                        function=self.condition.__name__,
                        value=value,
                        env=env,
                    )
                    raise ValidationError(_message, details=[(self, _message)])

            # Type is list or dict and has internal validators
            self._validate_internal_items(value, name, variable_path)

    def _validate_internal_items(
        self,
        value: Any,
        name: str,
        variable_path: tuple | None = None,
    ):
        """Validate internal items of a data structure."""
        variable_path = variable_path or tuple()
        variable_path += (name,)
        if isinstance(value, list):
            for i, item in enumerate(value):
                _item_path = tuple(variable_path)
                if isinstance(item, dict):
                    _item_path += (f"{i}", "{name}")
                    _validator_location = ".".join(_item_path)
                    data = item
                else:
                    _item_path += (f"{i}",)
                    _validator_location = ".".join(_item_path)
                    data = {"<item>": item}

                for validator in self.items_validators:
                    # avoid mutating a reusable validator
                    if not validator.names:
                        _validator = deepcopy(validator)
                        _validator.names = ("<item>",)
                    else:
                        _validator = validator

                    for k, v in _validator.default_messages.items():
                        _validator.messages[k] = v.replace(
                            "{name}", _validator_location
                        )

                    _validator.validate(data, variable_path=_item_path)

        elif isinstance(value, dict):
            _validator_location = ".".join(variable_path)
            for validator in self.items_validators:
                for k, v in validator.default_messages.items():
                    validator.messages[k] = v.replace(
                        "{name}", _validator_location + ".{name}"
                    )
                validator.validate(
                    value, only=validator.names, variable_path=variable_path
                )


class CombinedValidator(Validator):
    def __init__(
        self,
        validator_a: Validator,
        validator_b: Validator,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Takes 2 validators and combines the validation"""
        self.validators = (validator_a, validator_b)
        super().__init__(*args, **kwargs)
        for attr in EQUALITY_ATTRS:
            if not getattr(self, attr, None):
                value = tuple(
                    getattr(validator, attr) for validator in self.validators
                )
                setattr(self, attr, value)

    def validate(
        self,
        settings: Any,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        variable_path: tuple | None = None,
    ) -> None:  # pragma: no cover
        raise NotImplementedError(
            "subclasses OrValidator or AndValidator implements this method"
        )

    def __repr__(self):
        result = f"{self.__class__.__name__}("
        result += ", ".join(repr(v) for v in self.validators)
        result += ")"
        return result


class OrValidator(CombinedValidator):
    """Evaluates on Validator() | Validator()"""

    def validate(
        self,
        settings: Any,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        variable_path: tuple | None = None,
    ) -> None:
        """Ensure at least one of the validators are valid"""
        errors = []
        for validator in self.validators:
            try:
                validator.validate(
                    settings,
                    only=only,
                    exclude=exclude,
                    only_current_env=only_current_env,
                    variable_path=variable_path,
                )
            except ValidationError as e:
                errors.append(e)
                continue
            else:
                return

        _message = self.messages["combined"].format(
            errors=" or ".join(
                str(e).replace("combined validators failed ", "")
                for e in errors
            )
        )
        raise ValidationError(_message, details=[(self, _message)])


class AndValidator(CombinedValidator):
    """Evaluates on Validator() & Validator()"""

    def validate(
        self,
        settings: Any,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        variable_path: tuple | None = None,
    ) -> None:
        """Ensure both the validators are valid"""
        errors = []
        for validator in self.validators:
            try:
                validator.validate(
                    settings,
                    only=only,
                    exclude=exclude,
                    only_current_env=only_current_env,
                    variable_path=variable_path,
                )
            except ValidationError as e:
                errors.append(e)
                continue

        if errors:
            _message = self.messages["combined"].format(
                errors=" and ".join(
                    str(e).replace("combined validators failed ", "")
                    for e in errors
                )
            )
            raise ValidationError(_message, details=[(self, _message)])


class ValidatorList(list):
    def __init__(
        self,
        settings: Settings,
        validators: Sequence[Validator] | None = None,
        *args: Validator,
        **kwargs: Any,
    ) -> None:
        if isinstance(validators, (list, tuple)):
            args = list(args) + list(validators)  # type: ignore
        self._only = kwargs.pop("validate_only", None)
        self._exclude = kwargs.pop("validate_exclude", None)
        super().__init__(args, **kwargs)  # type: ignore
        self.settings = settings

    def register(self, *args: Validator, **kwargs: Validator):
        validators: list[Validator] = list(
            chain.from_iterable(kwargs.values())  # type: ignore
        )
        validators.extend(args)
        for validator in validators:
            if validator and validator not in self:
                self.append(validator)

    def descriptions(self, flat: bool = False) -> dict[str, str | list[str]]:
        if flat:
            descriptions: dict[str, str | list[str]] = {}
        else:
            descriptions = defaultdict(list)

        for validator in self:
            for name in validator.names:
                if isinstance(name, tuple) and len(name) > 0:
                    name = name[0]
                if flat:
                    descriptions.setdefault(name, validator.description)
                else:
                    descriptions[name].append(  # type: ignore
                        validator.description
                    )
        return descriptions

    def validate(
        self,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
    ) -> None:
        for validator in self:
            validator.validate(
                self.settings,
                only=only,
                exclude=exclude,
                only_current_env=only_current_env,
            )

    def validate_all(
        self,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        raise_error=True,
    ) -> list[ValidationError]:
        errors = []
        details = []
        for validator in self:
            try:
                validator.validate(
                    self.settings,
                    only=only,
                    exclude=exclude,
                    only_current_env=only_current_env,
                )
            except ValidationError as e:
                errors.append(e)
                details.append((validator, str(e)))
                continue

        if errors and raise_error:
            raise ValidationError(
                "; ".join(str(e) for e in errors), details=details
            )
        return errors
