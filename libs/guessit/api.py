#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API functions that can be used by external software
"""

from collections import OrderedDict

from pathlib import Path
import os
import traceback

from rebulk.introspector import introspect

from .__version__ import __version__
from .options import parse_options, load_config, merge_options
from .rules import rebulk_builder


class GuessitException(Exception):
    """
    Exception raised when guessit fails to perform a guess because of an internal error.
    """

    def __init__(self, string, options):
        super().__init__("An internal error has occured in guessit.\n"
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


def configure(options=None, rules_builder=rebulk_builder, force=False):
    """
    Load configuration files and initialize rebulk rules if required.

    :param options:
    :type options: dict
    :param rules_builder:
    :type rules_builder:
    :param force:
    :type force: bool
    :return:
    """
    default_api.configure(options, rules_builder=rules_builder, force=force)


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


def suggested_expected(titles, options=None):
    """
    Return a list of suggested titles to be used as `expected_title` based on the list of titles
    :param titles: the filename or release name
    :type titles: list|set|dict
    :param options:
    :type options: str|dict
    :return:
    :rtype: list of str
    """
    return default_api.suggested_expected(titles, options)


class GuessItApi(object):
    """
    An api class that can be configured with custom Rebulk configuration.
    """

    def __init__(self):
        """Default constructor."""
        self.rebulk = None
        self.config = None
        self.load_config_options = None
        self.advanced_config = None

    @classmethod
    def _fix_encoding(cls, value):
        if isinstance(value, list):
            return [cls._fix_encoding(item) for item in value]
        if isinstance(value, dict):
            return {cls._fix_encoding(k): cls._fix_encoding(v) for k, v in value.items()}
        if isinstance(value, bytes):
            return value.decode('ascii')
        return value

    @classmethod
    def _has_same_properties(cls, dic1, dic2, values):
        for value in values:
            if dic1.get(value) != dic2.get(value):
                return False
        return True

    def configure(self, options=None, rules_builder=rebulk_builder, force=False, sanitize_options=True):
        """
        Load configuration files and initialize rebulk rules if required.

        :param options:
        :type options: str|dict
        :param rules_builder:
        :type rules_builder:
        :param force:
        :type force: bool
        :return:
        :rtype: dict
        """
        if sanitize_options:
            options = parse_options(options, True)
            options = self._fix_encoding(options)

        if self.config is None or self.load_config_options is None or force or \
                not self._has_same_properties(self.load_config_options,
                                              options,
                                              ['config', 'no_user_config', 'no_default_config']):
            config = load_config(options)
            config = self._fix_encoding(config)
            self.load_config_options = options
        else:
            config = self.config

        advanced_config = merge_options(config.get('advanced_config'), options.get('advanced_config'))

        should_build_rebulk = force or not self.rebulk or not self.advanced_config or \
                              self.advanced_config != advanced_config

        if should_build_rebulk:
            self.advanced_config = advanced_config
            self.rebulk = rules_builder(advanced_config)

        self.config = config
        return self.config

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
        if isinstance(string, Path):
            try:
                # Handle path-like object
                string = os.fspath(string)
            except AttributeError:
                string = str(string)

        try:
            options = parse_options(options, True)
            options = self._fix_encoding(options)
            config = self.configure(options, sanitize_options=False)
            options = merge_options(config, options)
            result_decode = False
            result_encode = False

            if isinstance(string, bytes):
                string = string.decode('ascii')
                result_encode = True

            matches = self.rebulk.matches(string, options)
            if result_decode:
                for match in matches:
                    if isinstance(match.value, bytes):
                        match.value = match.value.decode("utf-8")
            if result_encode:
                for match in matches:
                    if isinstance(match.value, str):
                        match.value = match.value.encode("ascii")
            matches_dict = matches.to_dict(options.get('advanced', False), options.get('single_value', False),
                                           options.get('enforce_list', False))
            output_input_string = options.get('output_input_string', False)
            if output_input_string:
                matches_dict['input_string'] = matches.input_string
            return matches_dict
        except Exception as err:
            raise GuessitException(string, options) from err

    def properties(self, options=None):
        """
        Grab properties and values that can be generated.
        :param options:
        :type options:
        :return:
        :rtype:
        """
        options = parse_options(options, True)
        options = self._fix_encoding(options)
        config = self.configure(options, sanitize_options=False)
        options = merge_options(config, options)
        unordered = introspect(self.rebulk, options).properties
        ordered = OrderedDict()
        for k in sorted(unordered.keys(), key=str):
            ordered[k] = list(sorted(unordered[k], key=str))
        if hasattr(self.rebulk, 'customize_properties'):
            ordered = self.rebulk.customize_properties(ordered)
        return ordered

    def suggested_expected(self, titles, options=None):
        """
        Return a list of suggested titles to be used as `expected_title` based on the list of titles
        :param titles: the filename or release name
        :type titles: list|set|dict
        :param options:
        :type options: str|dict
        :return:
        :rtype: list of str
        """
        suggested = []
        for title in titles:
            guess = self.guessit(title, options)
            if len(guess) != 2 or 'title' not in guess:
                suggested.append(title)

        return suggested


default_api = GuessItApi()
