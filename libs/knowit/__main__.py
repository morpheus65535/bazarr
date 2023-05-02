import argparse
import json
import logging
import os
import sys
import typing
from argparse import ArgumentParser

import yaml

from knowit import (
    __url__,
    __version__,
    api,
)
from knowit.provider import ProviderError
from knowit.serializer import (
    get_json_encoder,
    get_yaml_dumper,
)
from knowit.utils import recurse_paths

logging.basicConfig(stream=sys.stdout, format='%(message)s')
logging.getLogger('CONSOLE').setLevel(logging.INFO)
logging.getLogger('knowit').setLevel(logging.ERROR)

console = logging.getLogger('CONSOLE')
logger = logging.getLogger('knowit')


def build_argument_parser() -> ArgumentParser:
    """Build the argument parser."""
    opts = ArgumentParser()
    opts.add_argument(
        dest='videopath',
        help='Path to the video to introspect',
        nargs='*',
        type=str,
    )

    provider_opts = opts.add_argument_group('Providers')
    provider_opts.add_argument(
        '-p',
        '--provider',
        dest='provider',
        help='The provider to be used: mediainfo, ffmpeg, mkvmerge or enzyme.',
        type=str,
    )

    output_opts = opts.add_argument_group('Output')
    output_opts.add_argument(
        '--debug',
        action='store_true',
        dest='debug',
        help='Print information for debugging knowit and for reporting bugs.'
    )
    output_opts.add_argument(
        '--report',
        action='store_true',
        dest='report',
        help='Parse media and report all non-detected values'
    )
    output_opts.add_argument(
        '-y',
        '--yaml',
        action='store_true',
        dest='yaml',
        help='Display output in yaml format'
    )
    output_opts.add_argument(
        '-N',
        '--no-units',
        action='store_true',
        dest='no_units',
        help='Display output without units'
    )
    output_opts.add_argument(
        '-P',
        '--profile',
        dest='profile',
        help='Display values according to specified profile: code, default, human, technical',
        type=str,
    )

    conf_opts = opts.add_argument_group('Configuration')
    conf_opts.add_argument(
        '--mediainfo',
        dest='mediainfo',
        help='The location to search for MediaInfo binaries',
        type=str,
    )
    conf_opts.add_argument(
        '--ffmpeg',
        dest='ffmpeg',
        help='The location to search for ffprobe (FFmpeg) binaries',
        type=str,
    )
    conf_opts.add_argument(
        '--mkvmerge',
        dest='mkvmerge',
        help='The location to search for mkvmerge (MKVToolNix) binaries',
        type=str,
    )

    information_opts = opts.add_argument_group('Information')
    information_opts.add_argument(
        '--version',
        dest='version',
        action='store_true',
        help='Display knowit version.'
    )

    return opts


def knowit(
        video_path: typing.Union[str, os.PathLike],
        options: argparse.Namespace,
        context: typing.MutableMapping,
) -> typing.Mapping:
    """Extract video metadata."""
    context['path'] = video_path
    if not options.report:
        console.info('For: %s', video_path)
    else:
        console.info('Parsing: %s', video_path)
    info = api.know(video_path, context)
    if not options.report:
        console.info('Knowit %s found: ', __version__)
        console.info(dumps(info, options, context))
    return info


def _as_yaml(
        info: typing.Mapping[str, typing.Any],
        context: typing.Mapping,
) -> str:
    """Convert info to string using YAML format."""
    data = {info['path']: info} if 'path' in info else info
    return yaml.dump(
        data,
        Dumper=get_yaml_dumper(context),
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def _as_json(
        info: typing.Mapping[str, typing.Any],
        context: typing.Mapping,
) -> str:
    """Convert info to string using JSON format."""
    return json.dumps(
        info,
        cls=get_json_encoder(context),
        indent=4,
        ensure_ascii=False,
    )


def dumps(
        info: typing.Mapping[str, typing.Any],
        options: argparse.Namespace,
        context: typing.Mapping,
) -> str:
    """Convert info to string using json or yaml format."""
    convert = _as_yaml if options.yaml else _as_json
    return convert(info, context)


def main(args: typing.Optional[typing.List[str]] = None) -> None:
    """Execute main function for entry point."""
    argument_parser = build_argument_parser()
    args = args or sys.argv[1:]
    options = argument_parser.parse_args(args)

    if options.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('enzyme').setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    paths = recurse_paths(options.videopath)

    if not paths:
        if options.version:
            console.info(api.debug_info())
        else:
            argument_parser.print_help()
        return

    report: typing.MutableMapping[str, str] = {}
    for i, video_path in enumerate(paths):
        try:
            context = {k: v for k, v in vars(options).items() if v is not None}
            if options.report:
                context['report'] = report
            else:
                del context['report']
            knowit(video_path, options, context)
        except ProviderError:
            logger.exception('Error when processing video')
        except OSError:
            logger.exception('OS error when processing video')
        except UnicodeError:
            logger.exception('Character encoding error when processing video')
        except api.KnowitException as e:
            logger.error(e)

        if options.report and i % 20 == 19 and report:
            console.info('Unknown values so far:')
            console.info(dumps(report, options, vars(options)))

    if options.report:
        if report:
            console.info('Knowit %s found unknown values:', __version__)
            console.info(dumps(report, options, vars(options)))
            console.info('Please report them at %s', __url__)
        else:
            console.info('Knowit %s knows everything. :-)', __version__)


if __name__ == '__main__':
    main(sys.argv[1:])
