from __future__ import annotations  # WARNING: remove this when debugging

from collections.abc import Callable
from collections.abc import Sequence
from typing import Any

from dynaconf.utils.functional import Empty
from dynaconf.utils.functional import empty
from dynaconf.validator import Validator as BaseValidator

from .exceptions import ValidationError


class Validator:
    """Define an interface to generate a valid dynaconf.Validator.

    The `operations` are::

        eq: value == other
        ne: value != other
        gt: value > other
        lt: value < other
        ge: value >= other
        le: value <= other
        is_type_of: isinstance(value, type)
        is_in:  value in sequence
        is_not_in: value not in sequence
        identity: value is other
        contains: contain value in
        not_contains: not contains value
        len_eq: len(value) == other
        len_ne: len(value) != other
        len_min: len(value) > other
        len_max: len(value) < other
        startswith: value.startswith(term)
        endswith:  value.endswith(term)
        not_startswith: not value.startswith(term)
        not_endswith:  not value.endswith(term)
        regex: pattern.match(value)
        not_regex: not pattern.match(value)
        condition: fn(value) is True
    """

    __slots__ = ()

    def __new__(
        cls,
        *,  # kw_only
        # Operations
        eq: Any = empty,
        ne: Any = empty,
        gt: Any = empty,
        lt: Any = empty,
        ge: Any = empty,
        le: Any = empty,
        identity: Any = empty,
        is_in: Any = empty,
        is_not_in: Any = empty,
        contains: Any = empty,
        not_contains: Any = empty,
        len_eq: Any = empty,
        len_ne: Any = empty,
        len_min: Any = empty,
        len_max: Any = empty,
        startswith: Any = empty,
        endswith: Any = empty,
        not_startswith: Any = empty,
        not_endswith: Any = empty,
        regex: Any = empty,
        not_regex: Any = empty,
        condition: Callable[[Any], bool] | None | Empty = empty,
        # options
        env: str | Sequence[str] | None | Empty = empty,
        messages: dict[str, str] | None | Empty = empty,
        cast: Callable[[Any], Any] | None | Empty = empty,
        description: str | None | Empty = empty,
        items_validators: list[BaseValidator] | None = None,
        # To be implemented, a interface like this to generate a When Validator
        # when: When | None = empty,
    ):
        kwargs = locals()
        kwargs.pop("cls")
        return BaseValidator(
            **{k: v for k, v in kwargs.items() if v is not empty}
        )


class ItemsValidator:
    """Validates each internal item in a sequence or mapping.

    Validates all integers in a list are >= 10::

        field: Annotated[list[int], ItemsValidator(ge=10, le=100)]

    The same as above but reusing validators::

        min_value = Validator(ge=10)
        max_value = Validator(le=100)
        field: Annotated[list[int], ItemsValidator(min_value, max_value)]

    Validates that values of the `port` key is not equal 5432::

        field: Annotated[dict[str, int], ItemsValidator("port", ne=5432)]

    Going down inside a dict of dict::

        field: Annotated[
            dict[str, dict[str, int]],
            ItemsValidator(
                "database",
                ItemsValidator("port, ne=5432)
            )
        ]

    For more complex cases the recommendations is to use `condition=function`::

        def my_value_is_valid(value) -> bool: ...

        field: Annotated[..., Validator(condition=my_value_is_valid)]

    """

    __slots__ = ()

    def __new__(
        cls,
        *args,
        # Operations
        eq: Any = empty,
        ne: Any = empty,
        gt: Any = empty,
        lt: Any = empty,
        ge: Any = empty,
        le: Any = empty,
        identity: Any = empty,
        is_in: Any = empty,
        is_not_in: Any = empty,
        contains: Any = empty,
        not_contains: Any = empty,
        len_eq: Any = empty,
        len_ne: Any = empty,
        len_min: Any = empty,
        len_max: Any = empty,
        startswith: Any = empty,
        endswith: Any = empty,
        not_startswith: Any = empty,
        not_endswith: Any = empty,
        regex: Any = empty,
        not_regex: Any = empty,
        condition: Callable[[Any], bool] | None | Empty = empty,
        # options
        env: str | Sequence[str] | None | Empty = empty,
        messages: dict[str, str] | None | Empty = empty,
        cast: Callable[[Any], Any] | None | Empty = empty,
        description: str | None | Empty = empty,
        items_validators: list[BaseValidator] | None = None,
        # To be implemented, a interface like this to generate a When Validator
        # when: When | None = empty,
    ):
        kwargs = locals()
        kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not empty and k not in ("cls", "args", "items_validators")
        }
        if items_validators:
            kwargs["items_validators"] = items_validators

        validators = [arg for arg in args if isinstance(arg, BaseValidator)]
        if kwargs:
            names = [arg for arg in args if isinstance(args, str)]
            validators.append(BaseValidator(*names, **kwargs))
        return BaseValidator(items_validators=validators)


# Utilities
# Inspired by the module annotated_types


class Not(BaseValidator):
    """Inverts a Validator

    field: Annotated[int, Not(Eq(10))]
    # actually the same as
    field: Annotated[int, Ne(10)]
    # but for SpecifiedOperations is much more semantic
    field: Annotated[str, Not(IsUrl())]
    """

    _validator: BaseValidator

    def __init__(self, validator: BaseValidator):
        self._validator = validator

    def validate(self, *args, **kwargs):
        self._validator.names = self.names
        try:
            # triggers validation of wrapped validator
            self._validator.validate(*args, **kwargs)
        except ValidationError:
            # If it fails then it is ok!
            return

        # If not fails, than it is an error
        raise ValidationError(f"Not({self._validator}) failed.")

    def __getattr__(self, name):
        return getattr(self._validator, name)


