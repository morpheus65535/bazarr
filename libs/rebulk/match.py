#!/usr/bin/env python
"""
Classes and functions related to matches
"""

from __future__ import annotations

import copy
import dataclasses
import itertools
from collections import OrderedDict, defaultdict
from collections.abc import Callable, Iterable, KeysView, MutableSequence
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
    overload,
)

from .debug import defined_at
from .key import Key
from .loose import ensure_list, filter_index
from .utils import is_iterable

if TYPE_CHECKING:
    from .debug import Frame

T = TypeVar("T")
M = TypeVar("M")
_V = TypeVar("_V")


def _element_type(hint: Any) -> type | None:
    """
    Resolve the *element* type carried by a model field annotation, or ``None``
    when it cannot be pinned to a single concrete type.

    ``list[X]`` resolves to ``X`` (the element a declared key types), an
    ``Optional[X]`` / ``X | None`` to ``X``, and a bare scalar ``type`` to
    itself. Anything else (bare ``Union`` of several types, an unparameterized
    container such as ``list`` / ``dict``, other generics, type vars) yields
    ``None`` so the caller skips the cross-check rather than guessing.
    """
    if hint is Any:
        return None
    origin = get_origin(hint)
    if origin is list:
        args = get_args(hint)
        return _element_type(args[0]) if args else None
    if origin is Union or origin is UnionType:
        non_none = [arg for arg in get_args(hint) if arg is not type(None)]
        return _element_type(non_none[0]) if len(non_none) == 1 else None
    if isinstance(hint, type) and not issubclass(hint, (list, tuple, set, frozenset, dict)):
        return hint
    return None


def _contradicts(hint: Any, declared: type) -> bool:
    """
    True when a model field annotation contradicts a declared key ``value_type``.

    The element types must be related by subclassing in either direction (so a
    ``date`` key matches a ``datetime`` field and vice versa); unrelated concrete
    types (``int`` vs ``str``) contradict. Unresolvable annotations never
    contradict.
    """
    element = _element_type(hint)
    if element is None:
        return False
    return not (issubclass(element, declared) or issubclass(declared, element))


class MatchesDict(OrderedDict[str | None, _V]):
    """
    A custom dict with matches property.

    Generic over the value type: ``to_dict(enforce_list=True)`` returns a
    ``MatchesDict[list[Any]]`` (every name maps to a list), the other modes a
    ``MatchesDict[Any]`` (a name maps to a single value or a list, depending on
    the matches).
    """

    def __init__(self) -> None:
        super().__init__()
        self.matches: dict[str | None, list[Match]] = defaultdict(list)
        self.values_list: dict[str | None, list[Any]] = defaultdict(list)


