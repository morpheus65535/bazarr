#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base builder class for Rebulk
"""
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from logging import getLogger

from six import add_metaclass

from .loose import set_defaults
from .pattern import RePattern, StringPattern, FunctionalPattern

log = getLogger(__name__).log


@add_metaclass(ABCMeta)
class Builder(object):
    """
    Base builder class for patterns
    """

    def __init__(self):
        self._defaults = {}
        self._regex_defaults = {}
        self._string_defaults = {}
        self._functional_defaults = {}
        self._chain_defaults = {}

    def reset(self):
        """
        Reset all defaults.

        :return:
        """
        self.__init__()

    def defaults(self, **kwargs):
        """
        Define default keyword arguments for all patterns
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(kwargs, self._defaults, override=True)
        return self

    def regex_defaults(self, **kwargs):
        """
        Define default keyword arguments for functional patterns.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(kwargs, self._regex_defaults, override=True)
        return self

    def string_defaults(self, **kwargs):
        """
        Define default keyword arguments for string patterns.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(kwargs, self._string_defaults, override=True)
        return self

    def functional_defaults(self, **kwargs):
        """
        Define default keyword arguments for functional patterns.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(kwargs, self._functional_defaults, override=True)
        return self

    def chain_defaults(self, **kwargs):
        """
        Define default keyword arguments for patterns chain.
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(kwargs, self._chain_defaults, override=True)
        return self

    def build_re(self, *pattern, **kwargs):
        """
        Builds a new regular expression pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(self._regex_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        return RePattern(*pattern, **kwargs)

    def build_string(self, *pattern, **kwargs):
        """
        Builds a new string pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(self._string_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        return StringPattern(*pattern, **kwargs)

    def build_functional(self, *pattern, **kwargs):
        """
        Builds a new functional pattern

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        set_defaults(self._functional_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        return FunctionalPattern(*pattern, **kwargs)

    def build_chain(self, **kwargs):
        """
        Builds a new patterns chain

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        from .chain import Chain
        set_defaults(self._chain_defaults, kwargs)
        set_defaults(self._defaults, kwargs)
        chain = Chain(self, **kwargs)
        chain._defaults = deepcopy(self._defaults)  # pylint: disable=protected-access
        chain._regex_defaults = deepcopy(self._regex_defaults)  # pylint: disable=protected-access
        chain._functional_defaults = deepcopy(self._functional_defaults)  # pylint: disable=protected-access
        chain._string_defaults = deepcopy(self._string_defaults)  # pylint: disable=protected-access
        chain._chain_defaults = deepcopy(self._chain_defaults)  # pylint: disable=protected-access
        return chain

    @abstractmethod
    def pattern(self, *pattern):
        """
        Register a list of Pattern instance
        :param pattern:
        :return:
        """
        pass

    def regex(self, *pattern, **kwargs):
        """
        Add re pattern

        :param pattern:
        :type pattern:
        :return: self
        :rtype: Rebulk
        """
        return self.pattern(self.build_re(*pattern, **kwargs))

    def string(self, *pattern, **kwargs):
        """
        Add string pattern

        :param pattern:
        :type pattern:
        :return: self
        :rtype: Rebulk
        """
        return self.pattern(self.build_string(*pattern, **kwargs))

    def functional(self, *pattern, **kwargs):
        """
        Add functional pattern

        :param pattern:
        :type pattern:
        :return: self
        :rtype: Rebulk
        """
        functional = self.build_functional(*pattern, **kwargs)
        return self.pattern(functional)

    def chain(self, **kwargs):
        """
        Add patterns chain, using configuration of this rebulk

        :param pattern:
        :type pattern:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        chain = self.build_chain(**kwargs)
        self.pattern(chain)
        return chain
