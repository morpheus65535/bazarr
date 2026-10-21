import typing
from logging import NullHandler, getLogger

from knowit.config import Config

logger = getLogger(__name__)
logger.addHandler(NullHandler())

T = typing.TypeVar('T')

_visible_chars_table = dict.fromkeys(range(32))


def _is_unknown(value: typing.Any) -> bool:
    return isinstance(value, str) and (not value or value.lower() == 'unknown')


class Reportable(typing.Generic[T]):
    """Reportable abstract class."""

    def __init__(
        self,
        *args: str,
        description: str | None = None,
        reportable: bool = True,
    ):
        """Initialize the object."""
        self.names = args
        self._description = description
        self.reportable = reportable

    @property
    def description(self) -> str:
        """Rule description."""
        return self._description or '|'.join(self.names)

    def report(self, value: str | T, context: typing.MutableMapping[str, typing.Any]) -> None:
        """Report unknown value."""
        if not value or not self.reportable:
            return

        if 'report' in context:
            report_map = context['report'].setdefault(self.description, {})
            # a raw track value is not always hashable: mappings and lists have to be keyed by their
            # representation instead.
            key = value if isinstance(value, typing.Hashable) else repr(value)
            if key not in report_map:
                report_map[key] = context['path']
        logger.info('Invalid %s: %r', self.description, value)


class Property(Reportable[T]):
    """Property class."""

    def __init__(
        self,
        *args: str,
        default: T | None = None,
        private: bool = False,
        description: str | None = None,
        delimiter: str = ' / ',
        **kwargs: typing.Any,
    ):
        """Init method."""
        super().__init__(*args, description=description, **kwargs)
        self.default = default
        self.private = private
        # Used to detect duplicated values. e.g.: en / en or High@L4.0 / High@L4.0 or Progressive / Progressive
        self.delimiter = delimiter

    @classmethod
    def _extract_value(cls, track: typing.Mapping[str, typing.Any], name: str, names: list[str]) -> typing.Any:
        if len(names) == 2:
            parent_value = track.get(names[0], track.get(names[0].upper(), {}))
            return parent_value.get(names[1], parent_value.get(names[1].upper()))

        return track.get(name, track.get(name.upper()))

    def extract_value(
        self,
        track: typing.Mapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> T | None:
        """Extract the property value from a given track."""
        for name in self.names:
            names = name.split('.')
            value = self._extract_value(track, name, names)
            if value is None:
                if self.default is None:
                    continue

                value = self.default

            if isinstance(value, bytes):
                value = value.decode()

            if isinstance(value, str):
                value = value.translate(_visible_chars_table).strip()
                if _is_unknown(value):
                    continue
                value = self._deduplicate(value)

            result = self.handle(value, context)
            if result is not None and not _is_unknown(result):
                return result

        return None

    @classmethod
    def _deduplicate(cls, value: str) -> str:
        values = value.split(' / ')
        if len(values) == 2 and values[0] == values[1]:
            return values[0]
        return value

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> T | None:
        """Return the value without any modification."""
        return typing.cast(T, value)


class Configurable(Property[T]):
    """Configurable property where values are in a config mapping."""

    def __init__(
        self,
        config: Config | typing.Mapping[str, typing.Any],
        *args: str,
        config_key: str | None = None,
        **kwargs: typing.Any,
    ):
        """Init method."""
        super().__init__(*args, **kwargs)
        self.mapping = getattr(config, config_key or self.__class__.__name__) if config else {}

    @classmethod
    def _extract_key(cls, value: str) -> str | typing.Literal[False]:
        return value.upper()

    @classmethod
    def _extract_fallback_key(cls, value: str, key: str) -> str | None:
        return None

    def _lookup(
        self,
        key: str | None,
        context: typing.MutableMapping[str, typing.Any],
    ) -> T | None | typing.Literal[False]:
        result = self.mapping.get(key)
        if result is not None:
            result = getattr(result, context.get('profile') or 'default')
            return result if result != '__ignored__' else False
        return None

    def handle(self, value: T, context: typing.MutableMapping[str, typing.Any]) -> T | None:
        """Return Variable or Constant."""
        # Configurable is only ever used with string-keyed lookups: the raw value is always a string
        # coming from the parsed track data, even though T describes the looked-up result type.
        str_value = typing.cast(str, value)
        initial_key = self._extract_key(str_value)
        if initial_key is False:
            return None

        key: str | None = initial_key
        result = self._lookup(key, context)
        if result is False:
            return None

        while not result and key:
            key = self._extract_fallback_key(str_value, key)
            result = self._lookup(key, context)
            if result is False:
                return None

        if not result:
            self.report(str_value, context)

        return result


class MultiValue(Property[typing.Any]):
    """Property with multiple values."""

    def __init__(
        self,
        prop: Property[typing.Any] | None = None,
        delimiter: str = '/',
        single: bool = False,
        handler: typing.Callable[[str | None, typing.MutableMapping[str, typing.Any]], str | None] | None = None,
        name: str | None = None,
        **kwargs: typing.Any,
    ):
        """Init method."""
        super().__init__(*(prop.names if prop else (name,)), **kwargs)
        self.prop = prop
        self.delimiter = delimiter
        self.single = single
        self.handler = handler

    def handle(
        self,
        value: str,
        context: typing.MutableMapping[str, typing.Any],
    ) -> str | list[str] | None:
        """Handle properties with multiple values."""
        if self.handler:
            call = self.handler
        elif self.prop:
            call = self.prop.handle
        else:
            call = None

        if call is None:
            raise NotImplementedError('No handler available')

        result = call(value, context)
        if result is not None:
            return result

        if isinstance(value, list):
            values = self._split(value[0], self.delimiter) if len(value) == 1 else value
        else:
            values = self._split(value, self.delimiter)

        if values is None:
            return call(values, context)
        if len(values) > 1 and not self.single:
            part_results = [call(item, context) if not _is_unknown(item) else None for item in values]
            results = [r for r in part_results if r is not None]
            if results:
                return results
        return call(values[0], context)

    @classmethod
    def _split(
        cls,
        value: T | None,
        delimiter: str = '/',
    ) -> list[str] | None:
        if value is None:
            return None

        return [x.strip() for x in str(value).split(delimiter)]


class Rule(Reportable[T]):
    """Rule abstract class."""

    def __init__(self, name: str, private: bool = False, override: bool = False, **kwargs: typing.Any):
        """Initialize the object."""
        super().__init__(name, **kwargs)
        self.private = private
        self.override = override

    def execute(
        self,
        props: typing.MutableMapping[str, typing.Any],
        pv_props: typing.MutableMapping[str, typing.Any],
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.Any:
        """How to execute a rule."""
        raise NotImplementedError
