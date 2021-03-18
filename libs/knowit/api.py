# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import traceback

from . import OrderedDict, __version__
from .config import Config
from .providers import (
    EnzymeProvider,
    FFmpegProvider,
    MediaInfoProvider,
)

_provider_map = OrderedDict([
    ('mediainfo', MediaInfoProvider),
    ('ffmpeg', FFmpegProvider),
    ('enzyme', EnzymeProvider)
])

provider_names = _provider_map.keys()

available_providers = OrderedDict([])


class KnowitException(Exception):
    """Exception raised when knowit fails to perform media info extraction because of an internal error."""


def initialize(context=None):
    """Initialize knowit."""
    if not available_providers:
        context = context or {}
        config = Config.build(context.get('config'))
        for name, provider_cls in _provider_map.items():
            available_providers[name] = provider_cls(config, context.get(name) or config.general.get(name))


def know(video_path, context=None):
    """Return a dict containing the video metadata.

    :param video_path:
    :type video_path: string
    :param context:
    :type context: dict
    :return:
    :rtype: dict
    """
    try:
        # handle path-like objects
        video_path = video_path.__fspath__()
    except AttributeError:
        pass

    try:
        context = context or {}
        context.setdefault('profile', 'default')
        initialize(context)

        for name, provider in available_providers.items():
            if name != (context.get('provider') or name):
                continue

            if provider.accepts(video_path):
                result = provider.describe(video_path, context)
                if result:
                    return result

        return {}
    except Exception:
        raise KnowitException(debug_info(context=context, exc_info=True))


def dependencies(context=None):
    """Return all dependencies detected by knowit."""
    deps = OrderedDict([])
    try:
        initialize(context)
        for name, provider_cls in _provider_map.items():
            if name in available_providers:
                deps[name] = available_providers[name].version
            else:
                deps[name] = {}
    except Exception:
        pass

    return deps


def _centered(value):
    value = value[-52:]
    return '| {msg:^53} |'.format(msg=value)


def debug_info(context=None, exc_info=False):
    lines = [
        '+-------------------------------------------------------+',
        _centered('KnowIt {0}'.format(__version__)),
        '+-------------------------------------------------------+'
    ]

    first = True
    for key, info in dependencies(context).items():
        if not first:
            lines.append(_centered(''))
        first = False

        for k, v in info.items():
            lines.append(_centered(k))
            lines.append(_centered(v))

    if context:
        debug_data = context.pop('debug_data', None)

        lines.append('+-------------------------------------------------------+')
        for k, v in context.items():
            if v:
                lines.append(_centered('{}: {}'.format(k, v)))

        if debug_data:
            lines.append('+-------------------------------------------------------+')
            lines.append(debug_data())

    if exc_info:
        lines.append('+-------------------------------------------------------+')
        lines.append(traceback.format_exc())

    lines.append('+-------------------------------------------------------+')
    lines.append(_centered('Please report any bug or feature request at'))
    lines.append(_centered('https://github.com/ratoaq2/knowit/issues.'))
    lines.append('+-------------------------------------------------------+')

    return '\n'.join(lines)
