#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Entry point module
"""
# pragma: no cover
from __future__ import print_function

import json
import logging
import os
import sys

import six
from rebulk.__version__ import __version__ as __rebulk_version__

from guessit import api
from guessit.__version__ import __version__
from guessit.jsonutils import GuessitEncoder
from guessit.options import argument_parser, parse_options, load_config, merge_options


try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error


def guess_filename(filename, options):
    """
    Guess a single filename using given options
    :param filename: filename to parse
    :type filename: str
    :param options:
    :type options: dict
    :return:
    :rtype:
    """
    if not options.get('yaml') and not options.get('json') and not options.get('show_property'):
        print('For:', filename)

    guess = api.guessit(filename, options)

    if options.get('show_property'):
        print(guess.get(options.get('show_property'), ''))
        return

    if options.get('json'):
        print(json.dumps(guess, cls=GuessitEncoder, ensure_ascii=False))
    elif options.get('yaml'):
        import yaml
        from guessit import yamlutils

        ystr = yaml.dump({filename: OrderedDict(guess)}, Dumper=yamlutils.CustomDumper, default_flow_style=False,
                         allow_unicode=True)
        i = 0
        for yline in ystr.splitlines():
            if i == 0:
                print("? " + yline[:-1])
            elif i == 1:
                print(":" + yline[1:])
            else:
                print(yline)
            i += 1
    else:
        print('GuessIt found:', json.dumps(guess, cls=GuessitEncoder, indent=4, ensure_ascii=False))


def display_properties(options):
    """
    Display properties
    """
    properties = api.properties(options)

    if options.get('json'):
        if options.get('values'):
            print(json.dumps(properties, cls=GuessitEncoder, ensure_ascii=False))
        else:
            print(json.dumps(list(properties.keys()), cls=GuessitEncoder, ensure_ascii=False))
    elif options.get('yaml'):
        import yaml
        from guessit import yamlutils
        if options.get('values'):
            print(yaml.dump(properties, Dumper=yamlutils.CustomDumper, default_flow_style=False, allow_unicode=True))
        else:
            print(yaml.dump(list(properties.keys()), Dumper=yamlutils.CustomDumper, default_flow_style=False,
                            allow_unicode=True))
    else:
        print('GuessIt properties:')

        properties_list = list(sorted(properties.keys()))
        for property_name in properties_list:
            property_values = properties.get(property_name)
            print(2 * ' ' + '[+] %s' % (property_name,))
            if property_values and options.get('values'):
                for property_value in property_values:
                    print(4 * ' ' + '[!] %s' % (property_value,))


def fix_argv_encoding():
    """
    Fix encoding of sys.argv on windows Python 2
    """
    if six.PY2 and os.name == 'nt':  # pragma: no cover
        # see http://bugs.python.org/issue2128
        import locale

        for i, j in enumerate(sys.argv):
            sys.argv[i] = j.decode(locale.getpreferredencoding())


def main(args=None):  # pylint:disable=too-many-branches
    """
    Main function for entry point
    """
    fix_argv_encoding()

    if args is None:  # pragma: no cover
        options = parse_options()
    else:
        options = parse_options(args)

    config = load_config(options)
    options = merge_options(config, options)

    if options.get('verbose'):
        logging.basicConfig(stream=sys.stdout, format='%(message)s')
        logging.getLogger().setLevel(logging.DEBUG)

    help_required = True

    if options.get('version'):
        print('+-------------------------------------------------------+')
        print('+                   GuessIt ' + __version__ + (28 - len(__version__)) * ' ' + '+')
        print('+-------------------------------------------------------+')
        print('+                   Rebulk ' + __rebulk_version__ + (29 - len(__rebulk_version__)) * ' ' + '+')
        print('+-------------------------------------------------------+')
        print('|      Please report any bug or feature request at      |')
        print('|     https://github.com/guessit-io/guessit/issues.     |')
        print('+-------------------------------------------------------+')
        help_required = False

    if options.get('yaml'):
        try:
            import yaml  # pylint:disable=unused-variable,unused-import
        except ImportError:  # pragma: no cover
            del options['yaml']
            print('PyYAML is not installed. \'--yaml\' option will be ignored ...', file=sys.stderr)

    if options.get('properties') or options.get('values'):
        display_properties(options)
        help_required = False

    filenames = []
    if options.get('filename'):
        for filename in options.get('filename'):
            filenames.append(filename)
    if options.get('input_file'):
        if six.PY2:
            input_file = open(options.get('input_file'), 'r')
        else:
            input_file = open(options.get('input_file'), 'r', encoding='utf-8')
        try:
            filenames.extend([line.strip() for line in input_file.readlines()])
        finally:
            input_file.close()

    filenames = list(filter(lambda f: f, filenames))

    if filenames:
        for filename in filenames:
            help_required = False
            guess_filename(filename, options)

    if help_required:  # pragma: no cover
        argument_parser.print_help()


if __name__ == '__main__':  # pragma: no cover
    main()
