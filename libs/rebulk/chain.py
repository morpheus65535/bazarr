#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chain patterns and handle repetiting capture group
"""
# pylint: disable=super-init-not-called
import itertools

from .builder import Builder
from .loose import call
from .match import Match, Matches
from .pattern import Pattern, filter_match_kwargs, BasePattern
from .remodule import re


class _InvalidChainException(Exception):
    """
    Internal exception raised when a chain is not valid
    """
    pass


class Chain(Pattern, Builder):
    """
    Definition of a pattern chain to search for.
    """

    def __init__(self, parent, chain_breaker=None, **kwargs):
        Builder.__init__(self)
        call(Pattern.__init__, self, **kwargs)
        self._kwargs = kwargs
        self._match_kwargs = filter_match_kwargs(kwargs)
        if callable(chain_breaker):
            self.chain_breaker = chain_breaker
        else:
            self.chain_breaker = None
        self.parent = parent
        self.parts = []

    def pattern(self, *pattern):
        """

        :param pattern:
        :return:
        """
        if not pattern:
            raise ValueError("One pattern should be given to the chain")
        if len(pattern) > 1:
            raise ValueError("Only one pattern can be given to the chain")
        part = ChainPart(self, pattern[0])
        self.parts.append(part)
        return part

    def close(self):
        """
        Deeply close the chain
        :return: Rebulk instance
        """
        parent = self.parent
        while isinstance(parent, Chain):
            parent = parent.parent
        return parent

    def _match(self, pattern, input_string, context=None):
        # pylint: disable=too-many-locals,too-many-nested-blocks
        chain_matches = []
        chain_input_string = input_string
        offset = 0
        while offset < len(input_string):
            chain_found = False
            current_chain_matches = []
            valid_chain = True
            for chain_part in self.parts:
                try:
                    chain_part_matches, raw_chain_part_matches = chain_part.matches(chain_input_string,
                                                                                    context,
                                                                                    with_raw_matches=True)

                    chain_found, chain_input_string, offset = \
                        self._to_next_chain_part(chain_part, chain_part_matches, raw_chain_part_matches, chain_found,
                                                 input_string, chain_input_string, offset, current_chain_matches)
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

        return chain_matches

    def _to_next_chain_part(self, chain_part, chain_part_matches, raw_chain_part_matches, chain_found,
                            input_string, chain_input_string, offset, current_chain_matches):
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

    def _process_match(self, match, match_index, child=False):
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
        # pylint: disable=too-many-locals
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

    def _build_chain_match(self, current_chain_matches, input_string):
        start = None
        end = None
        for match in current_chain_matches:
            if start is None or start > match.start:
                start = match.start
            if end is None or end < match.end:
                end = match.end
        match = call(Match, start, end, pattern=self, input_string=input_string, **self._match_kwargs)
        for chain_match in current_chain_matches:
            if chain_match.children:
                for child in chain_match.children:
                    match.children.append(child)
            if chain_match not in match.children:
                match.children.append(chain_match)
                chain_match.parent = match
        return match

    def _chain_breaker_eval(self, matches):
        return not self.chain_breaker or not self.chain_breaker(Matches(matches))

    @staticmethod
    def _fix_matches_offset(chain_part_matches, input_string, offset):
        for chain_part_match in chain_part_matches:
            if chain_part_match.input_string != input_string:
                chain_part_match.input_string = input_string
                chain_part_match.end += offset
                chain_part_match.start += offset
            if chain_part_match.children:
                Chain._fix_matches_offset(chain_part_match.children, input_string, offset)

    @staticmethod
    def _group_by_match_index(matches):
        grouped_matches_dict = {}
        for match_index, match in itertools.groupby(matches, lambda m: m.match_index):
            grouped_matches_dict[match_index] = list(match)
        return grouped_matches_dict

    @property
    def match_options(self):
        return {}

    @property
    def patterns(self):
        return [self]

    def __repr__(self):
        defined = ""
        if self.defined_at:
            defined = f"@{self.defined_at}"
        return f"<{self.__class__.__name__}{defined}:{self.parts}>"


class ChainPart(BasePattern):
    """
    Part of a pattern chain.
    """

    def __init__(self, chain, pattern):
        self._chain = chain
        self.pattern = pattern
        self.repeater_start = 1
        self.repeater_end = 1
        self._hidden = False

    @property
    def _is_chain_start(self):
        return self._chain.parts[0] == self

    def matches(self, input_string, context=None, with_raw_matches=False):
        matches, raw_matches = self.pattern.matches(input_string, context=context, with_raw_matches=True)

        matches = self._truncate_repeater(matches, input_string)
        raw_matches = self._truncate_repeater(raw_matches, input_string)

        self._validate_repeater(raw_matches)

        if with_raw_matches:
            return matches, raw_matches

        return matches

    def _truncate_repeater(self, matches, input_string):
        if not matches:
            return matches

        if not self._is_chain_start:
            separator = input_string[0:matches[0].initiator.raw_start]
            if separator:
                return []

        j = 1
        for i in range(0, len(matches) - 1):
            separator = input_string[matches[i].initiator.raw_end:
                                     matches[i + 1].initiator.raw_start]
            if separator:
                break
            j += 1
        truncated = matches[:j]
        if self.repeater_end is not None:
            truncated = [m for m in truncated if m.match_index < self.repeater_end]
        return truncated

    def _validate_repeater(self, matches):
        max_match_index = -1
        if matches:
            max_match_index = max([m.match_index for m in matches])
        if max_match_index + 1 < self.repeater_start:
            raise _InvalidChainException

    def chain(self):
        """
        Add patterns chain, using configuration from this chain

        :return:
        :rtype:
        """
        return self._chain.chain()

    def hidden(self, hidden=True):
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
    def is_hidden(self):
        """
        Check if the chain part is hidden
        :return:
        :rtype:
        """
        return self._hidden

    def regex(self, *pattern, **kwargs):
        """
        Add re pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return self._chain.regex(*pattern, **kwargs)

    def functional(self, *pattern, **kwargs):
        """
        Add functional pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return self._chain.functional(*pattern, **kwargs)

    def string(self, *pattern, **kwargs):
        """
        Add string pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        return self._chain.string(*pattern, **kwargs)

    def close(self):
        """
        Close the chain builder to continue registering other patterns

        :return:
        :rtype:
        """
        return self._chain.close()

    def repeater(self, value):
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
        if value == '+':
            self.repeater_start = 1
            self.repeater_end = None
        if value == '*':
            self.repeater_start = 0
            self.repeater_end = None
        elif value == '?':
            self.repeater_start = 0
            self.repeater_end = 1
        else:
            match = re.match(r'\{\s*(\d*)\s*,?\s*(\d*)\s*\}', value)
            if match:
                start = match.group(1)
                end = match.group(2)
                if start or end:
                    self.repeater_start = int(start) if start else 0
                    self.repeater_end = int(end) if end else None
        return self

    def __repr__(self):
        return f"{self.pattern}({{{self.repeater_start},{self.repeater_end}}})"
