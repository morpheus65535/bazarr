# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from logging import NullHandler, getLogger
from six import PY3, binary_type, string_types, text_type

from .core import Reportable

logger = getLogger(__name__)
logger.addHandler(NullHandler())

_visible_chars_table = dict.fromkeys(range(32))


def _is_unknown(value):
    return isinstance(value, text_type) and (not value or value.lower() == 'unknown')


class Property(Reportable):
    """Property class."""

    def __init__(self, name, default=None, private=False, description=None, delimiter=' / ', **kwargs):
        """Init method."""
        super(Property, self).__init__(name, description, **kwargs)
        self.default = default
        self.private = private
        # Used to detect duplicated values. e.g.: en / en or High@L4.0 / High@L4.0 or Progressive / Progressive
        self.delimiter = delimiter

    def extract_value(self, track, context):
        """Extract the property value from a given track."""
        names = self.name.split('.')
        value = track.get(names[0], {}).get(names[1]) if len(names) == 2 else track.get(self.name)
        if value is None:
            if self.default is None:
                return

            value = self.default

        if isinstance(value, string_types):
            if isinstance(value, binary_type):
                value = text_type(value)
            else:
                value = value.translate(_visible_chars_table).strip()
                if _is_unknown(value):
                    return
            value = self._deduplicate(value)

        result = self.handle(value, context)
        if result is not None and not _is_unknown(result):
            return result

    @classmethod
    def _deduplicate(cls, value):
        values = value.split(' / ')
        if len(values) == 2 and values[0] == values[1]:
            return values[0]
        return value

    def handle(self, value, context):
        """Return the value without any modification."""
        return value


class Configurable(Property):
    """Configurable property where values are in a config mapping."""

    def __init__(self, config, *args, **kwargs):
        """Init method."""
        super(Configurable, self).__init__(*args, **kwargs)
        self.mapping = getattr(config, self.__class__.__name__)

    @classmethod
    def _extract_key(cls, value):
        return text_type(value).upper()

    @classmethod
    def _extract_fallback_key(cls, value, key):
        pass

    def _lookup(self, key, context):
        result = self.mapping.get(key)
        if result is not None:
            result = getattr(result, context.get('profile') or 'default')
            return result if result != '__ignored__' else False

    def handle(self, value, context):
        """Return Variable or Constant."""
        key = self._extract_key(value)
        if key is False:
            return

        result = self._lookup(key, context)
        if result is False:
            return

        while not result and key:
            key = self._extract_fallback_key(value, key)
            result = self._lookup(key, context)
            if result is False:
                return

        if not result:
            self.report(value, context)

        return result


class MultiValue(Property):
    """Property with multiple values."""

    def __init__(self, prop=None, delimiter='/', single=False, handler=None, name=None, **kwargs):
        """Init method."""
        super(MultiValue, self).__init__(prop.name if prop else name, **kwargs)
        self.prop = prop
        self.delimiter = delimiter
        self.single = single
        self.handler = handler

    def handle(self, value, context):
        """Handle properties with multiple values."""
        values = (self._split(value[0], self.delimiter)
                  if len(value) == 1 else value) if isinstance(value, list) else self._split(value, self.delimiter)
        call = self.handler or self.prop.handle
        if len(values) > 1 and not self.single:
            return [call(item, context) if not _is_unknown(item) else None for item in values]

        return call(values[0], context)

    @classmethod
    def _split(cls, value, delimiter='/'):
        if value is None:
            return

        v = text_type(value)
        result = map(text_type.strip, v.split(delimiter))
        return list(result) if PY3 else result
