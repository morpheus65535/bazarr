#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abstract rule class definition and rule engine implementation
"""
from abc import ABCMeta, abstractmethod
import inspect
from itertools import groupby
from logging import getLogger

from .utils import is_iterable

from .toposort import toposort

from . import debug

log = getLogger(__name__).log


class Consequence(metaclass=ABCMeta):
    """
    Definition of a consequence to apply.
    """
    @abstractmethod
    def then(self, matches, when_response, context):  # pragma: no cover
        """
        Action implementation.

        :param matches:
        :type matches: rebulk.match.Matches
        :param context:
        :type context:
        :param when_response: return object from when call.
        :type when_response: object
        :return: True if the action was runned, False if it wasn't.
        :rtype: bool
        """
        pass


class Condition(metaclass=ABCMeta):
    """
    Definition of a condition to check.
    """
    @abstractmethod
    def when(self, matches, context):  # pragma: no cover
        """
        Condition implementation.

        :param matches:
        :type matches: rebulk.match.Matches
        :param context:
        :type context:
        :return: truthy if rule should be triggered and execute then action, falsy if it should not.
        :rtype: object
        """
        pass


class CustomRule(Condition, Consequence, metaclass=ABCMeta):
    """
    Definition of a rule to apply
    """
    # pylint: disable=no-self-use, unused-argument, abstract-method
    priority = 0
    name = None
    dependency = None
    properties = {}

    def __init__(self, log_level=None):
        self.defined_at = debug.defined_at()
        if log_level is None and not hasattr(self, 'log_level'):
            self.log_level = debug.LOG_LEVEL

    def enabled(self, context):
        """
        Disable rule.

        :param context:
        :type context:
        :return: True if rule is enabled, False if disabled
        :rtype: bool
        """
        return True

    def __lt__(self, other):
        return self.priority > other.priority

    def __repr__(self):
        defined = ""
        if self.defined_at:
            defined = f"@{self.defined_at}"
        return f"<{self.name if self.name else self.__class__.__name__}{defined}>"

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class Rule(CustomRule):
    """
    Definition of a rule to apply
    """
    # pylint:disable=abstract-method
    consequence = None

    def then(self, matches, when_response, context):
        assert self.consequence
        if is_iterable(self.consequence):
            if not is_iterable(when_response):
                when_response = [when_response]
            iterator = iter(when_response)
            for cons in self.consequence:  #pylint: disable=not-an-iterable
                if inspect.isclass(cons):
                    cons = cons()
                cons.then(matches, next(iterator), context)
        else:
            cons = self.consequence
            if inspect.isclass(cons):
                cons = cons()  # pylint:disable=not-callable
            cons.then(matches, when_response, context)


class RemoveMatch(Consequence):  # pylint: disable=abstract-method
    """
    Remove matches returned by then
    """
    def then(self, matches, when_response, context):
        if is_iterable(when_response):
            ret = []
            when_response = list(when_response)
            for match in when_response:
                if match in matches:
                    matches.remove(match)
                    ret.append(match)
            return ret
        if when_response in matches:
            matches.remove(when_response)
            return when_response


class AppendMatch(Consequence):  # pylint: disable=abstract-method
    """
    Append matches returned by then
    """
    def __init__(self, match_name=None):
        self.match_name = match_name

    def then(self, matches, when_response, context):
        if is_iterable(when_response):
            ret = []
            when_response = list(when_response)
            for match in when_response:
                if match not in matches:
                    if self.match_name:
                        match.name = self.match_name
                    matches.append(match)
                    ret.append(match)
            return ret
        if self.match_name:
            when_response.name = self.match_name
        if when_response not in matches:
            matches.append(when_response)
            return when_response


class RenameMatch(Consequence):  # pylint: disable=abstract-method
    """
    Rename matches returned by then
    """
    def __init__(self, match_name):
        self.match_name = match_name
        self.remove = RemoveMatch()
        self.append = AppendMatch()

    def then(self, matches, when_response, context):
        removed = self.remove.then(matches, when_response, context)
        if is_iterable(removed):
            removed = list(removed)
            for match in removed:
                match.name = self.match_name
        elif removed:
            removed.name = self.match_name
        if removed:
            self.append.then(matches, removed, context)


class AppendTags(Consequence):  # pylint: disable=abstract-method
    """
    Add tags to returned matches
    """
    def __init__(self, tags):
        self.tags = tags
        self.remove = RemoveMatch()
        self.append = AppendMatch()

    def then(self, matches, when_response, context):
        removed = self.remove.then(matches, when_response, context)
        if is_iterable(removed):
            removed = list(removed)
            for match in removed:
                match.tags.extend(self.tags)
        elif removed:
            removed.tags.extend(self.tags)  # pylint: disable=no-member
        if removed:
            self.append.then(matches, removed, context)


class RemoveTags(Consequence):  # pylint: disable=abstract-method
    """
    Remove tags from returned matches
    """
    def __init__(self, tags):
        self.tags = tags
        self.remove = RemoveMatch()
        self.append = AppendMatch()

    def then(self, matches, when_response, context):
        removed = self.remove.then(matches, when_response, context)
        if is_iterable(removed):
            removed = list(removed)
            for match in removed:
                for tag in self.tags:
                    if tag in match.tags:
                        match.tags.remove(tag)
        elif removed:
            for tag in self.tags:
                if tag in removed.tags:  # pylint: disable=no-member
                    removed.tags.remove(tag)  # pylint: disable=no-member
        if removed:
            self.append.then(matches, removed, context)


class Rules(list):
    """
    list of rules ready to execute.
    """

    def __init__(self, *rules):
        super().__init__()
        self.load(*rules)

    def load(self, *rules):
        """
        Load rules from a Rule module, class or instance

        :param rules:
        :type rules:
        :return:
        :rtype:
        """
        for rule in rules:
            if inspect.ismodule(rule):
                self.load_module(rule)
            elif inspect.isclass(rule):
                self.load_class(rule)
            else:
                self.append(rule)

    def load_module(self, module):
        """
        Load a rules module

        :param module:
        :type module:
        :return:
        :rtype:
        """
        # pylint: disable=unused-variable
        for name, obj in inspect.getmembers(module,
                                            lambda member: hasattr(member, '__module__')
                                            and member.__module__ == module.__name__
                                            and inspect.isclass):
            self.load_class(obj)

    def load_class(self, class_):
        """
        Load a Rule class.

        :param class_:
        :type class_:
        :return:
        :rtype:
        """
        self.append(class_())

    def execute_all_rules(self, matches, context):
        """
        Execute all rules from this rules list. All when condition with same priority will be performed before
        calling then actions.

        :param matches:
        :type matches:
        :param context:
        :type context:
        :return:
        :rtype:
        """
        ret = []
        for priority, priority_rules in groupby(sorted(self), lambda rule: rule.priority):
            sorted_rules = toposort_rules(list(priority_rules))  # Group by dependency graph toposort
            for rules_group in sorted_rules:
                rules_group = list(sorted(rules_group, key=self.index))  # Sort rules group based on initial ordering.
                group_log_level = None
                for rule in rules_group:
                    if group_log_level is None or group_log_level < rule.log_level:
                        group_log_level = rule.log_level
                log(group_log_level, "%s independent rule(s) at priority %s.", len(rules_group), priority)
                for rule in rules_group:
                    when_response = execute_rule(rule, matches, context)
                    if when_response is not None:
                        ret.append((rule, when_response))

        return ret


def execute_rule(rule, matches, context):
    """
    Execute the given rule.
    :param rule:
    :type rule:
    :param matches:
    :type matches:
    :param context:
    :type context:
    :return:
    :rtype:
    """
    if rule.enabled(context):
        log(rule.log_level, "Checking rule condition: %s", rule)
        when_response = rule.when(matches, context)
        if when_response:
            log(rule.log_level, "Rule was triggered: %s", when_response)
            log(rule.log_level, "Running rule consequence: %s %s", rule, when_response)
            rule.then(matches, when_response, context)
            return when_response
    else:
        log(rule.log_level, "Rule is disabled: %s", rule)

def toposort_rules(rules):
    """
    Sort given rules using toposort with dependency parameter.
    :param rules:
    :type rules:
    :return:
    :rtype:
    """
    graph = {}
    class_dict = {}
    for rule in rules:
        if rule.__class__ in class_dict:
            raise ValueError(f"Duplicate class rules are not allowed: {rule.__class__}")
        class_dict[rule.__class__] = rule
    for rule in rules:
        if not is_iterable(rule.dependency) and rule.dependency:
            rule_dependencies = [rule.dependency]
        else:
            rule_dependencies = rule.dependency
        dependencies = set()
        if rule_dependencies:
            for dependency in rule_dependencies:
                if inspect.isclass(dependency):
                    dependency = class_dict.get(dependency)
                if dependency:
                    dependencies.add(dependency)
        graph[rule] = dependencies
    return toposort(graph)
