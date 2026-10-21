#!/usr/bin/env python
"""
Chain patterns and handle repetiting capture group
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any, Literal, cast, overload

from .loose import call
from .match import Match, Matches
from .pattern import BasePattern, Pattern, filter_match_kwargs
from .remodule import re

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from .builder import ChainBuilder


class _InvalidChainException(Exception):
    """
    Internal exception raised when a chain is not valid
    """


class Chain(Pattern):
    """
    Definition of a pattern chain to search for.

    A ``Chain`` is a matchable :class:`~rebulk.pattern.Pattern`. It is assembled
    through a :class:`~rebulk.builder.ChainBuilder` (returned by ``Builder.chain``),
    which appends :class:`ChainPart` instances to :attr:`parts`.
    """

    def __init__(
        self,
        chain_breaker: Callable[[Matches], bool] | None = None,
        **kwargs: Any,
    ) -> None:
        call(Pattern.__init__, self, **kwargs)
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)
        self.chain_breaker: Callable[[Matches], bool] | None
        if callable(chain_breaker):
            self.chain_breaker = chain_breaker
        else:
            self.chain_breaker = None
        self.parts: list[ChainPart] = []

    def _match(
        self,
        pattern: Any,
        input_string: str,
        context: dict[str, Any] | None = None,
    ) -> Iterator[Match]:
        chain_matches: list[Match] = []
        chain_input_string = input_string
        offset = 0
        while offset < len(input_string):
            chain_found = False
            current_chain_matches: list[Match] = []
            valid_chain = True
            for chain_part in self.parts:
                try:
                    chain_part_matches, raw_chain_part_matches = chain_part.matches(
                        chain_input_string, context, with_raw_matches=True
                    )

                    chain_found, chain_input_string, offset = self._to_next_chain_part(
                        chain_part,
                        chain_part_matches,
                        raw_chain_part_matches,
                        chain_found,
                        input_string,
                        chain_input_string,
                        offset,
                        current_chain_matches,
                    )
                except _InvalidChainException:
                    valid_chain = False
                    if current_chain_matches:
                        offset = current_chain_matches[0].raw_end
                    break
            if not chain_found:
                break
            if current_chain_matches and valid_chain:
                match = self._build_chain_match(current_chain_matches, input_string)
                chain_matches.append(match)

        return chain_matches  # type: ignore[return-value]

    def _to_next_chain_part(
        self,
        chain_part: ChainPart,
        chain_part_matches: list[Match],
        raw_chain_part_matches: list[Match],
        chain_found: bool,
        input_string: str,
        chain_input_string: str,
        offset: int,
        current_chain_matches: list[Match],
    ) -> tuple[bool, str, int]:
        Chain._fix_matches_offset(chain_part_matches, input_string, offset)
        Chain._fix_matches_offset(raw_chain_part_matches, input_string, offset)

        if raw_chain_part_matches:
            grouped_matches_dict = self._group_by_match_index(chain_part_matches)
            grouped_raw_matches_dict = self._group_by_match_index(raw_chain_part_matches)

            for match_index, grouped_raw_matches in grouped_raw_matches_dict.items():
                chain_found = True
                offset = grouped_raw_matches[-1].raw_end
                chain_input_string = input_string[offset:]

                if not chain_part.is_hidden:
                    grouped_matches = grouped_matches_dict.get(match_index, [])
                    if self._chain_breaker_eval(current_chain_matches + grouped_matches):
                        current_chain_matches.extend(grouped_matches)
        return chain_found, chain_input_string, offset

    def _process_match(self, match: Match, match_index: int, child: bool = False) -> bool:
        """
        Handle a match
        :param match:
        :type match:
        :param match_index:
        :type match_index:
        :param child:
        :type child:
        :return:
        :rtype:
        """
        ret = super()._process_match(match, match_index, child=child)
        if ret:
            return True

        if match.children:
            last_pattern = match.children[-1].pattern
            last_pattern_groups = self._group_by_match_index(
                [child_ for child_ in match.children if child_.pattern == last_pattern]
            )

            if last_pattern_groups:
                original_children = Matches(match.children)
                original_end = match.end

                for index in reversed(list(last_pattern_groups)):
                    last_matches = last_pattern_groups[index]
                    for last_match in last_matches:
                        match.children.remove(last_match)
                    match.end = match.children[-1].end if match.children else match.start
                    ret = super()._process_match(match, match_index, child=child)
                    if ret:
                        return True

                match.children = original_children
                match.end = original_end

        return False

    def _build_chain_match(self, current_chain_matches: list[Match], input_string: str) -> Match:
        start: int | None = None
        end: int | None = None
        for match in current_chain_matches:
            if start is None or start > match.start:
                start = match.start
            if end is None or end < match.end:
                end = match.end
        match = cast("Match", call(Match, start, end, pattern=self, input_string=input_string, **self._match_kwargs))
        for chain_match in current_chain_matches:
            if chain_match.children:
                for child in chain_match.children:
                    match.children.append(child)
            if chain_match not in match.children:
                match.children.append(chain_match)
                chain_match.parent = match
        return match

    def _chain_breaker_eval(self, matches: list[Match]) -> bool:
        return not self.chain_breaker or not self.chain_breaker(Matches(matches))

    @staticmethod
    def _fix_matches_offset(chain_part_matches: Iterable[Match], input_string: str, offset: int) -> None:
        for chain_part_match in chain_part_matches:
            if chain_part_match.input_string != input_string:
                chain_part_match.input_string = input_string
                chain_part_match.end += offset
                chain_part_match.start += offset
            if chain_part_match.children:
                Chain._fix_matches_offset(chain_part_match.children, input_string, offset)

    @staticmethod
    def _group_by_match_index(matches: Iterable[Match]) -> dict[int, list[Match]]:
        grouped_matches_dict: dict[int, list[Match]] = {}
        # groupby only groups consecutive equal keys, so sort by match_index first
        # to avoid splitting (and overwriting) groups when matches are unordered.
        sorted_matches = sorted(matches, key=lambda m: m.match_index)
        for match_index, match in itertools.groupby(sorted_matches, lambda m: m.match_index):
            grouped_matches_dict[match_index] = list(match)
        return grouped_matches_dict

    @property
    def match_options(self) -> dict[str, Any]:
        return {}

    @property
    def patterns(self) -> list[Chain]:
        return [self]

    def __repr__(self) -> str:
        defined = ""
        if self.defined_at:
            defined = f"@{self.defined_at}"
        return f"<{self.__class__.__name__}{defined}:{self.parts}>"


class ChainPart(BasePattern):
    """
    Part of a pattern chain.
    """

    def __init__(self, builder: ChainBuilder, pattern: Any) -> None:
        self._builder = builder
        self.pattern = pattern
        self.repeater_start: int = 1
        self.repeater_end: int | None = 1
        self._hidden = False

    @property
    def _chain(self) -> Chain:
        return self._builder._chain

    @property
    def _is_chain_start(self) -> bool:
        return self._chain.parts[0] == self

    @overload
    def matches(
        self,
        input_string: str,
        context: dict[str, Any] | None,
        with_raw_matches: Literal[True],
    ) -> tuple[list[Match], list[Match]]: ...

    @overload
    def matches(
        self,
        input_string: str,
        context: dict[str, Any] | None = ...,
        *,
        with_raw_matches: Literal[True],
    ) -> tuple[list[Match], list[Match]]: ...

    @overload
    def matches(
        self,
        input_string: str,
        context: dict[str, Any] | None = ...,
        with_raw_matches: Literal[False] = ...,
    ) -> list[Match]: ...

    def matches(
        self,
        input_string: str,
        context: dict[str, Any] | None = None,
        with_raw_matches: bool = False,
    ) -> list[Match] | tuple[list[Match], list[Match]]:
        matches, raw_matches = self.pattern.matches(input_string, context=context, with_raw_matches=True)

        matches = self._truncate_repeater(matches, input_string)
        raw_matches = self._truncate_repeater(raw_matches, input_string)

        self._validate_repeater(raw_matches)

        if with_raw_matches:
            return matches, raw_matches

        return matches

    def _truncate_repeater(self, matches: list[Match], input_string: str) -> list[Match]:
        if not matches:
            return matches

        if not self._is_chain_start:
            separator = input_string[0 : matches[0].initiator.raw_start]
            if separator:
                return []

        j = 1
        for i in range(len(matches) - 1):
            separator = input_string[matches[i].initiator.raw_end : matches[i + 1].initiator.raw_start]
            if separator:
                break
            j += 1
        truncated = matches[:j]
        if self.repeater_end is not None:
            truncated = [m for m in truncated if m.match_index < self.repeater_end]
        return truncated

    def _validate_repeater(self, matches: list[Match]) -> None:
        max_match_index = -1
        if matches:
            max_match_index = max(m.match_index for m in matches)
        if max_match_index + 1 < self.repeater_start:
            raise _InvalidChainException

    def chain(self) -> ChainBuilder:
        """
        Nest another patterns chain, using configuration from this chain.
        """
        return self._builder.chain()

    def hidden(self, hidden: bool = True) -> ChainPart:
        """
        Hide chain part results from global chain result

        :param hidden:
        :type hidden:
        :return:
        :rtype:
        """
        self._hidden = hidden
        return self

    @property
    def is_hidden(self) -> bool:
        """
        Check if the chain part is hidden
        :return:
        :rtype:
        """
        return self._hidden

    def regex(self, *pattern: Any, **kwargs: Any) -> ChainPart:
        """
        Add re pattern to the chain.
        """
        return self._builder.regex(*pattern, **kwargs)

    def functional(self, *pattern: Any, **kwargs: Any) -> ChainPart:
        """
        Add functional pattern to the chain.
        """
        return self._builder.functional(*pattern, **kwargs)

    def string(self, *pattern: Any, **kwargs: Any) -> ChainPart:
        """
        Add string pattern to the chain.
        """
        return self._builder.string(*pattern, **kwargs)

    def close(self) -> Any:
        """
        Close the chain builder to continue registering other patterns

        :return:
        :rtype:
        """
        return self._builder.close()

    def repeater(self, value: Any) -> ChainPart:
        """
        Define the repeater of the current chain part.

        :param value:
        :type value:
        :return:
        :rtype:
        """
        try:
            value = int(value)
            self.repeater_start = value
            self.repeater_end = value
            return self
        except ValueError:
            pass
        if value == "+":
            self.repeater_start = 1
            self.repeater_end = None
        if value == "*":
            self.repeater_start = 0
            self.repeater_end = None
        elif value == "?":
            self.repeater_start = 0
            self.repeater_end = 1
        else:
            match = re.match(r"\{\s*(\d*)\s*,?\s*(\d*)\s*\}", value)
            if match:
                start = match.group(1)
                end = match.group(2)
                if start or end:
                    self.repeater_start = int(start) if start else 0
                    self.repeater_end = int(end) if end else None
        return self

    def __repr__(self) -> str:
        return f"{self.pattern}({{{self.repeater_start},{self.repeater_end}}})"
