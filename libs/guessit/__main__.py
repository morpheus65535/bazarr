#!/usr/bin/env python
"""
Entry point module
"""

from __future__ import annotations

# pragma: no cover
import json
import logging
import sys
from collections import OrderedDict
from typing import Any

from rebulk.__version__ import __version__ as __rebulk_version__

from guessit import api
from guessit.__version__ import __version__
from guessit.jsonutils import GuessitEncoder
from guessit.options import argument_parser, load_config, merge_options, parse_options


def guess_filename(filename: str, options: dict[str, Any]) -> None:
    """
    Guess a single filename using given options
    :param filename: filename to parse
    :type filename: str
    :param options:
    :type options: dict
    :return:
    :rtype:
    """
    if not options.get("yaml") and not options.get("json") and not options.get("show_property"):
        print("For:", filename)

    guess = api.guessit(filename, options)

    show_property = options.get("show_property")
    if show_property:
        print(guess.get(show_property, ""))
        return

    if options.get("json"):
        print(json.dumps(guess, cls=GuessitEncoder, ensure_ascii=False))
    elif options.get("yaml"):
        import yaml

        from guessit import yamlutils

        ystr = yaml.dump(
            {filename: OrderedDict(guess)}, Dumper=yamlutils.CustomDumper, default_flow_style=False, allow_unicode=True
        )
        for i, yline in enumerate(ystr.splitlines()):
            if i == 0:
                print("? " + yline[:-1])
            elif i == 1:
                print(":" + yline[1:])
            else:
                print(yline)
    else:
        print("GuessIt found:", json.dumps(guess, cls=GuessitEncoder, indent=4, ensure_ascii=False))


def display_properties(options: dict[str, Any]) -> None:
    """
    Display properties
    """
    properties = api.properties(options)

    if options.get("json"):
        if options.get("values"):
            print(json.dumps(properties, cls=GuessitEncoder, ensure_ascii=False))
        else:
            print(json.dumps(list(properties.keys()), cls=GuessitEncoder, ensure_ascii=False))
    elif options.get("yaml"):
        import yaml

        from guessit import yamlutils

        if options.get("values"):
            print(yaml.dump(properties, Dumper=yamlutils.CustomDumper, default_flow_style=False, allow_unicode=True))
        else:
            print(
                yaml.dump(
                    list(properties.keys()), Dumper=yamlutils.CustomDumper, default_flow_style=False, allow_unicode=True
                )
            )
    else:
        print("GuessIt properties:")

        properties_list = sorted(properties.keys())
        for property_name in properties_list:
            property_values = properties.get(property_name)
            print(2 * " " + f"[+] {property_name}")
            if property_values and options.get("values"):
                for property_value in property_values:
                    print(4 * " " + f"[!] {property_value}")


def display_schema(options: dict[str, Any]) -> None:
    """
    Display the property schema or its JSON Schema for the effective configuration.
    """
    data = api.json_schema(options) if options.get("json_schema") else api.schema(options)

    if options.get("yaml"):
        import yaml

        from guessit import yamlutils

        print(yaml.dump(data, Dumper=yamlutils.CustomDumper, default_flow_style=False, allow_unicode=True))
    else:
        indent = None if options.get("json") else 2
        print(json.dumps(data, cls=GuessitEncoder, indent=indent, ensure_ascii=False))


def main(args: list[str] | None = None) -> None:
    """
    Main function for entry point
    """
    options = parse_options() if args is None else parse_options(args)  # pragma: no cover

    config = load_config(options)
    options = merge_options(config, options)

    if options.get("verbose"):
        logging.basicConfig(stream=sys.stdout, format="%(message)s")
        logging.getLogger().setLevel(logging.DEBUG)

    help_required = True

    if options.get("version"):
        print("+-------------------------------------------------------+")
        print("+                   GuessIt " + __version__ + (28 - len(__version__)) * " " + "+")
        print("+-------------------------------------------------------+")
        print("+                   Rebulk " + __rebulk_version__ + (29 - len(__rebulk_version__)) * " " + "+")
        print("+-------------------------------------------------------+")
        print("|      Please report any bug or feature request at      |")
        print("|     https://github.com/guessit-io/guessit/issues.     |")
        print("+-------------------------------------------------------+")
        help_required = False

    if options.get("yaml"):
        try:
            import yaml  # noqa: F401
        except ImportError:  # pragma: no cover
            del options["yaml"]
            print("PyYAML is not installed. '--yaml' option will be ignored ...", file=sys.stderr)

    if options.get("properties") or options.get("values"):
        display_properties(options)
        help_required = False

    if options.get("schema") or options.get("json_schema"):
        display_schema(options)
        help_required = False

    filenames: list[str] = []
    filename_option = options.get("filename")
    if filename_option:
        for filename in filename_option:
            filenames.append(filename)
    input_file_option = options.get("input_file")
    if input_file_option:
        with open(input_file_option, encoding="utf-8") as input_file:
            filenames.extend([line.strip() for line in input_file.readlines()])

    filenames = list(filter(lambda f: f, filenames))

    if filenames:
        for filename in filenames:
            help_required = False
            guess_filename(filename, options)

    if help_required:  # pragma: no cover
        argument_parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
