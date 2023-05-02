import os
import traceback
import typing

from knowit import __version__
from knowit.config import Config
from knowit.provider import Provider
from .providers import (
    EnzymeProvider,
    FFmpegProvider,
    MediaInfoProvider,
    MkvMergeProvider,
)

_provider_map = {
    'mediainfo': MediaInfoProvider,
    'ffmpeg': FFmpegProvider,
    'mkvmerge': MkvMergeProvider,
    'enzyme': EnzymeProvider,
}

provider_names = _provider_map.keys()

available_providers: typing.Dict[str, Provider] = {}


class KnowitException(Exception):
    """Exception raised when knowit encounters an internal error."""


def initialize(context: typing.Optional[typing.Mapping] = None) -> None:
    """Initialize knowit."""
    if not available_providers:
        context = context or {}
        config = Config.build(context.get('config'))
        for name, provider_cls in _provider_map.items():
            general_config = getattr(config, 'general', {})
            mapping = context.get(name) or general_config.get(name)
            available_providers[name] = provider_cls(config, mapping)


def know(
        video_path: typing.Union[str, os.PathLike],
        context: typing.Optional[typing.MutableMapping] = None
) -> typing.Mapping:
    """Return a mapping of video metadata."""
    video_path = os.fspath(video_path)

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


def dependencies(context: typing.Optional[typing.Mapping] = None) -> typing.Mapping:
    """Return all dependencies detected by knowit."""
    deps = {}
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


def _centered(value: str) -> str:
    value = value[-52:]
    return f'| {value:^53} |'


def debug_info(
        context: typing.Optional[typing.MutableMapping] = None,
        exc_info: bool = False,
) -> str:
    lines = [
        '+-------------------------------------------------------+',
        _centered(f'KnowIt {__version__}'),
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
                lines.append(_centered(f'{k}: {v}'))

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
