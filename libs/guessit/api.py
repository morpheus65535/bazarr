#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API functions that can be used by external software
"""
try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error

import traceback

import six

from rebulk.introspector import introspect

from .rules import rebulk_builder
from .options import parse_options
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


def guessit(string, options=None):
    """
    Retrieves all matches from string as a dict
    :param string: the filename or release name
    :type string: str
    :param options: the filename or release name
    :type options: str|dict
    :return:
    :rtype:
    """
    return default_api.guessit(string, options)


def properties(options=None):
    """
    Retrieves all properties with possible values that can be guessed
    :param options:
    :type options:
    :return:
    :rtype:
    """
    return default_api.properties(options)


class GuessItApi(object):
    """
    An api class that can be configured with custom Rebulk configuration.
    """

    def __init__(self, rebulk):
        """
        :param rebulk: Rebulk instance to use.
        :type rebulk: Rebulk
        :return:
        :rtype:
        """
        self.rebulk = rebulk

    @staticmethod
    def _fix_option_encoding(value):
        if isinstance(value, list):
            return [GuessItApi._fix_option_encoding(item) for item in value]
        if six.PY2 and isinstance(value, six.text_type):
            return value.encode("utf-8")
        if six.PY3 and isinstance(value, six.binary_type):
            return value.decode('ascii')
        return value

    def guessit(self, string, options=None):
        """
        Retrieves all matches from string as a dict
        :param string: the filename or release name
        :type string: str
        :param options: the filename or release name
        :type options: str|dict
        :return:
        :rtype:
        """
        try:
            options = parse_options(options, True)
            result_decode = False
            result_encode = False

            fixed_options = {}
            for (key, value) in options.items():
                key = GuessItApi._fix_option_encoding(key)
                value = GuessItApi._fix_option_encoding(value)
                fixed_options[key] = value
            options = fixed_options

            if six.PY2 and isinstance(string, six.text_type):
                string = string.encode("utf-8")
                result_decode = True
            if six.PY3 and isinstance(string, six.binary_type):
                string = string.decode('ascii')
                result_encode = True
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
        unordered = introspect(self.rebulk, options).properties
        ordered = OrderedDict()
        for k in sorted(unordered.keys(), key=six.text_type):
            ordered[k] = list(sorted(unordered[k], key=six.text_type))
        if hasattr(self.rebulk, 'customize_properties'):
            ordered = self.rebulk.customize_properties(ordered)
        return ordered


default_api = GuessItApi(rebulk_builder())
