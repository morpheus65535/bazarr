import typing
from logging import NullHandler, getLogger

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
            description: typing.Optional[str] = None,
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

    def report(self, value: typing.Union[str, T], context: typing.MutableMapping) -> None:
        """Report unknown value."""
        if not value or not self.reportable:
            return

        if 'report' in context:
            report_map = context['report'].setdefault(self.description, {})
            if value not in report_map:
                report_map[value] = context['path']
        logger.info('Invalid %s: %r', self.description, value)


class Property(Reportable[T]):
    """Property class."""

    def __init__(
            self,
            *args: str,
            default: typing.Optional[T] = None,
            private: bool = False,
            description: typing.Optional[str] = None,
            delimiter: str = ' / ',
            **kwargs,
    ):
        """Init method."""
        super().__init__(*args, description=description, **kwargs)
        self.default = default
        self.private = private
        # Used to detect duplicated values. e.g.: en / en or High@L4.0 / High@L4.0 or Progressive / Progressive
        self.delimiter = delimiter

    @classmethod
    def _extract_value(cls,
                       track: typing.Mapping,
                       name: str,
                       names: typing.List[str]):
        if len(names) == 2:
            parent_value = track.get(names[0], track.get(names[0].upper(), {}))
            return parent_value.get(names[1], parent_value.get(names[1].upper()))

        return track.get(name, track.get(name.upper()))

    def extract_value(
            self,
            track: typing.Mapping,
            context: typing.MutableMapping,
    ) -> typing.Optional[T]:
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

    def handle(self, value: T, context: typing.MutableMapping) -> typing.Optional[T]:
        """Return the value without any modification."""
        return value


class Configurable(Property[T]):
    """Configurable property where values are in a config mapping."""

    def __init__(self, config: typing.Mapping[str, typing.Mapping], *args: str,
                 config_key: typing.Optional[str] = None, **kwargs):
        """Init method."""
        super().__init__(*args, **kwargs)
        self.mapping = getattr(config, config_key or self.__class__.__name__) if config else {}

    @classmethod
    def _extract_key(cls, value: str) -> typing.Union[str, bool]:
        return value.upper()

    @classmethod
    def _extract_fallback_key(cls, value: str, key: str) -> typing.Optional[T]:
        return None

    def _lookup(
            self,
            key: str,
            context: typing.MutableMapping,
    ) -> typing.Union[T, None, bool]:
        result = self.mapping.get(key)
        if result is not None:
            result = getattr(result, context.get('profile') or 'default')
            return result if result != '__ignored__' else False
        return None

    def handle(self, value, context):
        """Return Variable or Constant."""
        key = self._extract_key(value)
        if key is False:
            return None

        result = self._lookup(key, context)
        if result is False:
            return None

        while not result and key:
            key = self._extract_fallback_key(value, key)
            result = self._lookup(key, context)
            if result is False:
                return None

        if not result:
            self.report(value, context)

        return result


class MultiValue(Property):
    """Property with multiple values."""

    def __init__(self, prop: typing.Optional[Property] = None, delimiter='/', single=False,
                 handler: typing.Optional[
                     typing.Callable[[typing.Optional[str], typing.MutableMapping], typing.Optional[str]]] = None,
                 name=None, **kwargs):
        """Init method."""
        super().__init__(*(prop.names if prop else (name,)), **kwargs)
        self.prop = prop
        self.delimiter = delimiter
        self.single = single
        self.handler = handler

    def handle(
            self,
            value: str,
            context: typing.MutableMapping,
    ) -> typing.Optional[typing.Union[str, typing.List[str]]]:
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
            if len(value) == 1:
                values = self._split(value[0], self.delimiter)
            else:
                values = value
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
            value: typing.Optional[T],
            delimiter: str = '/',
    ) -> typing.Optional[typing.List[str]]:
        if value is None:
            return None

        return [x.strip() for x in str(value).split(delimiter)]


class Rule(Reportable[T]):
    """Rule abstract class."""

    def __init__(self, name: str, private=False, override=False, **kwargs):
        """Initialize the object."""
        super().__init__(name, **kwargs)
        self.private = private
        self.override = override

    def execute(self, props, pv_props, context: typing.Mapping):
        """How to execute a rule."""
        raise NotImplementedError
