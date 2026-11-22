import os
import traceback
import typing

from knowit import __url__, __version__
from knowit.config import Config
from knowit.environment import (
    collect_environment,
    format_environment,
    format_section,
)
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

available_providers: dict[str, Provider] = {}


class KnowitException(Exception):
    """Exception raised when knowit encounters an internal error."""


def initialize(context: typing.Mapping[str, typing.Any] | None = None, *, force: bool = False) -> None:
    """Initialize knowit, reload provider if a new suggested path is given."""
    context = context or {}
    config = Config.build(context.get('config'))
    for name, provider_cls in _provider_map.items():
        general_config = getattr(config, 'general', {})
        suggested_path = context.get(name) or general_config.get(name)
        # create provider if it is not initialized or if it is not loaded and suggesting a new path
        p = available_providers.get(name)
        if force or p is None or (not p.loaded() and not p.match_executor_location(suggested_path)):
            available_providers[name] = provider_cls(config, suggested_path)


def know(
    video_path: str | os.PathLike[str], context: typing.MutableMapping[str, typing.Any] | None = None
) -> typing.MutableMapping[str, typing.Any]:
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
        raise KnowitException(debug_info(context=context, exc_info=True)) from None


def dependencies(context: typing.Mapping[str, typing.Any] | None = None) -> typing.Mapping[str, typing.Any]:
    """Return all dependencies detected by knowit."""
    deps = {}
    try:
        initialize(context)
        for name in _provider_map:
            if name in available_providers:
                deps[name] = available_providers[name].version
            else:
                deps[name] = {}
    except Exception:
        pass

    return deps


def loaded_providers(options: dict[str, typing.Any] | None = None) -> dict[str, bool]:
    """Return a dict with each provider and if they are installed."""
    # initialize providers with options
    initialize(options)

    # return a dict of providers and the loaded state
    return {k: p.loaded() for k, p in available_providers.items()}


BOX_LINE = '+-------------------------------------------------------+'


def _centered(value: str) -> str:
    value = value[-52:]
    return f'| {value:^53} |'


def _format_request(context: typing.Mapping[str, typing.Any]) -> list[str]:
    """Render the options knowit was called with, excluding internal machinery."""
    request = {k: v for k, v in context.items() if v and k not in ('report', 'debug_data')}
    return format_section('request', request) if request else []


def debug_info(
    context: typing.MutableMapping[str, typing.Any] | None = None,
    exc_info: bool = False,
) -> str:
    """Return a report of the running environment, suitable for pasting into an issue.

    Every value is rendered in full: truncating a path or a library location hides
    exactly the detail most bug reports turn out to depend on.
    """
    lines = [
        BOX_LINE,
        _centered(f'KnowIt {__version__}'),
        BOX_LINE,
        '',
        format_environment(collect_environment(context)),
    ]

    if context:
        debug_data = context.pop('debug_data', None)

        request_lines = _format_request(context)
        if request_lines:
            lines.append('')
            lines.extend(request_lines)

        if debug_data:
            lines.append('')
            lines.append('raw provider data:')
            lines.append(debug_data())

    if exc_info:
        lines.append('')
        lines.append(traceback.format_exc())

    lines.append('')
    lines.extend(_format_footer(context))

    return '\n'.join(lines)


def _format_footer(context: typing.Mapping[str, typing.Any] | None = None) -> list[str]:
    """Tell the user the one command that produces a report we can act on.

    The instruction is not boxed: the box truncates, and a truncated command cannot be
    copied. This text is printed by every application that embeds knowit, so it is the
    place where most users learn what to send.
    """
    path = os.fspath(context['path']) if context and context.get('path') else '<path to your video>'
    return [
        BOX_LINE,
        _centered('Please report this problem at'),
        _centered(f'{__url__}/issues'),
        BOX_LINE,
        '',
        'Run this command and attach the file it creates to the issue.',
        'Your media file is not needed, and titles are masked in the report:',
        '',
        f'  knowit --bug-report "{path}"',
        '',
    ]
