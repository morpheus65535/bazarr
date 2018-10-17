#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Options
"""
import json
import os
import pkgutil
import shlex
from argparse import ArgumentParser

import six


def build_argument_parser():
    """
    Builds the argument parser
    :return: the argument parser
    :rtype: ArgumentParser
    """
    opts = ArgumentParser()
    opts.add_argument(dest='filename', help='Filename or release name to guess', nargs='*')

    naming_opts = opts.add_argument_group("Naming")
    naming_opts.add_argument('-t', '--type', dest='type', default=None,
                             help='The suggested file type: movie, episode. If undefined, type will be guessed.')
    naming_opts.add_argument('-n', '--name-only', dest='name_only', action='store_true', default=None,
                             help='Parse files as name only, considering "/" and "\\" like other separators.')
    naming_opts.add_argument('-Y', '--date-year-first', action='store_true', dest='date_year_first', default=None,
                             help='If short date is found, consider the first digits as the year.')
    naming_opts.add_argument('-D', '--date-day-first', action='store_true', dest='date_day_first', default=None,
                             help='If short date is found, consider the second digits as the day.')
    naming_opts.add_argument('-L', '--allowed-languages', action='append', dest='allowed_languages', default=None,
                             help='Allowed language (can be used multiple times)')
    naming_opts.add_argument('-C', '--allowed-countries', action='append', dest='allowed_countries', default=None,
                             help='Allowed country (can be used multiple times)')
    naming_opts.add_argument('-E', '--episode-prefer-number', action='store_true', dest='episode_prefer_number',
                             default=None,
                             help='Guess "serie.213.avi" as the episode 213. Without this option, '
                                  'it will be guessed as season 2, episode 13')
    naming_opts.add_argument('-T', '--expected-title', action='append', dest='expected_title', default=None,
                             help='Expected title to parse (can be used multiple times)')
    naming_opts.add_argument('-G', '--expected-group', action='append', dest='expected_group', default=None,
                             help='Expected release group (can be used multiple times)')

    input_opts = opts.add_argument_group("Input")
    input_opts.add_argument('-f', '--input-file', dest='input_file', default=None,
                            help='Read filenames from an input text file. File should use UTF-8 charset.')

    output_opts = opts.add_argument_group("Output")
    output_opts.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=None,
                             help='Display debug output')
    output_opts.add_argument('-P', '--show-property', dest='show_property', default=None,
                             help='Display the value of a single property (title, series, video_codec, year, ...)')
    output_opts.add_argument('-a', '--advanced', dest='advanced', action='store_true', default=None,
                             help='Display advanced information for filename guesses, as json output')
    output_opts.add_argument('-s', '--single-value', dest='single_value', action='store_true', default=None,
                             help='Keep only first value found for each property')
    output_opts.add_argument('-l', '--enforce-list', dest='enforce_list', action='store_true', default=None,
                             help='Wrap each found value in a list even when property has a single value')
    output_opts.add_argument('-j', '--json', dest='json', action='store_true', default=None,
                             help='Display information for filename guesses as json output')
    output_opts.add_argument('-y', '--yaml', dest='yaml', action='store_true', default=None,
                             help='Display information for filename guesses as yaml output')

    conf_opts = opts.add_argument_group("Configuration")
    conf_opts.add_argument('-c', '--config', dest='config', action='append', default=None,
                           help='Filepath to the configuration file. Configuration contains the same options as '
                                'those command line options, but option names have "-" characters replaced with "_". '
                                'If not defined, guessit tries to read a configuration default configuration file at '
                                '~/.guessit/options.(json|yml|yaml) and ~/.config/guessit/options.(json|yml|yaml). '
                                'Set to "false" to disable default configuration file loading.')
    conf_opts.add_argument('--no-embedded-config', dest='no_embedded_config', action='store_true',
                           default=None,
                           help='Disable default configuration.')

    information_opts = opts.add_argument_group("Information")
    information_opts.add_argument('-p', '--properties', dest='properties', action='store_true', default=None,
                                  help='Display properties that can be guessed.')
    information_opts.add_argument('-V', '--values', dest='values', action='store_true', default=None,
                                  help='Display property values that can be guessed.')
    information_opts.add_argument('--version', dest='version', action='store_true', default=None,
                                  help='Display the guessit version.')

    return opts


def parse_options(options=None, api=False):
    """
    Parse given option string

    :param options:
    :type options:
    :param api
    :type boolean
    :return:
    :rtype:
    """
    if isinstance(options, six.string_types):
        args = shlex.split(options)
        options = vars(argument_parser.parse_args(args))
    elif options is None:
        if api:
            options = {}
        else:
            options = vars(argument_parser.parse_args())
    elif not isinstance(options, dict):
        options = vars(argument_parser.parse_args(options))
    return options


argument_parser = build_argument_parser()


class ConfigurationException(Exception):
    """
    Exception related to configuration file.
    """
    pass


def load_config(options):
    """
    Load configuration from configuration file, if defined.
    :param options:
    :type options:
    :return:
    :rtype:
    """
    config_files_enabled = True
    custom_config_files = None
    if options.get('config') is not None:
        custom_config_files = options.get('config')
        if not custom_config_files \
                or not custom_config_files[0] \
                or custom_config_files[0].lower() in ['0', 'no', 'false', 'disabled']:
            config_files_enabled = False

    configurations = []
    if config_files_enabled:
        home_directory = os.path.expanduser("~")
        cwd = os.getcwd()
        yaml_supported = False
        try:
            import yaml  # pylint: disable=unused-variable
            yaml_supported = True
        except ImportError:
            pass
        config_file_locations = get_config_file_locations(home_directory, cwd, yaml_supported)
        config_files = [f for f in config_file_locations if os.path.exists(f)]

        if custom_config_files:
            config_files = config_files + custom_config_files

        for config_file in config_files:
            config_file_options = load_config_file(config_file)
            if config_file_options:
                configurations.append(config_file_options)

    if not options.get('no_embedded_config'):
        embedded_options_data = pkgutil.get_data('guessit', 'config/options.json').decode("utf-8")
        embedded_options = json.loads(embedded_options_data)
        configurations.append(embedded_options)

    if configurations:
        configurations.append(options)
        return merge_configurations(*configurations)

    return options


def merge_configurations(*configurations):
    """
    Merge configurations into a single options dict.
    :param configurations:
    :type configurations:
    :return:
    :rtype:
    """

    merged = {}

    for options in configurations:
        pristine = options.get('pristine')

        if pristine:
            if pristine is True:
                merged = {}
            else:
                for to_reset in pristine:
                    if to_reset in merged:
                        del merged[to_reset]

        for (option, value) in options.items():
            if value is not None and option != 'pristine':
                if option in merged.keys() and isinstance(merged[option], list):
                    merged[option].extend(value)
                elif isinstance(value, list):
                    merged[option] = list(value)
                else:
                    merged[option] = value

    return merged


def load_config_file(filepath):
    """
    Load a configuration as an options dict.

    Format of the file is given with filepath extension.
    :param filepath:
    :type filepath:
    :return:
    :rtype:
    """
    if filepath.endswith('.json'):
        with open(filepath) as config_file_data:
            return json.load(config_file_data)
    if filepath.endswith('.yaml') or filepath.endswith('.yml'):
        try:
            import yaml
            with open(filepath) as config_file_data:
                return yaml.load(config_file_data)
        except ImportError:  # pragma: no cover
            raise ConfigurationException('Configuration file extension is not supported. '
                                         'PyYAML should be installed to support "%s" file' % (
                                             filepath,))
    raise ConfigurationException('Configuration file extension is not supported for "%s" file.' % (filepath,))


def get_config_file_locations(homedir, cwd, yaml_supported=False):
    """
    Get all possible locations for configuration file.
    :param homedir: user home directory
    :type homedir: basestring
    :param cwd: current working directory
    :type homedir: basestring
    :return:
    :rtype: list
    """
    locations = []

    configdirs = [(os.path.join(homedir, '.guessit'), 'options'),
                  (os.path.join(homedir, '.config', 'guessit'), 'options'),
                  (cwd, 'guessit.options')]
    configexts = ['json']

    if yaml_supported:
        configexts.append('yaml')
        configexts.append('yml')

    for configdir in configdirs:
        for configext in configexts:
            locations.append(os.path.join(configdir[0], configdir[1] + '.' + configext))

    return locations
