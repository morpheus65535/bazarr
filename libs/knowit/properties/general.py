import re
import typing
from datetime import timedelta
from decimal import Decimal, InvalidOperation

import babelfish

from knowit.config import Config
from knowit.core import Configurable, Property, T
from knowit.utils import round_decimal


class Basic(Property[T]):
    """Basic property to handle int, Decimal and other basic types."""

    def __init__(
        self,
        *args: str,
        data_type: type[T],
        processor: typing.Callable[[T], T] | None = None,
        allow_fallback: bool = False,
        **kwargs: typing.Any,
    ):
        """Init method."""
        super().__init__(*args, **kwargs)
        self.data_type = data_type
        self.processor = processor or (lambda x: x)
        self.allow_fallback = allow_fallback

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> T | None:
        """Handle value."""
        if isinstance(value, self.data_type):
            return self.processor(value)

        try:
            # mypy can't verify an unbound TypeVar's constructor accepts an argument
            return self.processor(self.data_type(value))  # type: ignore[call-arg]
        except ValueError:
            if not self.allow_fallback:
                self.report(value, context)
            return None


class Duration(Property[timedelta]):
    """Duration property."""

    duration_re = re.compile(
        r'(?P<hours>\d{1,2}):'
        r'(?P<minutes>\d{1,2}):'
        r'(?P<seconds>\d{1,2})(?:\.'
        r'(?P<milliseconds>\d{3})'
        r'(?P<microseconds>\d{3})?\d*)?'
    )

    def __init__(self, *args: str, resolution: int | Decimal = 1, **kwargs: typing.Any):
        """Initialize a Duration."""
        super().__init__(*args, **kwargs)
        self.resolution = resolution

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> timedelta | None:
        """Return duration as timedelta."""
        if isinstance(value, timedelta):
            return value
        elif isinstance(value, int):
            return timedelta(milliseconds=int(value * self.resolution))
        try:
            return timedelta(milliseconds=int(Decimal(value) * self.resolution))
        except (ValueError, InvalidOperation):
            pass

        match = self.duration_re.match(value)
        if not match:
            self.report(value, context)
            return None

        params = {key: int(value) for key, value in match.groupdict().items() if value}
        return timedelta(**params)


class Language(Property[babelfish.Language]):
    """Language property."""

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> babelfish.Language | None:
        """Handle languages."""
        if not isinstance(value, str):
            # A provider can yield a structured value (e.g. mediainfo returning a mapping) where a
            # language code is expected. babelfish only parses strings and a mapping of 3 keys would
            # otherwise pass the alpha3 length check below.
            self.report(value, context)
            return babelfish.Language('und')

        try:
            if len(value) == 3:
                try:
                    return babelfish.Language.fromalpha3b(value)
                except babelfish.Error:
                    # Try alpha3t if alpha3b fails
                    return babelfish.Language.fromalpha3t(value)

            return babelfish.Language.fromietf(value)
        except (babelfish.Error, ValueError):
            pass

        try:
            return babelfish.Language.fromname(value)
        except babelfish.Error:
            pass

        self.report(value, context)
        return babelfish.Language('und')


class Quantity(Property[typing.Any]):
    """Quantity is a property with unit."""

    def __init__(self, *args: str, unit: typing.Any, data_type: type = int, **kwargs: typing.Any):
        """Init method."""
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.data_type = data_type

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> typing.Any:
        """Handle value with unit."""
        if not isinstance(value, self.data_type):
            try:
                value = self.data_type(value)
            except ValueError:
                self.report(value, context)
                return None
        if isinstance(value, Decimal):
            value = round_decimal(value, min_digits=1, max_digits=3)

        return value if context.get('no_units') else value * self.unit


class YesNo(Configurable[str]):
    """Yes or No handler."""

    yes_values = ('yes', 'true', '1')

    def __init__(
        self,
        *args: str,
        yes: typing.Any = True,
        no: typing.Any = False,
        hide_value: typing.Any = None,
        config: Config | typing.Mapping[str, typing.Any] | None = None,
        config_key: str | None = None,
        **kwargs: typing.Any,
    ):
        """Init method."""
        super().__init__(config or {}, *args, config_key=config_key, **kwargs)
        self.yes = yes
        self.no = no
        self.hide_value = hide_value

    def handle(self, value: str, context: typing.MutableMapping[str, typing.Any]) -> str | None:
        """Handle boolean values."""
        result = self.yes if str(value).lower() in self.yes_values else self.no
        if result == self.hide_value:
            return None

        return super().handle(result, context) if self.mapping else result
