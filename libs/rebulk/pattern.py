#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abstract pattern class definition along with various implementations (regexp, string, functional)
"""
# pylint: disable=super-init-not-called,wrong-import-position

from abc import ABCMeta, abstractmethod, abstractproperty

import six

from . import debug
from .loose import call, ensure_list, ensure_dict
from .match import Match
from .remodule import re, REGEX_AVAILABLE
from .utils import find_all, is_iterable, get_first_defined


@six.add_metaclass(ABCMeta)
class Pattern(object):
    """
    Definition of a particular pattern to search for.
    """

    def __init__(self, name=None, tags=None, formatter=None, value=None, validator=None, children=False, every=False,
                 private_parent=False, private_children=False, private=False, private_names=None, ignore_names=None,
                 marker=False, format_all=False, validate_all=False, disabled=lambda context: False, log_level=None,
                 properties=None, post_processor=None, **kwargs):
        """
        :param name: Name of this pattern
        :type name: str
        :param tags: List of tags related to this pattern
        :type tags: list[str]
        :param formatter: dict (name, func) of formatter to use with this pattern. name is the match name to support,
        and func a function(input_string) that returns the formatted string. A single formatter function can also be
        passed as a shortcut for {None: formatter}. The returned formatted string with be set in Match.value property.
        :type formatter: dict[str, func] || func
        :param value: dict (name, value) of value to use with this pattern. name is the match name to support,
        and value an object for the match value. A single object value can also be
        passed as a shortcut for {None: value}. The value with be set in Match.value property.
        :type value: dict[str, object] || object
        :param validator: dict (name, func) of validator to use with this pattern. name is the match name to support,
        and func a function(match) that returns the a boolean. A single validator function can also be
        passed as a shortcut for {None: validator}. If return value is False, match will be ignored.
        :param children: generates children instead of parent
        :type children: bool
        :param every: generates both parent and children.
        :type every: bool
        :param private: flag this pattern as beeing private.
        :type private: bool
        :param private_parent: force return of parent and flag parent matches as private.
        :type private_parent: bool
        :param private_children: force return of children and flag children matches as private.
        :type private_children: bool
        :param private_names: force return of named matches as private.
        :type private_names: bool
        :param ignore_names: drop some named matches after validation.
        :type ignore_names: bool
        :param marker: flag this pattern as beeing a marker.
        :type private: bool
        :param format_all if True, pattern will format every match in the hierarchy (even match not yield).
        :type format_all: bool
        :param validate_all if True, pattern will validate every match in the hierarchy (even match not yield).
        :type validate_all: bool
        :param disabled: if True, this pattern is disabled. Can also be a function(context).
        :type disabled: bool|function
        :param log_lvl: Log level associated to this pattern
        :type log_lvl: int
        :param post_process: Post processing function
        :type post_processor: func
        """
        # pylint:disable=too-many-locals,unused-argument
        self.name = name
        self.tags = ensure_list(tags)
        self.formatters, self._default_formatter = ensure_dict(formatter, lambda x: x)
        self.values, self._default_value = ensure_dict(value, None)
        self.validators, self._default_validator = ensure_dict(validator, lambda match: True)
        self.every = every
        self.children = children
        self.private = private
        self.private_names = private_names if private_names else []
        self.ignore_names = ignore_names if ignore_names else []
        self.private_parent = private_parent
        self.private_children = private_children
        self.marker = marker
        self.format_all = format_all
        self.validate_all = validate_all
        if not callable(disabled):
            self.disabled = lambda context: disabled
        else:
            self.disabled = disabled
        self._log_level = log_level
        self._properties = properties
        self.defined_at = debug.defined_at()
        if not callable(post_processor):
            self.post_processor = None
        else:
            self.post_processor = post_processor

    @property
    def log_level(self):
        """
        Log level for this pattern.
        :return:
        :rtype:
        """
        return self._log_level if self._log_level is not None else debug.LOG_LEVEL

    def _yield_children(self, match):
        """
        Does this match has children
        :param match:
        :type match:
        :return:
        :rtype:
        """
        return match.children and (self.children or self.every)

    def _yield_parent(self):
        """
        Does this mat
        :param match:
        :type match:
        :return:
        :rtype:
        """
        return not self.children or self.every

    def _match_parent(self, match, yield_parent):
        """
        Handle a parent match
        :param match:
        :type match:
        :param yield_parent:
        :type yield_parent:
        :return:
        :rtype:
        """
        if not match or match.value == "":
            return False

        pattern_value = get_first_defined(self.values, [match.name, '__parent__', None],
                                          self._default_value)
        if pattern_value:
            match.value = pattern_value

        if yield_parent or self.format_all:
            match.formatter = get_first_defined(self.formatters, [match.name, '__parent__', None],
                                                self._default_formatter)
        if yield_parent or self.validate_all:
            validator = get_first_defined(self.validators, [match.name, '__parent__', None],
                                          self._default_validator)
            if validator and not validator(match):
                return False
        return True

    def _match_child(self, child, yield_children):
        """
        Handle a children match
        :param child:
        :type child:
        :param yield_children:
        :type yield_children:
        :return:
        :rtype:
        """
        if not child or child.value == "":
            return False

        pattern_value = get_first_defined(self.values, [child.name, '__children__', None],
                                          self._default_value)
        if pattern_value:
            child.value = pattern_value

        if yield_children or self.format_all:
            child.formatter = get_first_defined(self.formatters, [child.name, '__children__', None],
                                                self._default_formatter)

        if yield_children or self.validate_all:
            validator = get_first_defined(self.validators, [child.name, '__children__', None],
                                          self._default_validator)
            if validator and not validator(child):
                return False
        return True

    def matches(self, input_string, context=None, with_raw_matches=False):
        """
        Computes all matches for a given input

        :param input_string: the string to parse
        :type input_string: str
        :param context: the context
        :type context: dict
        :param with_raw_matches: should return details
        :type with_raw_matches: dict
        :return: matches based on input_string for this pattern
        :rtype: iterator[Match]
        """
        # pylint: disable=too-many-branches

        matches = []
        raw_matches = []
        for pattern in self.patterns:
            yield_parent = self._yield_parent()
            match_index = -1
            for match in self._match(pattern, input_string, context):
                match_index += 1
                match.match_index = match_index
                raw_matches.append(match)
                yield_children = self._yield_children(match)
                if not self._match_parent(match, yield_parent):
                    continue
                validated = True
                for child in match.children:
                    if not self._match_child(child, yield_children):
                        validated = False
                        break
                if validated:
                    if self.private_parent:
                        match.private = True
                    if self.private_children:
                        for child in match.children:
                            child.private = True
                    if yield_parent or self.private_parent:
                        matches.append(match)
                    if yield_children or self.private_children:
                        for child in match.children:
                            child.match_index = match_index
                            matches.append(child)
        matches = self._matches_post_process(matches)
        self._matches_privatize(matches)
        self._matches_ignore(matches)
        if with_raw_matches:
            return matches, raw_matches
        return matches

    def _matches_post_process(self, matches):
        """
        Post process matches with user defined function
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        if self.post_processor:
            return self.post_processor(matches, self)
        return matches

    def _matches_privatize(self, matches):
        """
        Mark matches included in private_names with private flag.
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        if self.private_names:
            for match in matches:
                if match.name in self.private_names:
                    match.private = True

    def _matches_ignore(self, matches):
        """
        Ignore matches included in ignore_names.
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        if self.ignore_names:
            for match in list(matches):
                if match.name in self.ignore_names:
                    matches.remove(match)

    @abstractproperty
    def patterns(self):  # pragma: no cover
        """
        List of base patterns defined

        :return: A list of base patterns
        :rtype: list
        """
        pass

    @property
    def properties(self):
        """
        Properties names and values that can ben retrieved by this pattern.
        :return:
        :rtype:
        """
        if self._properties:
            return self._properties
        return {}

    @abstractproperty
    def match_options(self):  # pragma: no cover
        """
        dict of default options for generated Match objects

        :return: **options to pass to Match constructor
        :rtype: dict
        """
        pass

    @abstractmethod
    def _match(self, pattern, input_string, context=None):  # pragma: no cover
        """
        Computes all matches for a given pattern and input

        :param pattern: the pattern to use
        :param input_string: the string to parse
        :type input_string: str
        :param context: the context
        :type context: dict
        :return: matches based on input_string for this pattern
        :rtype: iterator[Match]
        """
        pass

    def __repr__(self):
        defined = ""
        if self.defined_at:
            defined = "@%s" % (self.defined_at,)
        return "<%s%s:%s>" % (self.__class__.__name__, defined, self.__repr__patterns__)

    @property
    def __repr__patterns__(self):
        return self.patterns


