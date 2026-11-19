#!/usr/bin/env python
"""
Introspect rebulk object to retrieve capabilities.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast

from .pattern import FunctionalPattern, Pattern, RePattern, StringPattern
from .utils import extend_safe

if TYPE_CHECKING:
    from .rebulk import Rebulk
    from .rules import CustomRule


class Description(metaclass=ABCMeta):
    """
    Abstract class for a description.
    """

    @property
    @abstractmethod
    def properties(self) -> dict[str, list[Any]]:  # pragma: no cover
        """
        Properties of described object.
        :return: all properties that described object can generate grouped by name.
        :rtype: dict
        """


class PatternDescription(Description):
    """
    Description of a pattern.
    """

    def __init__(self, pattern: Pattern) -> None:
        self.pattern = pattern
        self._properties: defaultdict[str, list[Any]] = defaultdict(list)

        if pattern.properties:
            for key, values in pattern.properties.items():
                extend_safe(self._properties[key], values)
        else:
            # A `value=` given to the pattern is stored in `pattern.values` (keyed by match
            # name, or `None` for the default), not in `match_options`. When set, it is the
            # introspected property value.
            pattern_values = {
                (value_name if value_name else pattern.name): value
                for value_name, value in pattern.values.items()
                if value is not None
            }
            if pattern_values:
                for value_key, value in pattern_values.items():
                    extend_safe(self._properties[cast("str", value_key)], [value])
            elif isinstance(pattern, StringPattern):
                extend_safe(self._properties[cast("str", pattern.name)], pattern.patterns)
            elif isinstance(pattern, RePattern):
                if pattern.name and pattern.name not in pattern.private_names:
                    extend_safe(self._properties[pattern.name], [None])
                if not pattern.private_children:
                    for regex_pattern in pattern.patterns:
                        for group_name in regex_pattern.groupindex:
                            if group_name not in pattern.private_names:
                                extend_safe(self._properties[group_name], [None])
            elif isinstance(pattern, FunctionalPattern) and pattern.name and pattern.name not in pattern.private_names:
                extend_safe(self._properties[pattern.name], [None])

    @property
    def properties(self) -> dict[str, list[Any]]:
        """
        Properties for this rule.
        :return:
        :rtype: dict
        """
        return self._properties


class RuleDescription(Description):
    """
    Description of a rule.
    """

    def __init__(self, rule: CustomRule) -> None:
        self.rule = rule

        self._properties: defaultdict[str, list[Any]] = defaultdict(list)

        if rule.properties:
            for key, values in rule.properties.items():
                extend_safe(self._properties[key], values)

    @property
    def properties(self) -> dict[str, list[Any]]:
        """
        Properties for this rule.
        :return:
        :rtype: dict
        """
        return self._properties


class Introspection(Description):
    """
    Introspection results.
    """

    def __init__(self, rebulk: Rebulk, context: dict[str, Any] | None = None) -> None:
        self.patterns = [
            PatternDescription(pattern)
            for pattern in rebulk.effective_patterns(context)
            if not pattern.private and not pattern.marker
        ]
        self.rules = [RuleDescription(rule) for rule in rebulk.effective_rules(context)]

    @property
    def properties(self) -> dict[str, list[Any]]:
        """
        Properties for Introspection results.
        :return:
        :rtype:
        """
        properties: defaultdict[str, list[Any]] = defaultdict(list)
        for pattern in self.patterns:
            for key, values in pattern.properties.items():
                extend_safe(properties[key], values)
        for rule in self.rules:
            for key, values in rule.properties.items():
                extend_safe(properties[key], values)
        return properties


def introspect(rebulk: Rebulk, context: dict[str, Any] | None = None) -> Introspection:
    """
    Introspect a Rebulk instance to grab defined objects and properties that can be generated.
    :param rebulk:
    :type rebulk: Rebulk
    :param context:
    :type context:
    :return: Introspection instance
    :rtype: Introspection
    """
    return Introspection(rebulk, context)
