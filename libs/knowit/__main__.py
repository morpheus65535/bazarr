import argparse
import io
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
    bugreport,
    collect,
    pathcheck,
)
from knowit.environment import format_section
from knowit.provider import ProviderError
from knowit.serializer import (
    get_json_encoder,
    get_yaml_dumper,
)
from knowit.utils import recurse_paths

# A media path may hold characters the console cannot encode, which is a common cause
# of reports in itself. Escaping them keeps the output readable instead of failing with
# a UnicodeEncodeError on top of the problem being reported.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(errors='backslashreplace')

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
        help='Print information for debugging knowit and for reporting bugs.',
    )
    output_opts.add_argument(
        '--report', action='store_true', dest='report', help='Parse media and report all non-detected values'
    )
    output_opts.add_argument('-y', '--yaml', action='store_true', dest='yaml', help='Display output in yaml format')
    output_opts.add_argument(
        '-N', '--no-units', action='store_true', dest='no_units', help='Display output without units'
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

    report_opts = opts.add_argument_group('Bug reporting')
    report_opts.add_argument(
        '--bug-report',
        action='store_true',
        dest='bug_report',
        help='Write a report with the environment and the raw output of every provider, to attach to an issue.',
    )
    report_opts.add_argument(
        '--bug-report-output',
        dest='bug_report_output',
        metavar='FILE',
        help='Where to write the bug report. Use - to write it to the standard output.',
        type=str,
    )
    report_opts.add_argument(
        '--no-redact',
        action='store_true',
        dest='no_redact',
        help='Do not mask titles, file names and tags in the bug report or the collected data.',
    )
    report_opts.add_argument(
        '--check-name',
        dest='check_name',
        metavar='NAME',
        help='Check whether a file name makes a provider fail. No media file is needed.',
        type=str,
    )

    collect_opts = opts.add_argument_group('Collect')
    collect_opts.add_argument(
        '--collect',
        action='store_true',
        dest='collect',
        help='Write the output of every provider for each file, to improve knowit. Use --no-redact to keep titles.',
    )
    collect_opts.add_argument(
        '-o',
        '--collect-output',
        dest='collect_output',
        metavar='FILE',
        help=f'Where to write the collected data, default {collect.DEFAULT_OUTPUT}. A run continues an existing file.',
        type=str,
    )

    collect_opts.add_argument(
        '--deep',
        action='store_true',
        dest='deep',
        help='Also read the first video frames with ffprobe, for HDR10+ and Dolby Vision data. Slower.',
    )

    information_opts = opts.add_argument_group('Information')
    information_opts.add_argument('--version', dest='version', action='store_true', help='Display knowit version.')

    return opts


def knowit(
    video_path: str | os.PathLike[str],
    options: argparse.Namespace,
    context: typing.MutableMapping[str, typing.Any],
) -> typing.Mapping[str, typing.Any]:
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
    context: typing.Mapping[str, typing.Any],
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
    context: typing.Mapping[str, typing.Any],
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
    context: typing.Mapping[str, typing.Any],
) -> str:
    """Convert info to string using json or yaml format."""
    convert = _as_yaml if options.yaml else _as_json
    return convert(info, context)


#: Options that drive the CLI itself and mean nothing to a provider.
CLI_ONLY_OPTIONS = frozenset(
    {
        'videopath',
        'bug_report',
        'bug_report_output',
        'check_name',
        'collect',
        'collect_output',
        'deep',
        'no_redact',
        'version',
        'yaml',
    }
)


def build_context(options: argparse.Namespace) -> dict[str, typing.Any]:
    """Build the context passed to the api from the command line options."""
    return {k: v for k, v in vars(options).items() if v is not None and k not in CLI_ONLY_OPTIONS}


def write_bug_report(paths: list[str], options: argparse.Namespace) -> None:
    """Build a bug report and write it where the user asked for it."""
    context = build_context(options)
    context.pop('report', None)
    report = bugreport.build_report(paths, context, anonymize=not options.no_redact)
    content = bugreport.dump_report(report)

    destination = options.bug_report_output or bugreport.default_output_path()
    if destination == '-':
        console.info(content)
        return

    try:
        with open(destination, 'w', encoding='utf-8') as stream:
            stream.write(content)
    except OSError:
        logger.exception('Could not write the bug report, printing it instead')
        console.info(content)
        return

    console.info('Bug report written to %s', destination)
    if not options.no_redact:
        console.info('Titles, file names and tags were masked. Use --no-redact to keep them.')
    console.info('Please attach it to an issue at %s/issues.', __url__)


def run_collect(paths: list[str], options: argparse.Namespace) -> None:
    """Collect the output of every provider for each file, and print a summary."""
    context = build_context(options)
    output = options.collect_output or collect.DEFAULT_OUTPUT
    total = len(paths)

    def on_file(index: int, video_path: str, status: str) -> None:
        console.info('[%d/%d] %s: %s', index, total, status, video_path)

    summary = collect.run(paths, output, context, anonymize=not options.no_redact, deep=options.deep, on_file=on_file)

    console.info('')
    if summary.get('interrupted'):
        console.info('Stopped. Run the same command again to continue.')
    console.info(
        'Files: %d, captured: %d, skipped (already in the output): %d',
        summary['files'],
        summary['captured'],
        summary['skipped'],
    )
    for name, count in summary['errors'].items():
        console.info('%s failed on %d files', name, count)
    if summary['unknown']:
        console.info('Unknown values:')
        console.info(dumps(summary['unknown'], options, vars(options)))
    console.info('Written to %s', output)
    if not options.no_redact:
        console.info('Titles, file names and tags were masked. Use --no-redact to keep them.')


def run_check_name(paths: list[str], options: argparse.Namespace) -> None:
    """Check a file name and print the outcome for each provider."""
    context = build_context(options)
    context.pop('report', None)
    result = pathcheck.check_name(options.check_name, context, paths[0] if paths else None)

    console.info('Checking the name: %s', result['name'])
    console.info('Using %s', result['sample'])
    console.info('')

    path_info = (result['candidate'] or {}).get('path')
    if path_info:
        console.info('\n'.join(format_section('path', path_info)))
        console.info('')

    console.info('\n'.join(format_section('result', result['verdict'])))
    console.info('')
    console.info('Add --bug-report-output to keep the full detail:')
    console.info('  knowit --check-name %r --bug-report-output report.yml', options.check_name)

    if options.bug_report_output:
        content = bugreport.dump_report(result)
        with open(options.bug_report_output, 'w', encoding='utf-8') as stream:
            stream.write(content)
        console.info('Full result written to %s', options.bug_report_output)


def main(args: list[str] | None = None) -> None:
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

    if options.check_name:
        run_check_name(paths, options)
        return

    if options.collect:
        run_collect(paths, options)
        return

    if options.bug_report:
        write_bug_report(paths, options)
        return

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
