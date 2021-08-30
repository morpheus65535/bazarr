#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Options
"""
import copy
import json
import os
import pkgutil
import shlex

from argparse import ArgumentParser


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
    naming_opts.add_argument('--includes', action='append', dest='includes', default=None,
                             help='List of properties to be detected')
    naming_opts.add_argument('--excludes', action='append', dest='excludes', default=None,
                             help='List of properties to be ignored')

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
    output_opts.add_argument('-i', '--output-input-string', dest='output_input_string', action='store_true',
                             default=False, help='Add input_string property in the output')

    conf_opts = opts.add_argument_group("Configuration")
    conf_opts.add_argument('-c', '--config', dest='config', action='append', default=None,
                           help='Filepath to configuration file. Configuration file contains the same '
                                'options as those from command line options, but option names have "-" characters '
                                'replaced with "_". This configuration will be merged with default and user '
                                'configuration files.')
    conf_opts.add_argument('--no-user-config', dest='no_user_config', action='store_true',
                           default=None,
                           help='Disable user configuration. If not defined, guessit tries to read configuration files '
                                'at ~/.guessit/options.(json|yml|yaml) and ~/.config/guessit/options.(json|yml|yaml)')
    conf_opts.add_argument('--no-default-config', dest='no_default_config', action='store_true',
                           default=None,
                           help='Disable default configuration. This should be done only if you are providing a full '
                                'configuration through user configuration or --config option. If no "advanced_config" '
                                'is provided by another configuration file, it will still be loaded from default '
                                'configuration.')

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
    :type api: boolean
    :return:
    :rtype:
    """
    if isinstance(options, str):
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
    pass  # pylint:disable=unnecessary-pass


def load_config(options):
    """
    Load options from configuration files, if defined and present.
    :param options:
    :type options:
    :return:
    :rtype:
    """
    configurations = []

    if not options.get('no_default_config'):
        default_options_data = pkgutil.get_data('guessit', 'config/options.json').decode('utf-8')
        default_options = json.loads(default_options_data)
        configurations.append(default_options)

    config_files = []

    if not options.get('no_user_config'):
        home_directory = os.path.expanduser("~")
        cwd = os.getcwd()
        yaml_supported = False
        try:
            import yaml  # pylint:disable=unused-variable,unused-import,import-outside-toplevel
            yaml_supported = True
        except ImportError:
            pass

        config_file_locations = get_options_file_locations(home_directory, cwd, yaml_supported)
        config_files = [f for f in config_file_locations if os.path.exists(f)]

    custom_config_files = options.get('config')
    if custom_config_files:
        config_files = config_files + custom_config_files

    for config_file in config_files:
        config_file_options = load_config_file(config_file)
        if config_file_options:
            configurations.append(config_file_options)

    config = {}
    if configurations:
        config = merge_options(*configurations)

    if 'advanced_config' not in config:
        # Guessit doesn't work without advanced_config, so we use default if no configuration files provides it.
        default_options_data = pkgutil.get_data('guessit', 'config/options.json').decode('utf-8')
        default_options = json.loads(default_options_data)
        config['advanced_config'] = default_options['advanced_config']

    return config


def merge_options(*options):
    """
    Merge options into a single options dict.
    :param options:
    :type options:
    :return:
    :rtype:
    """

    merged = {}
    if options:
        if options[0]:
            merged.update(copy.deepcopy(options[0]))

        for options in options[1:]:
            if options:
                pristine = options.get('pristine')

                if pristine is True:
                    merged = {}
                elif pristine:
                    for to_reset in pristine:
                        if to_reset in merged:
                            del merged[to_reset]

                for (option, value) in options.items():
                    merge_option_value(option, value, merged)

    return merged


def merge_option_value(option, value, merged):
    """
    Merge option value
    :param option:
    :param value:
    :param merged:
    :return:
    """
    if value is not None and option != 'pristine':
        if option in merged.keys() and isinstance(merged[option], list):
            for val in value:
                if val not in merged[option] and val is not None:
                    merged[option].append(val)
        elif option in merged.keys() and isinstance(merged[option], dict):
            merged[option] = merge_options(merged[option], value)
        elif isinstance(value, list):
            merged[option] = list(value)
        else:
            merged[option] = value


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
            import yaml  # pylint:disable=import-outside-toplevel
            with open(filepath) as config_file_data:
                return yaml.load(config_file_data, yaml.SafeLoader)
        except ImportError as err:  # pragma: no cover
            raise ConfigurationException('Configuration file extension is not supported. '
                                         'PyYAML should be installed to support "%s" file' % (
                                             filepath,)) from err

    try:
        # Try to load input as JSON
        return json.loads(filepath)
    except:  # pylint: disable=bare-except
        pass

    raise ConfigurationException('Configuration file extension is not supported for "%s" file.' % (filepath,))


def get_options_file_locations(homedir, cwd, yaml_supported=False):
    """
    Get all possible locations for options file.
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