class StringPattern(Pattern):
    """
    Definition of one or many strings to search for.
    """

    def __init__(self, *patterns, **kwargs):
        super(StringPattern, self).__init__(**kwargs)
        self._patterns = patterns
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)

    @property
    def patterns(self):
        return self._patterns

    @property
    def match_options(self):
        return self._match_kwargs

    def _match(self, pattern, input_string, context=None):
        for index in find_all(input_string, pattern, **self._kwargs):
            yield Match(index, index + len(pattern), pattern=self, input_string=input_string, **self._match_kwargs)


class RePattern(Pattern):
    """
    Definition of one or many regular expression pattern to search for.
    """

    def __init__(self, *patterns, **kwargs):
        super(RePattern, self).__init__(**kwargs)
        self.repeated_captures = REGEX_AVAILABLE
        if 'repeated_captures' in kwargs:
            self.repeated_captures = kwargs.get('repeated_captures')
        if self.repeated_captures and not REGEX_AVAILABLE:  # pragma: no cover
            raise NotImplementedError("repeated_capture is available only with regex module.")
        self.abbreviations = kwargs.get('abbreviations', [])
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)
        self._children_match_kwargs = filter_match_kwargs(kwargs, children=True)
        self._patterns = []
        for pattern in patterns:
            if isinstance(pattern, six.string_types):
                if self.abbreviations and pattern:
                    for key, replacement in self.abbreviations:
                        pattern = pattern.replace(key, replacement)
                pattern = call(re.compile, pattern, **self._kwargs)
            elif isinstance(pattern, dict):
                if self.abbreviations and 'pattern' in pattern:
                    for key, replacement in self.abbreviations:
                        pattern['pattern'] = pattern['pattern'].replace(key, replacement)
                pattern = re.compile(**pattern)
            elif hasattr(pattern, '__iter__'):
                pattern = re.compile(*pattern)
            self._patterns.append(pattern)

    @property
    def patterns(self):
        return self._patterns

    @property
    def __repr__patterns__(self):
        return [pattern.pattern for pattern in self.patterns]

    @property
    def match_options(self):
        return self._match_kwargs

    def _match(self, pattern, input_string, context=None):
        names = dict((v, k) for k, v in pattern.groupindex.items())
        for match_object in pattern.finditer(input_string):
            start = match_object.start()
            end = match_object.end()
            main_match = Match(start, end, pattern=self, input_string=input_string, **self._match_kwargs)

            if pattern.groups:
                for i in range(1, pattern.groups + 1):
                    name = names.get(i, main_match.name)
                    if self.repeated_captures:
                        for start, end in match_object.spans(i):
                            child_match = Match(start, end, name=name, parent=main_match, pattern=self,
                                                input_string=input_string, **self._children_match_kwargs)
                            main_match.children.append(child_match)
                    else:
                        start, end = match_object.span(i)
                        if start > -1 and end > -1:
                            child_match = Match(start, end, name=name, parent=main_match, pattern=self,
                                                input_string=input_string, **self._children_match_kwargs)
                            main_match.children.append(child_match)

            yield main_match


