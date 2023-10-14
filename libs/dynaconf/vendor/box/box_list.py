#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright (c) 2017-2020 - Chris Griffith - MIT License
import copy
import re
from typing import Iterable, Optional


from dynaconf.vendor import box
from .converters import (_to_yaml, _from_yaml, _to_json, _from_json,
                         _to_toml, _from_toml, _to_csv, _from_csv, BOX_PARAMETERS)
from .exceptions import BoxError, BoxTypeError, BoxKeyError

_list_pos_re = re.compile(r'\[(\d+)\]')


DYNABOX_CLASS = None  # a cache constant to avoid multiple imports


def get_dynabox_class_avoiding_circular_import():
    """
    See dynaconf issue #462
    """
    global DYNABOX_CLASS
    if DYNABOX_CLASS is None:
        from dynaconf.utils.boxing import DynaBox
        DYNABOX_CLASS = DynaBox
    return DYNABOX_CLASS


class BoxList(list):
    """
    Drop in replacement of list, that converts added objects to Box or BoxList
    objects as necessary.
    """

    def __init__(self, iterable: Iterable = None, box_class : Optional[box.Box] = None, **box_options):
        self.box_class = box_class or get_dynabox_class_avoiding_circular_import()
        self.box_options = box_options
        self.box_org_ref = self.box_org_ref = id(iterable) if iterable else 0
        if iterable:
            for x in iterable:
                self.append(x)
        if box_options.get('frozen_box'):
            def frozen(*args, **kwargs):
                raise BoxError('BoxList is frozen')

            for method in ['append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'sort']:
                self.__setattr__(method, frozen)

    def __getitem__(self, item):
        if self.box_options.get('box_dots') and isinstance(item, str) and item.startswith('['):
            list_pos = _list_pos_re.search(item)
            value = super(BoxList, self).__getitem__(int(list_pos.groups()[0]))
            if len(list_pos.group()) == len(item):
                return value
            return value.__getitem__(item[len(list_pos.group()):].lstrip('.'))
        return super(BoxList, self).__getitem__(item)

    def __delitem__(self, key):
        if self.box_options.get('frozen_box'):
            raise BoxError('BoxList is frozen')
        super(BoxList, self).__delitem__(key)

    def __setitem__(self, key, value):
        if self.box_options.get('frozen_box'):
            raise BoxError('BoxList is frozen')
        if self.box_options.get('box_dots') and isinstance(key, str) and key.startswith('['):
            list_pos = _list_pos_re.search(key)
            pos = int(list_pos.groups()[0])
            if len(list_pos.group()) == len(key):
                return super(BoxList, self).__setitem__(pos, value)
            return super(BoxList, self).__getitem__(pos).__setitem__(key[len(list_pos.group()):].lstrip('.'), value)
        super(BoxList, self).__setitem__(key, value)

    def _is_intact_type(self, obj):
        try:
            if self.box_options.get('box_intact_types') and isinstance(obj, self.box_options['box_intact_types']):
                return True
        except AttributeError as err:
            if 'box_options' in self.__dict__:
                raise BoxKeyError(err)
        return False

    def append(self, p_object):
        if isinstance(p_object, dict) and not self._is_intact_type(p_object):
            try:
                p_object = self.box_class(p_object, **self.box_options)
            except AttributeError as err:
                if 'box_class' in self.__dict__:
                    raise BoxKeyError(err)
        elif isinstance(p_object, list) and not self._is_intact_type(p_object):
            try:
                p_object = (self if id(p_object) == self.box_org_ref else BoxList(p_object, **self.box_options))
            except AttributeError as err:
                if 'box_org_ref' in self.__dict__:
                    raise BoxKeyError(err)
        super(BoxList, self).append(p_object)

    def extend(self, iterable):
        for item in iterable:
            self.append(item)

    def insert(self, index, p_object):
        if isinstance(p_object, dict) and not self._is_intact_type(p_object):
            p_object = self.box_class(p_object, **self.box_options)
        elif isinstance(p_object, list) and not self._is_intact_type(p_object):
            p_object = (self if id(p_object) == self.box_org_ref else BoxList(p_object))
        super(BoxList, self).insert(index, p_object)

    def __repr__(self):
        return f'<BoxList: {self.to_list()}>'

    def __str__(self):
        return str(self.to_list())

    def __copy__(self):
        return BoxList((x for x in self), self.box_class, **self.box_options)

    def __deepcopy__(self, memo=None):
        out = self.__class__()
        memo = memo or {}
        memo[id(self)] = out
        for k in self:
            out.append(copy.deepcopy(k, memo=memo))
        return out

    def __hash__(self):
        if self.box_options.get('frozen_box'):
            hashing = 98765
            hashing ^= hash(tuple(self))
            return hashing
        raise BoxTypeError("unhashable type: 'BoxList'")

    def to_list(self):
        new_list = []
        for x in self:
            if x is self:
                new_list.append(new_list)
            elif isinstance(x, box.Box):
                new_list.append(x.to_dict())
            elif isinstance(x, BoxList):
                new_list.append(x.to_list())
            else:
                new_list.append(x)
        return new_list

    def to_json(self, filename: str = None, encoding: str = 'utf-8', errors: str = 'strict',
                multiline: bool = False, **json_kwargs):
        """
        Transform the BoxList object into a JSON string.

        :param filename: If provided will save to file
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param multiline: Put each item in list onto it's own line
        :param json_kwargs: additional arguments to pass to json.dump(s)
        :return: string of JSON or return of `json.dump`
        """
        if filename and multiline:
            lines = [_to_json(item, filename=False, encoding=encoding, errors=errors, **json_kwargs) for item in self]
            with open(filename, 'w', encoding=encoding, errors=errors) as f:
                f.write("\n".join(lines))
        else:
            return _to_json(self.to_list(), filename=filename, encoding=encoding, errors=errors, **json_kwargs)

    @classmethod
    def from_json(cls, json_string: str = None, filename: str = None, encoding: str = 'utf-8', errors: str = 'strict',
                  multiline: bool = False, **kwargs):
        """
        Transform a json object string into a BoxList object. If the incoming
        json is a dict, you must use Box.from_json.

        :param json_string: string to pass to `json.loads`
        :param filename: filename to open and pass to `json.load`
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param multiline: One object per line
        :param kwargs: parameters to pass to `Box()` or `json.loads`
        :return: BoxList object from json data
        """
        bx_args = {}
        for arg in list(kwargs.keys()):
            if arg in BOX_PARAMETERS:
                bx_args[arg] = kwargs.pop(arg)

        data = _from_json(json_string, filename=filename, encoding=encoding,
                          errors=errors, multiline=multiline, **kwargs)

        if not isinstance(data, list):
            raise BoxError(f'json data not returned as a list, but rather a {type(data).__name__}')
        return cls(data, **bx_args)

    def to_yaml(self, filename: str = None, default_flow_style: bool = False,
                encoding: str = 'utf-8', errors: str = 'strict', **yaml_kwargs):
        """
        Transform the BoxList object into a YAML string.

        :param filename:  If provided will save to file
        :param default_flow_style: False will recursively dump dicts
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param yaml_kwargs: additional arguments to pass to yaml.dump
        :return: string of YAML or return of `yaml.dump`
        """
        return _to_yaml(self.to_list(), filename=filename, default_flow_style=default_flow_style,
                        encoding=encoding, errors=errors, **yaml_kwargs)

    @classmethod
    def from_yaml(cls, yaml_string: str = None, filename: str = None,
                  encoding: str = 'utf-8', errors: str = 'strict', **kwargs):
        """
        Transform a yaml object string into a BoxList object.

        :param yaml_string: string to pass to `yaml.load`
        :param filename: filename to open and pass to `yaml.load`
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param kwargs: parameters to pass to `BoxList()` or `yaml.load`
        :return: BoxList object from yaml data
        """
        bx_args = {}
        for arg in list(kwargs.keys()):
            if arg in BOX_PARAMETERS:
                bx_args[arg] = kwargs.pop(arg)

        data = _from_yaml(yaml_string=yaml_string, filename=filename, encoding=encoding, errors=errors, **kwargs)
        if not isinstance(data, list):
            raise BoxError(f'yaml data not returned as a list but rather a {type(data).__name__}')
        return cls(data, **bx_args)

    def to_toml(self, filename: str = None, key_name: str = 'toml', encoding: str = 'utf-8', errors: str = 'strict'):
        """
        Transform the BoxList object into a toml string.

        :param filename: File to write toml object too
        :param key_name: Specify the name of the key to store the string under
            (cannot directly convert to toml)
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :return: string of TOML (if no filename provided)
        """
        return _to_toml({key_name: self.to_list()}, filename=filename, encoding=encoding, errors=errors)

    @classmethod
    def from_toml(cls, toml_string: str = None, filename: str = None, key_name: str = 'toml',
                  encoding: str = 'utf-8', errors: str = 'strict', **kwargs):
        """
        Transforms a toml string or file into a BoxList object

        :param toml_string: string to pass to `toml.load`
        :param filename: filename to open and pass to `toml.load`
        :param key_name: Specify the name of the key to pull the list from
            (cannot directly convert from toml)
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param kwargs: parameters to pass to `Box()`
        :return:
        """
        bx_args = {}
        for arg in list(kwargs.keys()):
            if arg in BOX_PARAMETERS:
                bx_args[arg] = kwargs.pop(arg)

        data = _from_toml(toml_string=toml_string, filename=filename, encoding=encoding, errors=errors)
        if key_name not in data:
            raise BoxError(f'{key_name} was not found.')
        return cls(data[key_name], **bx_args)

    def to_csv(self, filename, encoding: str = 'utf-8', errors: str = 'strict'):
        _to_csv(self, filename=filename, encoding=encoding, errors=errors)

    @classmethod
    def from_csv(cls, filename, encoding: str = 'utf-8', errors: str = 'strict'):
        return cls(_from_csv(filename=filename, encoding=encoding, errors=errors))
