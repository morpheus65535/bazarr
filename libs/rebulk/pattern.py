#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abstract pattern class definition along with various implementations (regexp, string, functional)
"""
# pylint: disable=super-init-not-called,wrong-import-position

from abc import ABCMeta, abstractmethod

from . import debug
from .formatters import default_formatter
from .loose import call, ensure_list, ensure_dict
from .match import Match
from .remodule import re, REGEX_ENABLED
from .utils import find_all, is_iterable, get_first_defined
from .validators import allways_true


class BasePattern(metaclass=ABCMeta):
    """
    Base class for Pattern like objects
    """

    @abstractmethod
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
        pass


class Pattern(BasePattern, metaclass=ABCMeta):
    """
    Definition of a particular pattern to search for.
    """

    def __init__(self, name=None, tags=None, formatter=None, value=None, validator=None, children=False, every=False,
                 private_parent=False, private_children=False, private=False, private_names=None, ignore_names=None,
                 marker=False, format_all=False, validate_all=False, disabled=lambda context: False, log_level=None,
                 properties=None, post_processor=None, pre_match_processor=None, post_match_processor=None, **kwargs):
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
        :param post_processor: Post processing function
        :type post_processor: func
        :param pre_match_processor: Pre match processing function
        :type pre_match_processor: func
        :param post_match_processor: Post match processing function
        :type post_match_processor: func
        """
        # pylint:disable=too-many-locals,unused-argument
        self.name = name
        self.tags = ensure_list(tags)
        self.formatters, self._default_formatter = ensure_dict(formatter, default_formatter)
        self.values, self._default_value = ensure_dict(value, None)
        self.validators, self._default_validator = ensure_dict(validator, allways_true)
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
        if not callable(pre_match_processor):
            self.pre_match_processor = None
        else:
            self.pre_match_processor = pre_match_processor
        if not callable(post_match_processor):
            self.post_match_processor = None
        else:
            self.post_match_processor = post_match_processor

    @property
    def log_level(self):
        """
        Log level for this pattern.
        :return:
        :rtype:
        """
        return self._log_level if self._log_level is not None else debug.LOG_LEVEL

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
            match_index = 0
            for match in self._match(pattern, input_string, context):
                raw_matches.append(match)
                matches.extend(self._process_matches(match, match_index))
                match_index += 1

        matches = self._post_process_matches(matches)

        if with_raw_matches:
            return matches, raw_matches
        return matches

    @property
    def _should_include_children(self):
        """
        Check if children matches from this pattern should be included in matches results.
        :param match:
        :type match:
        :return:
        :rtype:
        """
        return self.children or self.every

    @property
    def _should_include_parent(self):
        """
        Check is a match from this pattern should be included in matches results.
        :param match:
        :type match:
        :return:
        :rtype:
        """
        return not self.children or self.every

    @staticmethod
    def _match_config_property_keys(match, child=False):
        if match.name:
            yield match.name
        if child:
            yield '__children__'
        else:
            yield '__parent__'
        yield None

    @staticmethod
    def _process_match_index(match, match_index):
        """
        Process match index from this pattern process state.

        :param match:
        :return:
        """
        match.match_index = match_index

    def _process_match_private(self, match, child=False):
        """
        Process match privacy from this pattern configuration.

        :param match:
        :param child:
        :return:
        """

        if match.name and match.name in self.private_names or \
                not child and self.private_parent or \
                child and self.private_children:
            match.private = True

    def _process_match_value(self, match, child=False):
        """
        Process match value from this pattern configuration.
        :param match:
        :return:
        """
        keys = self._match_config_property_keys(match, child=child)
        pattern_value = get_first_defined(self.values, keys, self._default_value)
        if pattern_value:
            match.value = pattern_value

    def _process_match_formatter(self, match, child=False):
        """
        Process match formatter from this pattern configuration.

        :param match:
        :return:
        """
        included = self._should_include_children if child else self._should_include_parent
        if included or self.format_all:
            keys = self._match_config_property_keys(match, child=child)
            match.formatter = get_first_defined(self.formatters, keys, self._default_formatter)

    def _process_match_validator(self, match, child=False):
        """
        Process match validation from this pattern configuration.

        :param match:
        :return: True if match is validated by the configured validator, False otherwise.
        """
        included = self._should_include_children if child else self._should_include_parent
        if included or self.validate_all:
            keys = self._match_config_property_keys(match, child=child)
            validator = get_first_defined(self.validators, keys, self._default_validator)
            if validator and not validator(match):
                return False
        return True

    def _process_match(self, match, match_index, child=False):
        """
        Process match from this pattern by setting all properties from defined configuration
        (index, private, value, formatter, validator, ...).

        :param match:
        :type match:
        :return: True if match is validated by the configured validator, False otherwise.
        :rtype:
        """
        self._process_match_index(match, match_index)
        self._process_match_private(match, child)
        self._process_match_value(match, child)
        self._process_match_formatter(match, child)
        return self._process_match_validator(match, child)

    @staticmethod
    def _process_match_processor(match, processor):
        if processor:
            ret = processor(match)
            if ret is not None:
                return ret
        return match

    def _process_matches(self, match, match_index):
        """
        Process and generate all matches for the given unprocessed match.
        :param match:
        :param match_index:
        :return: Process and dispatched matches.
        """
        match = self._process_match_processor(match, self.pre_match_processor)
        if not match:
            return

        if not self._process_match(match, match_index):
            return

        for child in match.children:
            if not self._process_match(child, match_index, child=True):
                return

        match = self._process_match_processor(match, self.post_match_processor)
        if not match:
            return

        if (self._should_include_parent or self.private_parent) and match.name not in self.ignore_names:
            yield match
        if self._should_include_children or self.private_children:
            children = [x for x in match.children if x.name not in self.ignore_names]
            for child in children:
                yield child

    def _post_process_matches(self, matches):
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

    @property
    @abstractmethod
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

    @property
    @abstractmethod
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
        Computes all unprocess matches for a given pattern and input.

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
            defined = f"@{self.defined_at}"
        return f"<{self.__class__.__name__}{defined}:{self.__repr__patterns__}>"

    @property
    def __repr__patterns__(self):
        return self.patterns


