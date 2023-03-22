import argparse
import json
import logging
import sys
import typing

import babelfish

from trakit import TrakItApi, __version__

logging.basicConfig(stream=sys.stdout, format='%(message)s')
logging.getLogger('CONSOLE').setLevel(logging.INFO)
logging.getLogger('trakit').setLevel(logging.WARNING)

console = logging.getLogger('CONSOLE')
logger = logging.getLogger('trakit')


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    opts = argparse.ArgumentParser()
    opts.add_argument(
        dest='value',
        help='track title to guess',
        type=str,
    )

    conf_opts = opts.add_argument_group('Configuration')
    conf_opts.add_argument(
        '-l',
        '--expected-language',
        dest='expected_language',
        help='The expected language to be guessed',
        type=str,
    )

    output_opts = opts.add_argument_group('Output')
    output_opts.add_argument(
        '--debug',
        action='store_true',
        dest='debug',
        help='Print information for debugging trakit and for reporting bugs.'
    )
    output_opts.add_argument(
        '-y',
        '--yaml',
        action='store_true',
        dest='yaml',
        help='Display output in yaml format'
    )

    information_opts = opts.add_argument_group('Information')
    information_opts.add_argument('--version', action='version', version=__version__)

    return opts


def _as_yaml(value: str, info: typing.Mapping[str, typing.Any]) -> str:
    """Convert info to string using YAML format."""
    import yaml

    def default_representer(r: yaml.representer.SafeRepresenter, data: typing.Any):
        return r.represent_scalar('tag:yaml.org,2002:str', str(data))

    yaml.representer.SafeRepresenter.add_representer(babelfish.Language, default_representer)

    return yaml.safe_dump({value: dict(info)}, allow_unicode=True, sort_keys=False)


def _as_json(info: typing.Mapping[str, typing.Any]) -> str:
    """Convert info to string using JSON format."""
    return json.dumps(info, ensure_ascii=False, indent=2, default=str)


def dump(value: str, info: typing.Mapping[str, typing.Any], opts: argparse.Namespace) -> str:
    """Convert info to string using json or yaml format."""
    if opts.yaml:
        return _as_yaml(value, info)

    return _as_json(info)


def trakit(value: str, opts: argparse.Namespace) -> typing.Mapping:
    """Extract video metadata."""
    if not opts.yaml:
        console.info('Parsing: %s', value)
    options = {k: v for k, v in vars(opts).items() if v is not None}
    info = TrakItApi().trakit(value, options)
    console.info('TrakIt %s found: ', __version__)
    console.info(dump(value, info, opts))
    return info


def main(args: typing.Optional[typing.List[str]] = None):
    """Execute main function for entry point."""
    argument_parser = build_argument_parser()
    args = args or sys.argv[1:]
    opts = argument_parser.parse_args(args)

    if opts.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('rebulk').setLevel(logging.DEBUG)

    return trakit(opts.value, opts)


if __name__ == '__main__':
    main(sys.argv[1:])