class FunctionalPattern(Pattern):
    """
    Definition of one or many functional pattern to search for.
    """

    def __init__(self, *patterns, **kwargs):
        super(FunctionalPattern, self).__init__(**kwargs)
        self._patterns = patterns
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)

    @property
    def patterns(self):
        return self._patterns

    @property
    def match_options(self):
        return self._match_kwargs

    def _match(self, pattern, input_string, context=None):
        ret = call(pattern, input_string, context, **self._kwargs)
        if ret:
            if not is_iterable(ret) or isinstance(ret, dict) \
                    or (is_iterable(ret) and hasattr(ret, '__getitem__') and isinstance(ret[0], int)):
                args_iterable = [ret]
            else:
                args_iterable = ret
            for args in args_iterable:
                if isinstance(args, dict):
                    options = args
                    options.pop('input_string', None)
                    options.pop('pattern', None)
                    if self._match_kwargs:
                        options = self._match_kwargs.copy()
                        options.update(args)
                    yield Match(pattern=self, input_string=input_string, **options)
                else:
                    kwargs = self._match_kwargs
                    if isinstance(args[-1], dict):
                        kwargs = dict(kwargs)
                        kwargs.update(args[-1])
                        args = args[:-1]
                    yield Match(*args, pattern=self, input_string=input_string, **kwargs)


def filter_match_kwargs(kwargs, children=False):
    """
    Filters out kwargs for Match construction

    :param kwargs:
    :type kwargs: dict
    :param children:
    :type children: Flag to filter children matches
    :return: A filtered dict
    :rtype: dict
    """
    kwargs = kwargs.copy()
    for key in ('pattern', 'start', 'end', 'parent', 'formatter', 'value'):
        if key in kwargs:
            del kwargs[key]
    if children:
        for key in ('name',):
            if key in kwargs:
                del kwargs[key]
    return kwargs
