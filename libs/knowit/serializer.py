import datetime
import json
import re
import typing
from datetime import timedelta
from decimal import Decimal

import babelfish
import yaml
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver as DefaultResolver
from yaml.scanner import Scanner

from knowit.units import units
from knowit.utils import round_decimal


def format_property(profile: str, o):
    """Convert properties to string."""
    if isinstance(o, timedelta):
        return format_duration(o, profile)

    if isinstance(o, babelfish.language.Language):
        return format_language(o, profile)

    if hasattr(o, 'units'):
        return format_quantity(o, profile)

    return str(o)


def get_json_encoder(context):
    """Return json encoder that handles all needed object types."""
    class StringEncoder(json.JSONEncoder):
        """String json encoder."""

        def default(self, o):
            return format_property(context['profile'], o)

    return StringEncoder


def get_yaml_dumper(context):
    """Return yaml dumper that handles all needed object types."""
    class CustomDumper(yaml.SafeDumper):
        """Custom YAML Dumper."""

        def default_representer(self, data):
            """Convert data to string."""
            if isinstance(data, int):
                return self.represent_int(data)
            return self.represent_str(str(data))

        def default_language_representer(self, data):
            """Convert language to string."""
            return self.represent_str(format_language(data, context['profile']))

        def default_quantity_representer(self, data):
            """Convert quantity to string."""
            return self.default_representer(format_quantity(data, context['profile']))

        def default_duration_representer(self, data):
            """Convert quantity to string."""
            return self.default_representer(format_duration(data, context['profile']))

    CustomDumper.add_representer(babelfish.Language, CustomDumper.default_language_representer)
    CustomDumper.add_representer(timedelta, CustomDumper.default_duration_representer)
    CustomDumper.add_representer(units.Quantity, CustomDumper.default_quantity_representer)
    CustomDumper.add_representer(Decimal, CustomDumper.default_representer)

    return CustomDumper


def get_yaml_loader(constructors=None):
    """Return a yaml loader that handles sequences as python lists."""
    constructors = constructors or {}
    yaml_implicit_resolvers = dict(DefaultResolver.yaml_implicit_resolvers)

    class Resolver(DefaultResolver):
        """Custom YAML Resolver."""

    Resolver.yaml_implicit_resolvers.clear()
    for ch, vs in yaml_implicit_resolvers.items():
        Resolver.yaml_implicit_resolvers.setdefault(ch, []).extend(
            (tag, regexp) for tag, regexp in vs
            if not tag.endswith('float')
        )
    Resolver.add_implicit_resolver(  # regex copied from yaml source
        '!decimal',
        re.compile(r'''^(?:
            [-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?
            |\.[0-9_]+(?:[eE][-+][0-9]+)?
            |[-+]?[0-9][0-9_]*(?::[0-9]?[0-9])+\.[0-9_]*
            |[-+]?\.(?:inf|Inf|INF)
            |\.(?:nan|NaN|NAN)
        )$''', re.VERBOSE),
        list('-+0123456789.')
    )

    class CustomLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):
        """Custom YAML Loader."""

        def __init__(self, stream):
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)
            SafeConstructor.__init__(self)
            Resolver.__init__(self)

    CustomLoader.add_constructor('tag:yaml.org,2002:seq', yaml.Loader.construct_python_tuple)
    for tag, constructor in constructors.items():
        CustomLoader.add_constructor(tag, constructor)

    def decimal_constructor(loader, node):
        value = loader.construct_scalar(node)
        return Decimal(value)

    CustomLoader.add_constructor('!decimal', decimal_constructor)

    return CustomLoader


def format_duration(
        duration: datetime.timedelta,
        profile='default',
) -> typing.Union[str, Decimal]:
    if profile == 'technical':
        return str(duration)

    seconds = duration.total_seconds()
    if profile == 'code':
        return round_decimal(
            Decimal((duration.days * 86400 + duration.seconds) * 10 ** 6 + duration.microseconds) / 10**6, min_digits=1
        )

    hours = int(seconds // 3600)
    seconds = seconds - (hours * 3600)
    minutes = int(seconds // 60)
    seconds = int(seconds - (minutes * 60))
    if profile == 'human':
        if hours > 0:
            return f'{hours} hours {minutes:02d} minutes {seconds:02d} seconds'
        if minutes > 0:
            return f'{minutes} minutes {seconds:02d} seconds'
        return f'{seconds} seconds'

    return f'{hours}:{minutes:02d}:{seconds:02d}'


def format_language(
        language: babelfish.language.Language,
        profile: str = 'default',
) -> str:
    if profile in ('default', 'human'):
        return str(language.name)

    return str(language)


def format_quantity(
        quantity,
        profile='default',
) -> str:
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


def _format_quantity(
        num,
        unit: str = 'B',
        binary: bool = False,
        precision: int = 2,
) -> str:
    if binary:
        factor = 1024
        affix = 'i'
    else:
        factor = 1000
        affix = ''
    for prefix in ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z'):
        if abs(num) < factor:
            break
        num /= factor
    else:
        prefix = 'Y'

    return f'{num:3.{precision}f} {prefix}{affix}{unit}'


YAMLLoader = get_yaml_loader()
