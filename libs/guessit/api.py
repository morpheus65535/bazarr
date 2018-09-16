#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API functions that can be used by external software
"""

try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error

import os
import traceback

import six

from rebulk.introspector import introspect

from .rules import rebulk_builder
from .options import parse_options, load_config
from .__version__ import __version__


class GuessitException(Exception):
    """
    Exception raised when guessit fails to perform a guess because of an internal error.
    """
    def __init__(self, string, options):
        super(GuessitException, self).__init__("An internal error has occured in guessit.\n"
                                               "===================== Guessit Exception Report =====================\n"
                                               "version=%s\n"
                                               "string=%s\n"
                                               "options=%s\n"
                                               "--------------------------------------------------------------------\n"
                                               "%s"
                                               "--------------------------------------------------------------------\n"
                                               "Please report at "
                                               "https://github.com/guessit-io/guessit/issues.\n"
                                               "====================================================================" %
                                               (__version__, str(string), str(options), traceback.format_exc()))

        self.string = string
        self.options = options


def configure(options, rules_builder=rebulk_builder):
    """
    Load rebulk rules according to advanced configuration in options dictionary.

    :param options:
    :type options: dict
    :param rules_builder:
    :type rules_builder:
    :return:
    """
    default_api.configure(options, rules_builder=rules_builder, force=True)


def guessit(string, options=None):
    """
    Retrieves all matches from string as a dict
    :param string: the filename or release name
    :type string: str
    :param options:
    :type options: str|dict
    :return:
    :rtype:
    """
    return default_api.guessit(string, options)


def properties(options=None):
    """
    Retrieves all properties with possible values that can be guessed
    :param options:
    :type options: str|dict
    :return:
    :rtype:
    """
    return default_api.properties(options)


class GuessItApi(object):
    """
    An api class that can be configured with custom Rebulk configuration.
    """

    def __init__(self):
        """Default constructor."""
        self.rebulk = None

    @classmethod
    def _fix_encoding(cls, value):
        if isinstance(value, list):
            return [cls._fix_encoding(item) for item in value]
        if isinstance(value, dict):
            return {cls._fix_encoding(k): cls._fix_encoding(v) for k, v in value.items()}
        if six.PY2 and isinstance(value, six.text_type):
            return value.encode('utf-8')
        if six.PY3 and isinstance(value, six.binary_type):
            return value.decode('ascii')
        return value

    def configure(self, options, rules_builder=rebulk_builder, force=False):
        """
        Load rebulk rules according to advanced configuration in options dictionary.

        :param options:
        :type options: str|dict
        :param rules_builder:
        :type rules_builder:
        :param force:
        :return:
        :rtype: dict
        """
        options = parse_options(options, True)
        should_load = force or not self.rebulk
        advanced_config = options.pop('advanced_config', None)

        if should_load and not advanced_config:
            advanced_config = load_config(options)['advanced_config']

        options = self._fix_encoding(options)

        if should_load:
            advanced_config = self._fix_encoding(advanced_config)
            self.rebulk = rules_builder(advanced_config)

        return options

    def guessit(self, string, options=None):  # pylint: disable=too-many-branches
        """
        Retrieves all matches from string as a dict
        :param string: the filename or release name
        :type string: str|Path
        :param options:
        :type options: str|dict
        :return:
        :rtype:
        """
        try:
            from pathlib import Path
            if isinstance(string, Path):
                try:
                    # Handle path-like object
                    string = os.fspath(string)
                except AttributeError:
                    string = str(string)
        except ImportError:
            pass

        try:
            options = self.configure(options)
            result_decode = False
            result_encode = False

            if six.PY2:
                if isinstance(string, six.text_type):
                    string = string.encode("utf-8")
                    result_decode = True
                elif isinstance(string, six.binary_type):
                    string = six.binary_type(string)
            if six.PY3:
                if isinstance(string, six.binary_type):
                    string = string.decode('ascii')
                    result_encode = True
                elif isinstance(string, six.text_type):
                    string = six.text_type(string)

            matches = self.rebulk.matches(string, options)
            if result_decode:
                for match in matches:
                    if isinstance(match.value, six.binary_type):
                        match.value = match.value.decode("utf-8")
            if result_encode:
                for match in matches:
                    if isinstance(match.value, six.text_type):
                        match.value = match.value.encode("ascii")
            return matches.to_dict(options.get('advanced', False), options.get('single_value', False),
                                   options.get('enforce_list', False))
        except:
            raise GuessitException(string, options)

    def properties(self, options=None):
        """
        Grab properties and values that can be generated.
        :param options:
        :type options:
        :return:
        :rtype:
        """
        options = self.configure(options)
        unordered = introspect(self.rebulk, options).properties
        ordered = OrderedDict()
        for k in sorted(unordered.keys(), key=six.text_type):
            ordered[k] = list(sorted(unordered[k], key=six.text_type))
        if hasattr(self.rebulk, 'customize_properties'):
            ordered = self.rebulk.customize_properties(ordered)
        return ordered


default_api = GuessItApi()
