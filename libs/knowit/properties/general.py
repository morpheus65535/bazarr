import re
import typing
from datetime import timedelta
from decimal import Decimal, InvalidOperation

import babelfish

from knowit.core import Configurable, Property
from knowit.utils import round_decimal

T = typing.TypeVar('T')


class Basic(Property[T]):
    """Basic property to handle int, Decimal and other basic types."""

    def __init__(self, *args: str, data_type: typing.Type,
                 processor: typing.Optional[typing.Callable[[T], T]] = None,
                 allow_fallback: bool = False, **kwargs):
        """Init method."""
        super().__init__(*args, **kwargs)
        self.data_type = data_type
        self.processor = processor or (lambda x: x)
        self.allow_fallback = allow_fallback

    def handle(self, value, context: typing.MutableMapping):
        """Handle value."""
        if isinstance(value, self.data_type):
            return self.processor(value)

        try:
            return self.processor(self.data_type(value))
        except ValueError:
            if not self.allow_fallback:
                self.report(value, context)


class Duration(Property[timedelta]):
    """Duration property."""

    duration_re = re.compile(r'(?P<hours>\d{1,2}):'
                             r'(?P<minutes>\d{1,2}):'
                             r'(?P<seconds>\d{1,2})(?:\.'
                             r'(?P<milliseconds>\d{3})'
                             r'(?P<microseconds>\d{3})?\d*)?')

    def __init__(self, *args: str, resolution: typing.Union[int, Decimal] = 1, **kwargs):
        """Initialize a Duration."""
        super().__init__(*args, **kwargs)
        self.resolution = resolution

    def handle(self, value, context: typing.MutableMapping):
        """Return duration as timedelta."""
        if isinstance(value, timedelta):
            return value
        elif isinstance(value, int):
            return timedelta(milliseconds=int(value * self.resolution))
        try:
            return timedelta(
                milliseconds=int(Decimal(value) * self.resolution))
        except (ValueError, InvalidOperation):
            pass

        match = self.duration_re.match(value)
        if not match:
            self.report(value, context)
            return None

        params = {
            key: int(value)
            for key, value in match.groupdict().items()
            if value
        }
        return timedelta(**params)


class Language(Property[babelfish.Language]):
    """Language property."""

    def handle(self, value, context: typing.MutableMapping):
        """Handle languages."""
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


class Quantity(Property):
    """Quantity is a property with unit."""

    def __init__(self, *args: str, unit, data_type=int, **kwargs):
        """Init method."""
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.data_type = data_type

    def handle(self, value, context):
        """Handle value with unit."""
        if not isinstance(value, self.data_type):
            try:
                value = self.data_type(value)
            except ValueError:
                self.report(value, context)
                return
        if isinstance(value, Decimal):
            value = round_decimal(value, min_digits=1, max_digits=3)

        return value if context.get('no_units') else value * self.unit


class YesNo(Configurable[str]):
    """Yes or No handler."""

    yes_values = ('yes', 'true', '1')

    def __init__(self, *args: str, yes=True, no=False, hide_value=None,
                 config: typing.Optional[
                     typing.Mapping[str, typing.Mapping]] = None,
                 config_key: typing.Optional[str] = None,
                 **kwargs):
        """Init method."""
        super().__init__(config or {}, config_key=config_key, *args, **kwargs)
        self.yes = yes
        self.no = no
        self.hide_value = hide_value

    def handle(self, value, context):
        """Handle boolean values."""
        result = self.yes if str(value).lower() in self.yes_values else self.no
        if result == self.hide_value:
            return None

        return super().handle(result, context) if self.mapping else result