class StringPattern(Pattern):
    """
    Definition of one or many strings to search for.
    """

    def __init__(self, *patterns, **kwargs):
        super().__init__(**kwargs)
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
            match = Match(index, index + len(pattern), pattern=self, input_string=input_string, **self._match_kwargs)
            if match:
                yield match


class RePattern(Pattern):
    """
    Definition of one or many regular expression pattern to search for.
    """

    def __init__(self, *patterns, **kwargs):
        super().__init__(**kwargs)
        self.repeated_captures = REGEX_ENABLED
        if 'repeated_captures' in kwargs:
            self.repeated_captures = kwargs.get('repeated_captures')
        if self.repeated_captures and not REGEX_ENABLED:  # pragma: no cover
            raise NotImplementedError("repeated_capture is available only with regex module.")
        self.abbreviations = kwargs.get('abbreviations', [])
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)
        self._children_match_kwargs = filter_match_kwargs(kwargs, children=True)
        self._patterns = []
        for pattern in patterns:
            if isinstance(pattern, str):
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
                            if child_match:
                                main_match.children.append(child_match)
                    else:
                        start, end = match_object.span(i)
                        if start > -1 and end > -1:
                            child_match = Match(start, end, name=name, parent=main_match, pattern=self,
                                                input_string=input_string, **self._children_match_kwargs)
                            if child_match:
                                main_match.children.append(child_match)

            if main_match:
                yield main_match


class FunctionalPattern(Pattern):
    """
    Definition of one or many functional pattern to search for.
    """

    def __init__(self, *patterns, **kwargs):
        super().__init__(**kwargs)
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
                    match = Match(pattern=self, input_string=input_string, **options)
                    if match:
                        yield match
                else:
                    kwargs = self._match_kwargs
                    if isinstance(args[-1], dict):
                        kwargs = dict(kwargs)
                        kwargs.update(args[-1])
                        args = args[:-1]
                    match = Match(*args, pattern=self, input_string=input_string, **kwargs)
                    if match:
                        yield match


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
