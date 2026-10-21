#!/usr/bin/env python
"""
Abstract pattern class definition along with various implementations (regexp, string, functional)
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Literal, overload

from . import debug
from .formatters import default_formatter
from .loose import call, ensure_dict, ensure_list
from .match import Match
from .remodule import REGEX_ENABLED, re
from .utils import find_all, get_first_defined, is_iterable
from .validators import allways_true

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence


def _callable_or_none(value: Any) -> Callable[..., Any] | None:
    """Return ``value`` if it is callable, else ``None``."""
    return value if callable(value) else None


class BasePattern(metaclass=ABCMeta):
    """
    Base class for Pattern like objects
    """

    # Computes all matches for a given input. When ``with_raw_matches`` is True, a
    # ``(matches, raw_matches)`` tuple is returned, otherwise a plain list of matches.
    @overload
    @abstractmethod
    def matches(
        self, input_string: str, context: dict[str, Any] | None, with_raw_matches: Literal[True]
    ) -> tuple[list[Match], list[Match]]: ...
    @overload
    @abstractmethod
    def matches(
        self, input_string: str, context: dict[str, Any] | None = ..., *, with_raw_matches: Literal[True]
    ) -> tuple[list[Match], list[Match]]: ...
    @overload
    @abstractmethod
    def matches(
        self, input_string: str, context: dict[str, Any] | None = ..., with_raw_matches: Literal[False] = ...
    ) -> list[Match]: ...


class Pattern(BasePattern, metaclass=ABCMeta):
    """
    Definition of a particular pattern to search for.
    """

    def __init__(
        self,
        name: str | None = None,
        tags: list[str] | None = None,
        formatter: Callable[..., Any] | dict[str | None, Callable[..., Any]] | None = None,
        value: Any = None,
        validator: Callable[..., Any] | dict[str | None, Callable[..., Any]] | None = None,
        children: bool = False,
        every: bool = False,
        private_parent: bool = False,
        private_children: bool = False,
        private: bool = False,
        private_names: list[str] | None = None,
        ignore_names: list[str] | None = None,
        marker: bool = False,
        format_all: bool = False,
        validate_all: bool = False,
        disabled: bool | Callable[[dict[str, Any] | None], bool] = lambda context: False,
        log_level: int | None = None,
        properties: dict[str, Any] | None = None,
        post_processor: Callable[..., Any] | None = None,
        pre_match_processor: Callable[..., Any] | None = None,
        post_match_processor: Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> None:
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
        self.name = name
        self.tags: list[str] = ensure_list(tags)
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
        self.disabled: Callable[[dict[str, Any] | None], bool]
        if not callable(disabled):
            self.disabled = lambda context: disabled
        else:
            self.disabled = disabled
        self._log_level = log_level
        self._properties = properties
        self.defined_at = debug.defined_at()
        self.post_processor = _callable_or_none(post_processor)
        self.pre_match_processor = _callable_or_none(pre_match_processor)
        self.post_match_processor = _callable_or_none(post_match_processor)

    @property
    def log_level(self) -> int:
        """
        Log level for this pattern.
        :return:
        :rtype:
        """
        return self._log_level if self._log_level is not None else debug.LOG_LEVEL

    @overload
    def matches(
        self, input_string: str, context: dict[str, Any] | None, with_raw_matches: Literal[True]
    ) -> tuple[list[Match], list[Match]]: ...
    @overload
    def matches(
        self, input_string: str, context: dict[str, Any] | None = ..., *, with_raw_matches: Literal[True]
    ) -> tuple[list[Match], list[Match]]: ...
    @overload
    def matches(
        self, input_string: str, context: dict[str, Any] | None = ..., with_raw_matches: Literal[False] = ...
    ) -> list[Match]: ...
    def matches(
        self,
        input_string: str,
        context: dict[str, Any] | None = None,
        with_raw_matches: bool = False,
    ) -> list[Match] | tuple[list[Match], list[Match]]:
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

        matches: list[Match] = []
        raw_matches: list[Match] = []

        for pattern in self.patterns:
            for match_index, match in enumerate(self._match(pattern, input_string, context)):
                raw_matches.append(match)
                matches.extend(self._process_matches(match, match_index))

        matches = self._post_process_matches(matches)

        if with_raw_matches:
            return matches, raw_matches
        return matches

    @property
    def _should_include_children(self) -> bool:
        """
        Check if children matches from this pattern should be included in matches results.
        :param match:
        :type match:
        :return:
        :rtype:
        """
        return self.children or self.every

    @property
    def _should_include_parent(self) -> bool:
        """
        Check is a match from this pattern should be included in matches results.
        :param match:
        :type match:
        :return:
        :rtype:
        """
        return not self.children or self.every

    @staticmethod
    def _match_config_property_keys(match: Match, child: bool = False) -> Iterator[str | None]:
        if match.name:
            yield match.name
        if child:
            yield "__children__"
        else:
            yield "__parent__"
        yield None

    @staticmethod
    def _process_match_index(match: Match, match_index: int) -> None:
        """
        Process match index from this pattern process state.

        :param match:
        :return:
        """
        match.match_index = match_index

    def _process_match_private(self, match: Match, child: bool = False) -> None:
        """
        Process match privacy from this pattern configuration.

        :param match:
        :param child:
        :return:
        """

        if (
            (match.name and match.name in self.private_names)
            or (not child and self.private_parent)
            or (child and self.private_children)
        ):
            match.private = True

    def _process_match_value(self, match: Match, child: bool = False) -> None:
        """
        Process match value from this pattern configuration.
        :param match:
        :return:
        """
        keys = self._match_config_property_keys(match, child=child)
        pattern_value = get_first_defined(self.values, keys, self._default_value)
        if pattern_value:
            match.value = pattern_value

    def _process_match_formatter(self, match: Match, child: bool = False) -> None:
        """
        Process match formatter from this pattern configuration.

        :param match:
        :return:
        """
        included = self._should_include_children if child else self._should_include_parent
        if included or self.format_all:
            keys = self._match_config_property_keys(match, child=child)
            match.formatter = get_first_defined(self.formatters, keys, self._default_formatter)

    def _process_match_validator(self, match: Match, child: bool = False) -> bool:
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

    def _process_match(self, match: Match, match_index: int, child: bool = False) -> bool:
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
    def _process_match_processor(match: Match, processor: Callable[..., Any] | None) -> Match:
        if processor:
            ret: Match = processor(match)
            if ret is not None:
                return ret
        return match

    def _process_matches(self, match: Match, match_index: int) -> Iterator[Match]:
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
            yield from children

    def _post_process_matches(self, matches: list[Match]) -> list[Match]:
        """
        Post process matches with user defined function
        :param matches:
        :type matches:
        :return:
        :rtype:
        """
        if self.post_processor:
            processed: list[Match] = self.post_processor(matches, self)
            return processed
        return matches

    @property
    @abstractmethod
    def patterns(self) -> Sequence[Any]:  # pragma: no cover
        """
        List of base patterns defined

        :return: A list of base patterns
        :rtype: list
        """

    @property
    def properties(self) -> dict[str, Any]:
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
    def match_options(self) -> dict[str, Any]:  # pragma: no cover
        """
        dict of default options for generated Match objects

        :return: **options to pass to Match constructor
        :rtype: dict
        """

    @abstractmethod
    def _match(
        self,
        pattern: Any,
        input_string: str,
        context: dict[str, Any] | None = None,
    ) -> Iterator[Match]:  # pragma: no cover
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

    def __repr__(self) -> str:
        defined = ""
        if self.defined_at:
            defined = f"@{self.defined_at}"
        return f"<{self.__class__.__name__}{defined}:{self.__repr__patterns__}>"

    @property
    def __repr__patterns__(self) -> Sequence[Any]:
        return self.patterns


class StringPattern(Pattern):
    """
    Definition of one or many strings to search for.
    """

    def __init__(self, *patterns: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._patterns = patterns
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)

    @property
    def patterns(self) -> Sequence[Any]:
        return self._patterns

    @property
    def match_options(self) -> dict[str, Any]:
        return self._match_kwargs

    def _match(self, pattern: Any, input_string: str, context: dict[str, Any] | None = None) -> Iterator[Match]:
        for index in find_all(input_string, pattern, **self._kwargs):
            match = Match(index, index + len(pattern), pattern=self, input_string=input_string, **self._match_kwargs)
            if match:
                yield match


class RePattern(Pattern):
    """
    Definition of one or many regular expression pattern to search for.
    """

    def __init__(self, *patterns: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.repeated_captures: bool = REGEX_ENABLED
        if "repeated_captures" in kwargs:
            self.repeated_captures = bool(kwargs.get("repeated_captures"))
        if self.repeated_captures and not REGEX_ENABLED:  # pragma: no cover
            raise NotImplementedError("repeated_capture is available only with regex module.")
        self.abbreviations = kwargs.get("abbreviations", [])
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)
        self._children_match_kwargs = filter_match_kwargs(kwargs, children=True)
        self._patterns: list[Any] = []
        for pattern in patterns:
            if isinstance(pattern, str):
                if self.abbreviations and pattern:
                    for key, replacement in self.abbreviations:
                        pattern = pattern.replace(key, replacement)
                pattern = call(re.compile, pattern, **self._kwargs)
            elif isinstance(pattern, dict):
                if self.abbreviations and "pattern" in pattern:
                    for key, replacement in self.abbreviations:
                        pattern["pattern"] = pattern["pattern"].replace(key, replacement)
                pattern = re.compile(**pattern)
            elif hasattr(pattern, "__iter__"):
                pattern = re.compile(*pattern)
            self._patterns.append(pattern)

    @property
    def patterns(self) -> Sequence[Any]:
        return self._patterns

    @property
    def __repr__patterns__(self) -> Sequence[Any]:
        return [pattern.pattern for pattern in self.patterns]

    @property
    def match_options(self) -> dict[str, Any]:
        return self._match_kwargs

    def _match(self, pattern: Any, input_string: str, context: dict[str, Any] | None = None) -> Iterator[Match]:
        names = {v: k for k, v in pattern.groupindex.items()}
        for match_object in pattern.finditer(input_string):
            start = match_object.start()
            end = match_object.end()
            main_match = Match(start, end, pattern=self, input_string=input_string, **self._match_kwargs)

            if pattern.groups:
                for i in range(1, pattern.groups + 1):
                    name = names.get(i, main_match.name)
                    if self.repeated_captures:
                        spans = match_object.spans(i)
                    else:
                        span = match_object.span(i)
                        spans = [span] if span[0] > -1 and span[1] > -1 else []
                    for child_start, child_end in spans:
                        child_match = Match(
                            child_start,
                            child_end,
                            name=name,
                            parent=main_match,
                            pattern=self,
                            input_string=input_string,
                            **self._children_match_kwargs,
                        )
                        if child_match:
                            main_match.children.append(child_match)

            if main_match:
                yield main_match


class FunctionalPattern(Pattern):
    """
    Definition of one or many functional pattern to search for.
    """

    def __init__(self, *patterns: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._patterns = patterns
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)

    @property
    def patterns(self) -> Sequence[Any]:
        return self._patterns

    @property
    def match_options(self) -> dict[str, Any]:
        return self._match_kwargs

    def _match(self, pattern: Any, input_string: str, context: dict[str, Any] | None = None) -> Iterator[Match]:
        ret = call(pattern, input_string, context, **self._kwargs)
        if ret:
            args_iterable: Any
            if (
                not is_iterable(ret)
                or isinstance(ret, dict)
                or (is_iterable(ret) and hasattr(ret, "__getitem__") and isinstance(ret[0], int))
            ):
                args_iterable = [ret]
            else:
                args_iterable = ret
            for args in args_iterable:
                if isinstance(args, dict):
                    options = args
                    options.pop("input_string", None)
                    options.pop("pattern", None)
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
                    match = Match(*args, pattern=self, input_string=input_string, **kwargs)  # type: ignore[misc]
                    if match:
                        yield match


def filter_match_kwargs(kwargs: dict[str, Any], children: bool = False) -> dict[str, Any]:
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
    for key in ("pattern", "start", "end", "parent", "formatter", "value"):
        if key in kwargs:
            del kwargs[key]
    if children:
        for key in ("name",):
            if key in kwargs:
                del kwargs[key]
    return kwargs
