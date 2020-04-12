# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from collections import OrderedDict
from datetime import timedelta

import babelfish
from six import text_type
import yaml

from .units import units


def format_property(context, o):
    """Convert properties to string."""
    if isinstance(o, timedelta):
        return format_duration(o, context['profile'])

    if isinstance(o, babelfish.language.Language):
        return format_language(o, context['profile'])

    if hasattr(o, 'units'):
        return format_quantity(o, context['profile'])

    return text_type(o)


def get_json_encoder(context):
    """Return json encoder that handles all needed object types."""
    class StringEncoder(json.JSONEncoder):
        """String json encoder."""

        def default(self, o):
            return format_property(context, o)

    return StringEncoder


def get_yaml_dumper(context):
    """Return yaml dumper that handles all needed object types."""
    class CustomDumper(yaml.SafeDumper):
        """Custom YAML Dumper."""

        def default_representer(self, data):
            """Convert data to string."""
            if isinstance(data, int):
                return self.represent_int(data)
            if isinstance(data, float):
                return self.represent_float(data)
            return self.represent_str(str(data))

        def ordered_dict_representer(self, data):
            """Representer for OrderedDict."""
            return self.represent_mapping('tag:yaml.org,2002:map', data.items())

        def default_language_representer(self, data):
            """Convert language to string."""
            return self.represent_str(format_language(data, context['profile']))

        def default_quantity_representer(self, data):
            """Convert quantity to string."""
            return self.default_representer(format_quantity(data, context['profile']))

        def default_duration_representer(self, data):
            """Convert quantity to string."""
            return self.default_representer(format_duration(data, context['profile']))

    CustomDumper.add_representer(OrderedDict, CustomDumper.ordered_dict_representer)
    CustomDumper.add_representer(babelfish.Language, CustomDumper.default_language_representer)
    CustomDumper.add_representer(timedelta, CustomDumper.default_duration_representer)
    CustomDumper.add_representer(units.Quantity, CustomDumper.default_quantity_representer)

    return CustomDumper


def get_yaml_loader(constructors=None):
    """Return a yaml loader that handles sequences as python lists."""
    constructors = constructors or {}

    class CustomLoader(yaml.Loader):
        """Custom YAML Loader."""

        pass

    CustomLoader.add_constructor('tag:yaml.org,2002:seq', CustomLoader.construct_python_tuple)
    for tag, constructor in constructors.items():
        CustomLoader.add_constructor(tag, constructor)

    return CustomLoader


def format_duration(duration, profile='default'):
    if profile == 'technical':
        return str(duration)

    seconds = duration.total_seconds()
    if profile == 'code':
        return duration.total_seconds()

    hours = int(seconds // 3600)
    seconds = seconds - (hours * 3600)
    minutes = int(seconds // 60)
    seconds = int(seconds - (minutes * 60))
    if profile == 'human':
        if hours > 0:
            return '{0} hours {1:02d} minutes {2:02d} seconds'.format(hours, minutes, seconds)
        if minutes > 0:
            return '{0} minutes {1:02d} seconds'.format(minutes, seconds)

        return '{0} seconds'.format(seconds)

    return '{0}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)


def format_language(language, profile='default'):
    if profile in ('default', 'human'):
        return str(language.name)

    return str(language)


def format_quantity(quantity, profile='default'):
    """Human friendly format."""
    if profile == 'code':
        return quantity.magnitude

    unit = quantity.units
    if unit != 'bit':
        technical = profile == 'technical'
        if unit == 'hertz':
            return _format_quantity(quantity.magnitude, unit='Hz', binary=technical, precision=3 if technical else 1)

        root_unit = quantity.to_root_units().units
        if root_unit == 'bit':
            return _format_quantity(quantity.magnitude, binary=technical, precision=3 if technical else 2)
        if root_unit == 'bit / second':
            return _format_quantity(quantity.magnitude, unit='bps', binary=technical, precision=3 if technical else 1)

    return str(quantity)


def _format_quantity(num, unit='B', binary=False, precision=2):
    fmt_pattern = '{value:3.%sf} {prefix}{affix}{unit}' % precision
    factor = 1024. if binary else 1000.
    binary_affix = 'i' if binary else ''
    for prefix in ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z'):
        if abs(num) < factor:
            return fmt_pattern.format(value=num, prefix=prefix, affix=binary_affix, unit=unit)
        num /= factor

    return fmt_pattern.format(value=num, prefix='Y', affix=binary_affix, unit=unit)


YAMLLoader = get_yaml_loader()