# Generic Validation Aliases


class GenericValidator:
    """Base to create aliased Validator with generic parametrized operation.

    This class exists mainly to allow creation of semantic named validators.

    Usage::

      class NoWayItIs(GenericValidator):
          operations = ["eq"]

      field: Annotated[T, NoWatItIs("pineapple")]

    Which is equivalent to::

      field: Annotatted[T, Validator(ne="pineapple")]

    Non parametrized alternative would be::

      NoWayItIsPineApple = Validator(ne="pineapple")
      field: Annotated[T, NoWayItIsPineApple]

    This class also allows definition of operatiosn with multiple parameters::

      class Interval(GenericOperation)
          operations = ["gt", "lt"]

     field: Annotated[int, Interval(5, 10)]  # 6, 7, 8, 9

    This  also allows definition of Validator with partial arguments::

        class GoodPassword(GenericValidator):
            operations = ["condition", "len_min", "len_max"]

            @staticmethod
            def contains_special_chars(val):
                return (
                    any(c in val for c in "@#$&!%")
                    and any(c.isupper() for c in val)
                    and any(c.isdigit() for c in val)
                )

            args = [contains_special_chars]

        field: Annotated[str, GoodPassword(10, 20)]

    """

    operations: list[str]
    args: list[Any] = []

    def __new__(cls, *params):
        params = cls.args + list(params)
        if len(cls.operations) != len(params):
            raise TypeError(
                f"{cls.__name__} takes "
                f"{len(cls.operations)} positional arguments"
            )
        return Validator(**dict(zip(cls.operations, params)))


class Eq(GenericValidator):
    """Eq(x) -> Validator(eq=x)"""

    operations = ["eq"]


class Ne(GenericValidator):
    """Ne(x) -> Validator(ne=x)"""

    operations = ["ne"]


class Gt(GenericValidator):
    """Gt(x) -> Validator(gt=x)"""

    operations = ["gt"]


class Lt(GenericValidator):
    """Lt(x) -> Validator(lt=x)"""

    operations = ["lt"]


class Ge(GenericValidator):
    """Ge(x) -> Validator(gte=x)"""

    operations = ["ge"]


class Le(GenericValidator):
    """Le(x) -> Validator(lte=x)"""

    operations = ["le"]


class Id(GenericValidator):
    """Id(x) -> Validator(identity=x)"""

    operations = ["identity"]


class In(GenericValidator):
    """In(x) -> Validator(is_in=x)"""

    operations = ["is_in"]


class NotIn(GenericValidator):
    """NotIn(x) -> Validator(is_not_in=x)"""

    operations = ["is_not_in"]


class Contains(GenericValidator):
    """Contains(x) -> Validator(contains=x)"""

    operations = ["contains"]


class NotContains(GenericValidator):
    """NotContains(x) -> Validator(not_contains=x)"""

    operations = ["not_contains"]


class LenEq(GenericValidator):
    """LenEq(x) -> Validator(len_eq=x)"""

    operations = ["len_eq"]


class LenNe(GenericValidator):
    """LenNe(x) -> Validator(len_ne=x)"""

    operations = ["len_ne"]


class LenMin(GenericValidator):
    """LenMin(x) -> Validator(len_min=x)"""

    operations = ["len_min"]


class LenMax(GenericValidator):
    """LenMax(x) -> Validator(len_max=x)"""

    operations = ["len_max"]


class Starts(GenericValidator):
    """Starts(x) -> Validator(startswith=x)"""

    operations = ["startswith"]


class Ends(GenericValidator):
    """Ends(x) -> Validator(endswith=x)"""

    operations = ["endswith"]


class NotStarts(GenericValidator):
    """NotStarts(x) -> Validator(not_startswith=x)"""

    operations = ["not_startswith"]


class NotEnds(GenericValidator):
    """NotEnds(x) -> Validator(not_endswith=x)"""

    operations = ["not_endswith"]


class Regex(GenericValidator):
    """Regex(x) -> Validator(regex=x)"""

    operations = ["regex"]


class NotRegex(GenericValidator):
    """NotRegex(x) -> Validator(not_regex=x)"""

    operations = ["not_regex"]


class Condition(GenericValidator):
    """Condition(x) -> Validator(condition=x)"""

    operations = ["condition"]


# Custom Validation Aliases
# The aliases defined here are mostly examples
# users can create their own aliases for domain specific validation.

is_url = Regex(
    r"((http|https)://)"  # Match the protocol (http or https) required
    r"(www\.)?"  # Match 'www.' optionally
    r"[\w.-]+"  # Match the domain name
    r"\.[a-z]{2,}"  # Match the top-level domain
    r"(/[^\s]*)?"  # Match the path (everything after the domain name)
)

is_connection_string = Regex(
    r"^(?P<scheme>postgresql|mysql|sqlite):\/\/"
    r"(?:(?P<user>[^:]+):"
    r"(?P<password>[^@]+)@)?"
    r"(?P<host>[^:\/]+)?"
    r"(?::(?P<port>\d+))?"
    r"\/(?P<path>[^\s]+)$"
)

is_semver = Regex(
    r"^(\d+)\.(\d+)\.(\d+)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

positive_int = Gt(0)
negative_int = Lt(0)
