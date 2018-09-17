#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Introspect rebulk object to retrieve capabilities.
"""
from abc import ABCMeta, abstractproperty
from collections import defaultdict

import six
from .pattern import StringPattern, RePattern, FunctionalPattern
from .utils import extend_safe


@six.add_metaclass(ABCMeta)
class Description(object):
    """
    Abstract class for a description.
    """
    @abstractproperty
    def properties(self):  # pragma: no cover
        """
        Properties of described object.
        :return: all properties that described object can generate grouped by name.
        :rtype: dict
        """
        pass


class PatternDescription(Description):
    """
    Description of a pattern.
    """
    def __init__(self, pattern):  # pylint:disable=too-many-branches
        self.pattern = pattern
        self._properties = defaultdict(list)

        if pattern.properties:
            for key, values in pattern.properties.items():
                extend_safe(self._properties[key], values)
        elif 'value' in pattern.match_options:
            self._properties[pattern.name].append(pattern.match_options['value'])
        elif isinstance(pattern, StringPattern):
            extend_safe(self._properties[pattern.name], pattern.patterns)
        elif isinstance(pattern, RePattern):
            if pattern.name and pattern.name not in pattern.private_names:
                extend_safe(self._properties[pattern.name], [None])
            if not pattern.private_children:
                for regex_pattern in pattern.patterns:
                    for group_name, values in regex_pattern.groupindex.items():
                        if group_name not in pattern.private_names:
                            extend_safe(self._properties[group_name], [None])
        elif isinstance(pattern, FunctionalPattern):
            if pattern.name and pattern.name not in pattern.private_names:
                extend_safe(self._properties[pattern.name], [None])


    @property
    def properties(self):
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
    def __init__(self, rule):
        self.rule = rule

        self._properties = defaultdict(list)

        if rule.properties:
            for key, values in rule.properties.items():
                extend_safe(self._properties[key], values)

    @property
    def properties(self):
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
    def __init__(self, rebulk, context=None):
        self.patterns = [PatternDescription(pattern) for pattern in rebulk.effective_patterns(context)
                         if not pattern.private and not pattern.marker]
        self.rules = [RuleDescription(rule) for rule in rebulk.effective_rules(context)]

    @property
    def properties(self):
        """
        Properties for Introspection results.
        :return:
        :rtype:
        """
        properties = defaultdict(list)
        for pattern in self.patterns:
            for key, values in pattern.properties.items():
                extend_safe(properties[key], values)
        for rule in self.rules:
            for key, values in rule.properties.items():
                extend_safe(properties[key], values)
        return properties


def introspect(rebulk, context=None):
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