class _BaseMatches(MutableSequence):  # type: ignore[type-arg]
    """
    A custom list[Match] that automatically maintains name, tag, start and end lookup structures.
    """

    _base = list
    _base_add = _base.append
    _base_remove = _base.remove
    _base_extend = _base.extend

    def __init__(self, matches: Iterable[Match] | None = None, input_string: str | None = None) -> None:
        self.input_string = input_string
        self.declared_keys: dict[str, Key[Any]] = {}
        self._max_end = 0
        self._delegate: list[Match] = []
        self.__name_dict: dict[str | None, list[Match]] | None = None
        self.__tag_dict: dict[str, list[Match]] | None = None
        self.__start_dict: dict[int, list[Match]] | None = None
        self.__end_dict: dict[int, list[Match]] | None = None
        self.__index_dict: dict[int, list[Match]] | None = None
        if matches:
            self.extend(matches)

    @property
    def _name_dict(self) -> dict[str | None, list[Match]]:
        if self.__name_dict is None:
            self.__name_dict = defaultdict(_BaseMatches._base)
            for name, values in itertools.groupby([m for m in self._delegate if m.name], lambda item: item.name):
                _BaseMatches._base_extend(self.__name_dict[name], values)

        return self.__name_dict

    @property
    def _start_dict(self) -> dict[int, list[Match]]:
        if self.__start_dict is None:
            self.__start_dict = defaultdict(_BaseMatches._base)
            for start, values in itertools.groupby(list(self._delegate), lambda item: item.start):
                _BaseMatches._base_extend(self.__start_dict[start], values)

        return self.__start_dict

    @property
    def _end_dict(self) -> dict[int, list[Match]]:
        if self.__end_dict is None:
            self.__end_dict = defaultdict(_BaseMatches._base)
            for start, values in itertools.groupby(list(self._delegate), lambda item: item.end):
                _BaseMatches._base_extend(self.__end_dict[start], values)

        return self.__end_dict

    @property
    def _tag_dict(self) -> dict[str, list[Match]]:
        if self.__tag_dict is None:
            self.__tag_dict = defaultdict(_BaseMatches._base)
            for match in self._delegate:
                for tag in match.tags:
                    _BaseMatches._base_add(self.__tag_dict[tag], match)

        return self.__tag_dict

    @property
    def _index_dict(self) -> dict[int, list[Match]]:
        if self.__index_dict is None:
            self.__index_dict = defaultdict(_BaseMatches._base)
            for match in self._delegate:
                for index in range(*match.span):
                    _BaseMatches._base_add(self.__index_dict[index], match)

        return self.__index_dict

    def _add_match(self, match: Match) -> None:
        """
        Add a match
        :param match:
        :type match: Match
        """
        if self.__name_dict is not None and match.name:
            _BaseMatches._base_add(self._name_dict[match.name], (match))
        if self.__tag_dict is not None:
            for tag in match.tags:
                _BaseMatches._base_add(self._tag_dict[tag], match)
        if self.__start_dict is not None:
            _BaseMatches._base_add(self._start_dict[match.start], match)
        if self.__end_dict is not None:
            _BaseMatches._base_add(self._end_dict[match.end], match)
        if self.__index_dict is not None:
            for index in range(*match.span):
                _BaseMatches._base_add(self._index_dict[index], match)
        self._max_end = max(self._max_end, match.end)

    def _remove_match(self, match: Match) -> None:
        """
        Remove a match
        :param match:
        :type match: Match
        """
        if self.__name_dict is not None and match.name:
            _BaseMatches._base_remove(self._name_dict[match.name], match)
        if self.__tag_dict is not None:
            for tag in match.tags:
                _BaseMatches._base_remove(self._tag_dict[tag], match)
        if self.__start_dict is not None:
            _BaseMatches._base_remove(self._start_dict[match.start], match)
        if self.__end_dict is not None:
            _BaseMatches._base_remove(self._end_dict[match.end], match)
        if self.__index_dict is not None:
            for index in range(*match.span):
                _BaseMatches._base_remove(self._index_dict[index], match)
        if match.end >= self._max_end and not self._end_dict[match.end]:
            self._max_end = max(self._end_dict.keys())

    @overload
    def previous(self, match: Match, predicate: int) -> Match | None: ...
    @overload
    def previous(self, match: Match, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def previous(self, match: Match, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def previous(self, match: Match, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def previous(
        self, match: Match, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None
    ) -> Any:
        """
        Retrieves the nearest previous matches.
        :param match:
        :type match:
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return:
        :rtype:
        """
        current = match.start
        while current > -1:
            previous_matches = self.ending(current)
            if previous_matches:
                return filter_index(previous_matches, predicate, index)
            current -= 1
        return filter_index(_BaseMatches._base(), predicate, index)

    @overload
    def next(self, match: Match, predicate: int) -> Match | None: ...
    @overload
    def next(self, match: Match, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def next(self, match: Match, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def next(self, match: Match, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def next(
        self, match: Match, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None
    ) -> Any:
        """
        Retrieves the nearest next matches.
        :param match:
        :type match:
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return:
        :rtype:
        """
        current = match.start + 1
        while current <= self._max_end:
            next_matches = self.starting(current)
            if next_matches:
                return filter_index(next_matches, predicate, index)
            current += 1
        return filter_index(_BaseMatches._base(), predicate, index)

    @overload
    def named(self, name: str, predicate: int) -> Match | None: ...
    @overload
    def named(self, name: str, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def named(self, name: str, predicate: Callable[[Match], Any] | None) -> list[Match]: ...
    @overload
    def named(self, *names: str, predicate: Callable[[Match], Any] | None = ..., index: int) -> Match | None: ...
    @overload
    def named(self, *names: str, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def named(self, *names: Any, **kwargs: Any) -> Any:
        """
        Retrieves a set of Match objects that have any of the given names.

        Several names can be passed to select matches named by any of them (a
        match has a single name, so this is an "any-of" selection), in the order
        of the given names then match order within each. ``predicate`` and
        ``index`` keep their usual meaning.

        :param names: one or more match names.
        :param predicate:
        :param index:
        :return: set of matches
        :rtype: list[Match]
        """
        predicate = kwargs.pop("predicate", None)
        index = kwargs.pop("index", None)
        if kwargs:
            raise TypeError(f"named() got unexpected keyword arguments {list(kwargs)}")
        name_list: list[str] = []
        extras: list[Any] = []
        for arg in names:
            if isinstance(arg, str) and not extras:
                name_list.append(arg)
            else:
                # positional predicate / index following the names
                extras.append(arg)
        if extras and predicate is None:
            predicate = extras[0]
        if len(extras) > 1 and index is None:
            index = extras[1]
        collection: list[Match] = []
        for name in dict.fromkeys(name_list):
            collection.extend(self._name_dict[name])
        return filter_index(collection, predicate, index)

    @overload
    def tagged(self, tag: str, predicate: int) -> Match | None: ...
    @overload
    def tagged(self, tag: str, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def tagged(self, tag: str, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def tagged(self, tag: str, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def tagged(self, tag: str, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None) -> Any:
        """
        Retrieves a set of Match objects that have the given tag defined.
        :param tag:
        :type tag: str
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._tag_dict[tag]), predicate, index)

    @overload
    def starting(self, start: int, predicate: int) -> Match | None: ...
    @overload
    def starting(self, start: int, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def starting(self, start: int, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def starting(self, start: int, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def starting(
        self, start: int, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None
    ) -> Any:
        """
        Retrieves a set of Match objects that starts at given index.
        :param start: the starting index
        :type start: int
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._start_dict[start]), predicate, index)

    @overload
    def ending(self, end: int, predicate: int) -> Match | None: ...
    @overload
    def ending(self, end: int, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def ending(self, end: int, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def ending(self, end: int, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def ending(self, end: int, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None) -> Any:
        """
        Retrieves a set of Match objects that ends at given index.
        :param end: the ending index
        :type end: int
        :param predicate:
        :type predicate:
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._end_dict[end]), predicate, index)

    @overload
    def range(self, start: int, end: int | None, predicate: int) -> Match | None: ...
    @overload
    def range(
        self, start: int, end: int | None, predicate: Callable[[Match], Any] | None, index: int
    ) -> Match | None: ...
    @overload
    def range(
        self,
        start: int = ...,
        end: int | None = ...,
        predicate: Callable[[Match], Any] | None = ...,
        *,
        index: int,
    ) -> Match | None: ...
    @overload
    def range(
        self, start: int = ..., end: int | None = ..., predicate: Callable[[Match], Any] | None = ...
    ) -> list[Match]: ...
    def range(
        self,
        start: int = 0,
        end: int | None = None,
        predicate: Callable[[Match], Any] | int | None = None,
        index: int | None = None,
    ) -> Any:
        """
        Retrieves a set of Match objects that are available in given range, sorted from start to end.
        :param start: the starting index
        :type start: int
        :param end: the ending index
        :type end: int
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        end = self.max_end if end is None else min(self.max_end, end)
        ret = _BaseMatches._base()
        for match in sorted(self):
            if match.start < end and match.end > start:
                ret.append(match)
        return filter_index(ret, predicate, index)

    @overload
    def chain_before(
        self,
        position: int | Match,
        seps: str,
        start: int = ...,
        predicate: Callable[[Match], Any] | None = ...,
        *,
        index: int,
    ) -> Match | None: ...
    @overload
    def chain_before(
        self, position: int | Match, seps: str, start: int = ..., predicate: Callable[[Match], Any] | None = ...
    ) -> list[Match]: ...
    def chain_before(
        self,
        position: int | Match,
        seps: str,
        start: int = 0,
        predicate: Callable[[Match], Any] | None = None,
        index: int | None = None,
    ) -> Any:
        """
        Retrieves a list of chained matches, before position, matching predicate and separated by characters from seps
        only.
        :param position:
        :type position:
        :param seps:
        :type seps:
        :param start:
        :type start:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        if hasattr(position, "start"):
            position = position.start

        chain = _BaseMatches._base()
        position = min(self.max_end, position)

        for i in reversed(range(start, position)):
            index_matches = self.at_index(i)
            filtered_matches = [index_match for index_match in index_matches if not predicate or predicate(index_match)]
            if filtered_matches:
                for chain_match in filtered_matches:
                    if chain_match not in chain:
                        chain.append(chain_match)
            elif self.input_string[i] not in seps:  # type: ignore[index]
                break

        return filter_index(chain, predicate, index)

    @overload
    def chain_after(
        self,
        position: int | Match,
        seps: str,
        end: int | None = ...,
        predicate: Callable[[Match], Any] | None = ...,
        *,
        index: int,
    ) -> Match | None: ...
    @overload
    def chain_after(
        self, position: int | Match, seps: str, end: int | None = ..., predicate: Callable[[Match], Any] | None = ...
    ) -> list[Match]: ...
    def chain_after(
        self,
        position: int | Match,
        seps: str,
        end: int | None = None,
        predicate: Callable[[Match], Any] | None = None,
        index: int | None = None,
    ) -> Any:
        """
        Retrieves a list of chained matches, after position, matching predicate and separated by characters from seps
        only.
        :param position:
        :type position:
        :param seps:
        :type seps:
        :param end:
        :type end:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        if hasattr(position, "end"):
            position = position.end
        chain = _BaseMatches._base()

        end = self.max_end if end is None else min(self.max_end, end)

        for i in range(position, end):
            index_matches = self.at_index(i)
            filtered_matches = [index_match for index_match in index_matches if not predicate or predicate(index_match)]
            if filtered_matches:
                for chain_match in filtered_matches:
                    if chain_match not in chain:
                        chain.append(chain_match)
            elif self.input_string[i] not in seps:  # type: ignore[index]
                break

        return filter_index(chain, predicate, index)

    @property
    def max_end(self) -> int:
        """
        Retrieves the maximum index.
        :return:
        """
        return max(len(self.input_string), self._max_end) if self.input_string else self._max_end

    def _hole_start(self, position: int, ignore: Callable[[Match], Any] | None = None) -> int:
        """
        Retrieves the start of hole index from position.
        :param position:
        :type position:
        :param ignore:
        :type ignore:
        :return:
        :rtype:
        """
        for lindex in reversed(range(position)):
            for starting in self.starting(lindex):
                if not ignore or not ignore(starting):
                    return lindex
        return 0

    def _hole_end(self, position: int, ignore: Callable[[Match], Any] | None = None) -> int:
        """
        Retrieves the end of hole index from position.
        :param position:
        :type position:
        :param ignore:
        :type ignore:
        :return:
        :rtype:
        """
        for rindex in range(position, self.max_end):
            for starting in self.starting(rindex):
                if not ignore or not ignore(starting):
                    return rindex
        return self.max_end

    @overload
    def holes(
        self,
        start: int = ...,
        end: int | None = ...,
        formatter: Any = ...,
        ignore: Callable[[Match], Any] | None = ...,
        seps: str | None = ...,
        predicate: Callable[[Match], Any] | None = ...,
        *,
        index: int,
    ) -> Match | None: ...
    @overload
    def holes(
        self,
        start: int = ...,
        end: int | None = ...,
        formatter: Any = ...,
        ignore: Callable[[Match], Any] | None = ...,
        seps: str | None = ...,
        predicate: Callable[[Match], Any] | None = ...,
    ) -> list[Match]: ...
    def holes(
        self,
        start: int = 0,
        end: int | None = None,
        formatter: Any = None,
        ignore: Callable[[Match], Any] | None = None,
        seps: str | None = None,
        predicate: Callable[[Match], Any] | int | None = None,
        index: int | None = None,
    ) -> Any:
        """
        Retrieves a set of Match objects that are not defined in given range.
        :param start:
        :type start:
        :param end:
        :type end:
        :param formatter:
        :type formatter:
        :param ignore:
        :type ignore:
        :param seps:
        :type seps:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        assert self.input_string if seps else True, "input_string must be defined when using seps parameter"
        end = self.max_end if end is None else min(self.max_end, end)
        ret: list[Match] = _BaseMatches._base()
        hole = False
        rindex = start

        loop_start = self._hole_start(start, ignore)

        for rindex in range(loop_start, end):
            current = []
            for at_index in self.at_index(rindex):
                if not ignore or not ignore(at_index):
                    current.append(at_index)

            if seps and hole and self.input_string and self.input_string[rindex] in seps:
                hole = False
                ret[-1].end = rindex
            else:
                if not current and not hole:
                    # Open a new hole match
                    hole = True
                    ret.append(
                        Match(max(rindex, start), None, input_string=self.input_string, formatter=formatter)  # type: ignore[arg-type]
                    )
                elif current and hole:
                    # Close current hole match
                    hole = False
                    ret[-1].end = rindex

        if ret and hole:
            # go the the next starting element ...
            ret[-1].end = min(self._hole_end(rindex, ignore), end)
        return filter_index(ret, predicate, index)

    @overload
    def conflicting(self, match: Match, predicate: int) -> Match | None: ...
    @overload
    def conflicting(self, match: Match, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def conflicting(
        self, match: Match, predicate: Callable[[Match], Any] | None = ..., *, index: int
    ) -> Match | None: ...
    @overload
    def conflicting(self, match: Match, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def conflicting(
        self, match: Match, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None
    ) -> Any:
        """
        Retrieves a list of ``Match`` objects that conflicts with given match.
        :param match:
        :type match:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        ret = _BaseMatches._base()

        for i in range(*match.span):
            for at_match in self.at_index(i):
                if at_match not in ret:
                    ret.append(at_match)

        ret.remove(match)

        return filter_index(ret, predicate, index)

    @overload
    def at_match(self, match: Match, predicate: int) -> Match | None: ...
    @overload
    def at_match(self, match: Match, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def at_match(self, match: Match, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def at_match(self, match: Match, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def at_match(
        self, match: Match, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None
    ) -> Any:
        """
        Retrieves a list of matches from given match.
        """
        # Delegating between overloaded methods: the loose impl-level union of
        # predicate/index does not match any single public overload of at_span.
        return self.at_span(match.span, predicate, index)  # type: ignore[arg-type]

    @overload
    def at_span(self, span: tuple[int, int], predicate: int) -> Match | None: ...
    @overload
    def at_span(self, span: tuple[int, int], predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def at_span(
        self, span: tuple[int, int], predicate: Callable[[Match], Any] | None = ..., *, index: int
    ) -> Match | None: ...
    @overload
    def at_span(self, span: tuple[int, int], predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def at_span(
        self,
        span: tuple[int, int],
        predicate: Callable[[Match], Any] | int | None = None,
        index: int | None = None,
    ) -> Any:
        """
        Retrieves a list of matches from given (start, end) tuple.
        """
        starting = self._index_dict[span[0]]
        ending = self._index_dict[span[1] - 1]

        merged = list(starting)
        for marker in ending:
            if marker not in merged:
                merged.append(marker)

        return filter_index(merged, predicate, index)

    @overload
    def at_index(self, pos: int, predicate: int) -> Match | None: ...
    @overload
    def at_index(self, pos: int, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def at_index(self, pos: int, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def at_index(self, pos: int, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def at_index(
        self, pos: int, predicate: Callable[[Match], Any] | int | None = None, index: int | None = None
    ) -> Any:
        """
        Retrieves a list of matches from given position
        """
        return filter_index(self._index_dict[pos], predicate, index)

    @property
    def names(self) -> KeysView[str | None]:
        """
        Retrieve all names.
        :return:
        """
        return self._name_dict.keys()

    @property
    def tags(self) -> KeysView[str]:
        """
        Retrieve all tags.
        :return:
        """
        return self._tag_dict.keys()

    @overload
    def to_dict(
        self, details: bool = ..., first_value: bool = ..., *, enforce_list: Literal[True]
    ) -> MatchesDict[list[Any]]: ...
    @overload
    def to_dict(self, details: bool = ..., first_value: bool = ..., enforce_list: bool = ...) -> MatchesDict[Any]: ...
    def to_dict(self, details: bool = False, first_value: bool = False, enforce_list: bool = False) -> MatchesDict[Any]:
        """
        Converts matches to a dict object.
        :param details if True, values will be complete Match object, else it will be only string Match.value property
        :type details: bool
        :param first_value if True, only the first value will be kept. Else, multiple values will be set as a list in
        the dict.
        :type first_value: bool
        :param enforce_list: if True, value is wrapped in a list even when a single value is found. Else, list values
        are available under `values_list` property of the returned dict object.
        :type enforce_list: bool
        :return:
        :rtype: dict
        """
        ret: MatchesDict[Any] = MatchesDict()
        for match in sorted(self):
            value = match if details else match.value
            ret.matches[match.name].append(match)
            if not enforce_list and value not in ret.values_list[match.name]:
                ret.values_list[match.name].append(value)
            if match.name in ret:
                if not first_value:
                    if not isinstance(ret[match.name], list):
                        if ret[match.name] == value:
                            continue
                        ret[match.name] = [ret[match.name]]
                    else:
                        if value in ret[match.name]:
                            continue
                    ret[match.name].append(value)
            else:
                if enforce_list and not isinstance(value, list):
                    ret[match.name] = [value]
                else:
                    ret[match.name] = value
        return ret

    def __len__(self) -> int:
        return len(self._delegate)

    @overload
    def __getitem__(self, index: int) -> Match: ...

    @overload
    def __getitem__(self, index: slice) -> Matches: ...

    @overload
    def __getitem__(self, index: Key[T]) -> T | None: ...

    def __getitem__(self, index: int | slice | Key[Any]) -> Any:
        if isinstance(index, Key):
            named = self._name_dict[index.name]
            return named[0].value if named else None
        ret = self._delegate[index]
        if isinstance(ret, list):
            return Matches(ret)
        return ret

    def all(self, key: Key[T]) -> list[T]:
        """
        Retrieve all values for the given typed key, in match order.
        """
        return [match.value for match in self._name_dict[key.name]]

    def to(self, model: type[M]) -> M:
        """
        Project named matches onto a typed model.

        ``model`` may be:

        * a ``dataclass`` or ``TypedDict`` — each field is filled from matches
          sharing its name: a ``list[...]`` field collects all values (in match
          order), any other field takes the first value. A field with no value
          is left to its default (dataclass, or raises if required) or omitted
          (``TypedDict``).
        * a ``list[...]`` type of a *scalar* item — returns the values of all
          matches. ``list`` of a ``dataclass`` / ``TypedDict`` is rejected:
          matches are a flat sequence with no record grouping to build several
          structured items from.
        * any other type (e.g. ``int``, ``str``, ``float``) — returns the value
          of the first match, and raises ``LookupError`` if there is none.

        The result is typed end to end via ``def to(self, model: type[M]) -> M``.
        Values are used as produced by each pattern's formatter (see ``key=`` /
        ``formatter=``); ``to`` does not coerce them.

        When the builder declared keys (``declare_keys``), they are carried on the
        :class:`Matches` as :attr:`declared_keys` and cross-checked here: a
        dataclass / ``TypedDict`` field whose (element) type contradicts the
        declared ``value_type`` of a key with the same name raises ``TypeError``,
        closing the typing loop from the build-time declaration to the projected
        value. Fields with no matching declared key are left untouched.
        """
        if get_origin(model) is list:
            (item_type,) = get_args(model) or (object,)
            if dataclasses.is_dataclass(item_type) or is_typeddict(item_type):
                name = getattr(item_type, "__name__", item_type)
                raise TypeError(
                    f"list[{name}] is not supported: matches have no record grouping to build "
                    "several structured items; use list of a scalar type, or a single dataclass/TypedDict"
                )
            return cast("M", [match.value for match in self])
        if dataclasses.is_dataclass(model):
            hints = get_type_hints(model)
            field_names: Iterable[str] = [data_field.name for data_field in dataclasses.fields(model)]
        elif is_typeddict(model):
            hints = get_type_hints(model)
            field_names = hints
        elif isinstance(model, type):
            if not self._delegate:
                raise LookupError(f"no match available to build a {model.__name__}")
            return cast("M", self[0].value)
        else:
            raise TypeError(f"{model!r} is not a dataclass, TypedDict, primitive or list type")
        kwargs: dict[str, Any] = {}
        for name in field_names:
            hint = hints.get(name)
            declared = self.declared_keys.get(name)
            if declared is not None and _contradicts(hint, declared.value_type):
                raise TypeError(
                    f"{model.__name__} field {name!r} typed {hint!r} contradicts "
                    f"declared key {name!r} of value_type {declared.value_type!r}"
                )
            values = [match.value for match in self._name_dict[name]]
            if get_origin(hint) is list:
                kwargs[name] = values
            elif values:
                kwargs[name] = values[0]
        return model(**kwargs)

    def check_declared_keys(self) -> None:
        """
        Assert each named match value matches its declared ``Key.value_type``.

        For every match whose name has a declared :class:`~rebulk.key.Key` (see
        :meth:`~rebulk.builder.PatternFactory.declare_keys`), check that the
        formatted value is an instance of the key's ``value_type``, raising
        ``TypeError`` on a mismatch. This turns the declared output type into an
        enforced contract, catching a per-pattern ``formatter`` override that does
        not actually produce the declared type.

        It is meant to run in development / CI (it does nothing useful unless keys
        are declared); :class:`~rebulk.rebulk.Rebulk` calls it from ``matches``
        only when :data:`rebulk.debug.CHECK_DECLARED_KEYS` is enabled.

        Escape hatches keep it free of false positives:

        * a ``None`` value (an unmatched / cleared match) is skipped;
        * a ``value=``-mapped match (a hardcoded literal that never went through
          the converter) is skipped — its value is not a ``str -> value_type``
          conversion;
        * a ``private`` match is skipped — it is internal scaffolding, not an
          emitted value, and the parent of a ``children=True`` pattern carries
          the raw matched substring (the formatter only runs on the children);
        * each match is checked on its own scalar value, so a name bound to
          several matches (``children``) is validated element by element.
        """
        for match in self:
            key = self.declared_keys.get(match.name) if match.name else None
            if key is None or match.private or match.has_literal_value:
                continue
            value = match.value
            if value is None or isinstance(value, key.value_type):
                continue
            raise TypeError(
                f"match {match.name!r} value {value!r} of type {type(value).__name__!r} "
                f"does not match declared key {key.name!r} value_type {key.value_type!r}"
            )

    @overload
    def __setitem__(self, index: int, match: Match) -> None: ...

    @overload
    def __setitem__(self, index: slice, match: Iterable[Match]) -> None: ...

    def __setitem__(self, index: int | slice, match: Match | Iterable[Match]) -> None:
        self._delegate[index] = match  # type: ignore[index,assignment]
        if isinstance(index, slice):
            for match_item in match:  # type: ignore[union-attr]
                self._add_match(match_item)
            return
        self._add_match(match)  # type: ignore[arg-type]

    def __delitem__(self, index: int | slice) -> None:
        match = self._delegate[index]
        del self._delegate[index]
        if isinstance(match, list):
            # if index is a slice, we has a match list
            for match_item in match:
                self._remove_match(match_item)
        else:
            self._remove_match(match)

    def __repr__(self) -> str:
        return self._delegate.__repr__()

    def insert(self, index: int, value: Match) -> None:
        self._delegate.insert(index, value)
        self._add_match(value)


class Matches(_BaseMatches):
    """
    A custom list[Match] contains matches list.
    """

    def __init__(self, matches: Iterable[Match] | None = None, input_string: str | None = None) -> None:
        self.markers = Markers(input_string=input_string)
        super().__init__(matches=matches, input_string=input_string)

    def _add_match(self, match: Match) -> None:
        assert not match.marker, "A marker match should not be added to <Matches> object"
        super()._add_match(match)


class Markers(_BaseMatches):
    """
    A custom list[Match] containing markers list.
    """

    def __init__(self, matches: Iterable[Match] | None = None, input_string: str | None = None) -> None:
        super().__init__(matches=None, input_string=input_string)

    def _add_match(self, match: Match) -> None:
        assert match.marker, "A non-marker match should not be added to <Markers> object"
        super()._add_match(match)


class Match:
    """
    Object storing values related to a single match
    """

    def __init__(
        self,
        start: int,
        end: int,
        value: Any = None,
        name: str | None = None,
        tags: list[str] | None = None,
        marker: bool | None = None,
        parent: Match | None = None,
        private: bool | None = None,
        pattern: Any = None,
        input_string: str | None = None,
        formatter: Any = None,
        conflict_solver: Any = None,
        **kwargs: Any,
    ) -> None:
        self.start = start
        self.end = end
        self.name = name
        self._value = value
        self.tags: list[str] = ensure_list(tags)
        self.marker = marker
        self.parent = parent
        self.input_string = input_string
        self.formatter = formatter
        self.pattern = pattern
        self.private = private
        self.conflict_solver = conflict_solver
        self._children: Matches | None = None
        self._raw_start: int | None = None
        self._raw_end: int | None = None
        # Set by Pattern processing for matches produced by repeated/multi patterns.
        self.match_index: int = 0
        self.defined_at: Frame | None = pattern.defined_at if pattern else defined_at()

    @property
    def span(self) -> tuple[int, int]:
        """
        2-tuple with start and end indices of the match
        """
        return self.start, self.end

    @property
    def children(self) -> Matches:
        """
        Children matches.
        """
        if self._children is None:
            self._children = Matches(None, self.input_string)
        return self._children

    @children.setter
    def children(self, value: Matches) -> None:
        self._children = value

    @property
    def value(self) -> Any:
        """
        Get the value of the match, using formatter if defined.
        :return:
        :rtype:
        """
        if self._value:
            return self._value
        if self.formatter:
            return self.formatter(self.raw)
        return self.raw

    @value.setter
    def value(self, value: Any) -> None:
        """
        Set the value (hardcode)
        :param value:
        :type value:
        :return:
        :rtype:
        """
        self._value = value

    @property
    def has_literal_value(self) -> bool:
        """
        True when :attr:`value` returns a hardcoded literal (set via ``value=``)
        rather than a formatter / raw-text result.

        Mirrors the truthiness test the :attr:`value` getter uses, so it reflects
        exactly when ``value`` short-circuits to the stored literal.
        """
        return bool(self._value)

    @property
    def names(self) -> set[str | None]:
        """
        Get all names of children
        :return:
        :rtype:
        """
        if not self.children:
            return {self.name}
        ret: set[str | None] = set()
        for child in self.children:
            for name in child.names:
                ret.add(name)
        return ret

    @property
    def raw_start(self) -> int:
        """
        start index of raw value
        :return:
        :rtype:
        """
        if self._raw_start is None:
            return self.start
        return self._raw_start

    @raw_start.setter
    def raw_start(self, value: int | None) -> None:
        """
        Set start index of raw value
        :return:
        :rtype:
        """
        self._raw_start = value

    @property
    def raw_end(self) -> int:
        """
        end index of raw value
        :return:
        :rtype:
        """
        if self._raw_end is None:
            return self.end
        return self._raw_end

    @raw_end.setter
    def raw_end(self, value: int | None) -> None:
        """
        Set end index of raw value
        :return:
        :rtype:
        """
        self._raw_end = value

    @property
    def raw(self) -> str | None:
        """
        Get the raw value of the match, without using hardcoded value nor formatter.
        :return:
        :rtype:
        """
        if self.input_string:
            return self.input_string[self.raw_start : self.raw_end]
        return None

    @property
    def initiator(self) -> Match:
        """
        Retrieve the initiator parent of a match
        :param match:
        :type match:
        :return:
        :rtype:
        """
        match = self
        while match.parent:
            match = match.parent
        return match

    @overload
    def crop(self, crops: Any, predicate: int) -> Match | None: ...
    @overload
    def crop(self, crops: Any, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def crop(self, crops: Any, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def crop(self, crops: Any, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def crop(
        self,
        crops: Any,
        predicate: Callable[[Match], Any] | int | None = None,
        index: int | None = None,
    ) -> Any:
        """
        crop the match with given Match objects or spans tuples
        :param crops:
        :type crops: list or object
        :return: a list of Match objects
        :rtype: list[Match]
        """
        if not is_iterable(crops) or (len(crops) == 2 and isinstance(crops[0], int)):
            crops = [crops]
        initial = copy.deepcopy(self)
        ret = [initial]
        for crop in crops:
            if hasattr(crop, "span"):
                start, end = crop.span
            else:
                start, end = crop
            for current in list(ret):
                if start <= current.start and end >= current.end:
                    # self is included in crop, remove current ...
                    ret.remove(current)
                elif start >= current.start and end <= current.end:
                    # crop is included in self, split current ...
                    right = copy.deepcopy(current)
                    current.end = start
                    if not current:
                        ret.remove(current)
                    right.start = end
                    if right:
                        ret.append(right)
                elif current.end >= end > current.start:
                    current.start = end
                elif current.start <= start < current.end:
                    current.end = start
        return filter_index(ret, predicate, index)

    @overload
    def split(self, seps: str, predicate: int) -> Match | None: ...
    @overload
    def split(self, seps: str, predicate: Callable[[Match], Any] | None, index: int) -> Match | None: ...
    @overload
    def split(self, seps: str, predicate: Callable[[Match], Any] | None = ..., *, index: int) -> Match | None: ...
    @overload
    def split(self, seps: str, predicate: Callable[[Match], Any] | None = ...) -> list[Match]: ...
    def split(
        self,
        seps: str,
        predicate: Callable[[Match], Any] | int | None = None,
        index: int | None = None,
    ) -> Any:
        """
        Split this match in multiple matches using given separators.
        :param seps:
        :type seps: string containing separator characters
        :return: list of new Match objects
        :rtype: list
        """
        current_match: Match = copy.deepcopy(self)
        split_match: Match | None = current_match
        ret: list[Match] = []

        for i, char in enumerate(self.raw):  # type: ignore[arg-type]
            if char in seps:
                if not split_match:
                    split_match = copy.deepcopy(current_match)
                    current_match.end = self.start + i

            else:
                if split_match:
                    split_match.start = self.start + i
                    current_match = split_match
                    ret.append(split_match)
                    split_match = None

        return filter_index(ret, predicate, index)

    def tagged(self, *tags: str) -> bool:
        """
        Check if this match has at least one of the provided tags

        :param tags:
        :return: True if at least one tag is defined, False otherwise.
        """
        return any(tag in self.tags for tag in tags)

    def named(self, *names: str) -> bool:
        """
        Check if one of the children match has one of the provided name

        :param names:
        :return: True if at least one child is named with a given name is defined, False otherwise.
        """
        return any(name in self.names for name in names)

    def __len__(self) -> int:
        return self.end - self.start

    def __hash__(self) -> int:
        # Hash on the span only (a subset of the __eq__ fields), never on the
        # mutable value: a match kept in a set/dict must stay findable after its
        # value is changed. Equal matches still share a hash; same-span matches
        # with different values collide harmlessly and __eq__ tells them apart.
        return hash((Match, self.start, self.end))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Match):
            return (
                self.span == other.span
                and self.value == other.value
                and self.name == other.name
                and self.parent == other.parent
            )
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Match):
            return (
                self.span != other.span
                or self.value != other.value
                or self.name != other.name
                or self.parent != other.parent
            )
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Match):
            return self.span < other.span
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Match):
            return self.span > other.span
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, Match):
            return self.span <= other.span
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Match):
            return self.span >= other.span
        return NotImplemented

    def __repr__(self) -> str:
        flags = ""
        name = ""
        tags = ""
        defined = ""
        initiator = ""
        if self.initiator.value != self.value:
            initiator = f"+initiator={self.initiator.value}"
        if self.private:
            flags += "+private"
        if self.name:
            name = f"+name={self.name}"
        if self.tags:
            tags = f"+tags={self.tags}"
        if self.defined_at:
            defined += f"@{self.defined_at}"
        return f"<{self.value}:{self.span}{flags}{name}{tags}{initiator}{defined}>"
