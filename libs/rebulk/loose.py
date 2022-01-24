#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Various utilities functions
"""

import sys

from inspect import isclass
try:
    from inspect import getfullargspec as getargspec

    _fullargspec_supported = True
except ImportError:
    _fullargspec_supported = False
    from inspect import getargspec

from .utils import is_iterable

if sys.version_info < (3, 4, 0):  # pragma: no cover
    def _constructor(class_):
        """
        Retrieves constructor from given class

        :param class_:
        :type class_: class
        :return: constructor from given class
        :rtype: callable
        """
        return class_.__init__
else:  # pragma: no cover
    def _constructor(class_):
        """
        Retrieves constructor from given class

        :param class_:
        :type class_: class
        :return: constructor from given class
        :rtype: callable
        """
        return class_


def call(function, *args, **kwargs):
    """
    Call a function or constructor with given args and kwargs after removing args and kwargs that doesn't match
    function or constructor signature

    :param function: Function or constructor to call
    :type function: callable
    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return: sale vakye as default function call
    :rtype: object
    """
    func = constructor_args if isclass(function) else function_args
    call_args, call_kwargs = func(function, *args, ignore_unused=True, **kwargs)  # @see #20
    return function(*call_args, **call_kwargs)


def function_args(callable_, *args, **kwargs):
    """
    Return (args, kwargs) matching the function signature

    :param callable: callable to inspect
    :type callable: callable
    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return: (args, kwargs) matching the function signature
    :rtype: tuple
    """
    argspec = getargspec(callable_)  # pylint:disable=deprecated-method
    return argspec_args(argspec, False, *args, **kwargs)


def constructor_args(class_, *args, **kwargs):
    """
    Return (args, kwargs) matching the function signature

    :param callable: callable to inspect
    :type callable: Callable
    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return: (args, kwargs) matching the function signature
    :rtype: tuple
    """
    argspec = getargspec(_constructor(class_))  # pylint:disable=deprecated-method
    return argspec_args(argspec, True, *args, **kwargs)


def argspec_args(argspec, constructor, *args, **kwargs):
    """
    Return (args, kwargs) matching the argspec object

    :param argspec: argspec to use
    :type argspec: argspec
    :param constructor: is it a constructor ?
    :type constructor: bool
    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return: (args, kwargs) matching the function signature
    :rtype: tuple
    """
    if argspec.varkw:
        call_kwarg = kwargs
    else:
        call_kwarg = dict((k, kwargs[k]) for k in kwargs if k in argspec.args) # pylint:disable=consider-using-dict-items
    if argspec.varargs:
        call_args = args
    else:
        call_args = args[:len(argspec.args) - (1 if constructor else 0)]
    return call_args, call_kwarg


if not _fullargspec_supported:
    def argspec_args_legacy(argspec, constructor, *args, **kwargs):
        """
        Return (args, kwargs) matching the argspec object

        :param argspec: argspec to use
        :type argspec: argspec
        :param constructor: is it a constructor ?
        :type constructor: bool
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return: (args, kwargs) matching the function signature
        :rtype: tuple
        """
        if argspec.keywords:
            call_kwarg = kwargs
        else:
            call_kwarg = dict((k, kwargs[k]) for k in kwargs if k in argspec.args) # pylint:disable=consider-using-dict-items
        if argspec.varargs:
            call_args = args
        else:
            call_args = args[:len(argspec.args) - (1 if constructor else 0)]
        return call_args, call_kwarg


    argspec_args = argspec_args_legacy


def ensure_list(param):
    """
    Retrieves a list from given parameter.

    :param param:
    :type param:
    :return:
    :rtype:
    """
    if not param:
        param = []
    elif not is_iterable(param):
        param = [param]
    return param


def ensure_dict(param, default_value, default_key=None):
    """
    Retrieves a dict and a default value from given parameter.

    if parameter is not a dict, it will be promoted as the default value.

    :param param:
    :type param:
    :param default_value:
    :type default_value:
    :param default_key:
    :type default_key:
    :return:
    :rtype:
    """
    if not param:
        param = default_value
    if not isinstance(param, dict):
        if param:
            default_value = param
        return {default_key: param}, default_value
    return param, default_value


def filter_index(collection, predicate=None, index=None):
    """
    Filter collection with predicate function and index.

    If index is not found, returns None.
    :param collection:
    :type collection: collection supporting iteration and slicing
    :param predicate: function to filter the collection with
    :type predicate: function
    :param index: position of a single element to retrieve
    :type index: int
    :return: filtered list, or single element of filtered list if index is defined
    :rtype: list or object
    """
    if index is None and isinstance(predicate, int):
        index = predicate
        predicate = None
    if predicate:
        collection = collection.__class__(filter(predicate, collection))
    if index is not None:
        try:
            collection = collection[index]
        except IndexError:
            collection = None
    return collection


def set_defaults(defaults, kwargs, override=False):
    """
    Set defaults from defaults dict to kwargs dict

    :param override:
    :type override:
    :param defaults:
    :type defaults:
    :param kwargs:
    :type kwargs:
    :return:
    :rtype:
    """
    if 'clear' in defaults.keys() and defaults.pop('clear'):
        kwargs.clear()
    for key, value in defaults.items():
        if key in kwargs:
            if isinstance(value, list) and isinstance(kwargs[key], list):
                kwargs[key] = list(value) + kwargs[key]
            elif isinstance(value, dict) and isinstance(kwargs[key], dict):
                set_defaults(value, kwargs[key])
        if key not in kwargs or override:
            kwargs[key] = value
