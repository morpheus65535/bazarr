#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright (c) 2017-2020 - Chris Griffith - MIT License
"""
Improved dictionary access through dot notation with additional tools.
"""
import copy
import re
import string
import warnings
from collections.abc import Iterable, Mapping, Callable
from keyword import kwlist
from pathlib import Path
from typing import Any, Union, Tuple, List, Dict

from dynaconf.vendor import box
from .converters import (_to_json, _from_json, _from_toml, _to_toml, _from_yaml, _to_yaml, BOX_PARAMETERS)
from .exceptions import BoxError, BoxKeyError, BoxTypeError, BoxValueError, BoxWarning

__all__ = ['Box']

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')
_list_pos_re = re.compile(r'\[(\d+)\]')

# a sentinel object for indicating no default, in order to allow users
# to pass `None` as a valid default value
NO_DEFAULT = object()


def _camel_killer(attr):
    """
    CamelKiller, qu'est-ce que c'est?

    Taken from http://stackoverflow.com/a/1176023/3244542
    """
    attr = str(attr)

    s1 = _first_cap_re.sub(r'\1_\2', attr)
    s2 = _all_cap_re.sub(r'\1_\2', s1)
    return re.sub(' *_+', '_', s2.lower())


def _recursive_tuples(iterable, box_class, recreate_tuples=False, **kwargs):
    out_list = []
    for i in iterable:
        if isinstance(i, dict):
            out_list.append(box_class(i, **kwargs))
        elif isinstance(i, list) or (recreate_tuples and isinstance(i, tuple)):
            out_list.append(_recursive_tuples(i, box_class, recreate_tuples, **kwargs))
        else:
            out_list.append(i)
    return tuple(out_list)


def _parse_box_dots(item):
    for idx, char in enumerate(item):
        if char == '[':
            return item[:idx], item[idx:]
        elif char == '.':
            return item[:idx], item[idx + 1:]
    raise BoxError('Could not split box dots properly')


def _get_box_config():
    return {
        # Internal use only
        '__created': False,
        '__safe_keys': {}
    }


class Box(dict):
    """
    Improved dictionary access through dot notation with additional tools.

    :param default_box: Similar to defaultdict, return a default value
    :param default_box_attr: Specify the default replacement.
        WARNING: If this is not the default 'Box', it will not be recursive
    :param default_box_none_transform: When using default_box, treat keys with none values as absent. True by default
    :param frozen_box: After creation, the box cannot be modified
    :param camel_killer_box: Convert CamelCase to snake_case
    :param conversion_box: Check for near matching keys as attributes
    :param modify_tuples_box: Recreate incoming tuples with dicts into Boxes
    :param box_safe_prefix: Conversion box prefix for unsafe attributes
    :param box_duplicates: "ignore", "error" or "warn" when duplicates exists in a conversion_box
    :param box_intact_types: tuple of types to ignore converting
    :param box_recast: cast certain keys to a specified type
    :param box_dots: access nested Boxes by period separated keys in string
    """

    _protected_keys = [
        "to_dict",
        "to_json",
        "to_yaml",
        "from_yaml",
        "from_json",
        "from_toml",
        "to_toml",
        "merge_update",
    ] + [attr for attr in dir({}) if not attr.startswith("_")]

    def __new__(cls, *args: Any,  box_settings: Any = None, default_box: bool = False, default_box_attr: Any = NO_DEFAULT,
                default_box_none_transform: bool = True, frozen_box: bool = False, camel_killer_box: bool = False,
                conversion_box: bool = True, modify_tuples_box: bool = False, box_safe_prefix: str = 'x',
                box_duplicates: str = 'ignore', box_intact_types: Union[Tuple, List] = (),
                box_recast: Dict = None, box_dots: bool = False, **kwargs: Any):
        """
        Due to the way pickling works in python 3, we need to make sure
        the box config is created as early as possible.
        """
        obj = super(Box, cls).__new__(cls, *args, **kwargs)
        obj._box_config = _get_box_config()
        obj._box_config.update({
            'default_box': default_box,
            'default_box_attr': cls.__class__ if default_box_attr is NO_DEFAULT else default_box_attr,
            'default_box_none_transform': default_box_none_transform,
            'conversion_box': conversion_box,
            'box_safe_prefix': box_safe_prefix,
            'frozen_box': frozen_box,
            'camel_killer_box': camel_killer_box,
            'modify_tuples_box': modify_tuples_box,
            'box_duplicates': box_duplicates,
            'box_intact_types': tuple(box_intact_types),
            'box_recast': box_recast,
            'box_dots': box_dots,
            'box_settings': box_settings or {}
        })
        return obj

    def __init__(self, *args: Any, box_settings: Any = None, default_box: bool = False, default_box_attr: Any = NO_DEFAULT,
                 default_box_none_transform: bool = True, frozen_box: bool = False, camel_killer_box: bool = False,
                 conversion_box: bool = True, modify_tuples_box: bool = False, box_safe_prefix: str = 'x',
                 box_duplicates: str = 'ignore', box_intact_types: Union[Tuple, List] = (),
                 box_recast: Dict = None, box_dots: bool = False, **kwargs: Any):
        super().__init__()
        self._box_config = _get_box_config()
        self._box_config.update({
            'default_box': default_box,
            'default_box_attr': self.__class__ if default_box_attr is NO_DEFAULT else default_box_attr,
            'default_box_none_transform': default_box_none_transform,
            'conversion_box': conversion_box,
            'box_safe_prefix': box_safe_prefix,
            'frozen_box': frozen_box,
            'camel_killer_box': camel_killer_box,
            'modify_tuples_box': modify_tuples_box,
            'box_duplicates': box_duplicates,
            'box_intact_types': tuple(box_intact_types),
            'box_recast': box_recast,
            'box_dots': box_dots,
            'box_settings': box_settings or {}
        })
        if not self._box_config['conversion_box'] and self._box_config['box_duplicates'] != 'ignore':
            raise BoxError('box_duplicates are only for conversion_boxes')
        if len(args) == 1:
            if isinstance(args[0], str):
                raise BoxValueError('Cannot extrapolate Box from string')
            if isinstance(args[0], Mapping):
                for k, v in args[0].items():
                    if v is args[0]:
                        v = self

                    if v is None and self._box_config['default_box'] and self._box_config['default_box_none_transform']:
                        continue
                    self.__setitem__(k, v)
            elif isinstance(args[0], Iterable):
                for k, v in args[0]:
                    self.__setitem__(k, v)
            else:
                raise BoxValueError('First argument must be mapping or iterable')
        elif args:
            raise BoxTypeError(f'Box expected at most 1 argument, got {len(args)}')

        for k, v in kwargs.items():
            if args and isinstance(args[0], Mapping) and v is args[0]:
                v = self
            self.__setitem__(k, v)

        self._box_config['__created'] = True

    def __add__(self, other: dict):
        new_box = self.copy()
        if not isinstance(other, dict):
            raise BoxTypeError(f'Box can only merge two boxes or a box and a dictionary.')
        new_box.merge_update(other)
        return new_box

    def __hash__(self):
        if self._box_config['frozen_box']:
            hashing = 54321
            for item in self.items():
                hashing ^= hash(item)
            return hashing
        raise BoxTypeError('unhashable type: "Box"')

    def __dir__(self):
        allowed = string.ascii_letters + string.digits + '_'
        items = set(super().__dir__())
        # Only show items accessible by dot notation
        for key in self.keys():
            key = str(key)
            if ' ' not in key and key[0] not in string.digits and key not in kwlist:
                for letter in key:
                    if letter not in allowed:
                        break
                else:
                    items.add(key)

        for key in self.keys():
            if key not in items:
                if self._box_config['conversion_box']:
                    key = self._safe_attr(key)
                    if key:
                        items.add(key)

        return list(items)

    def get(self, key, default=NO_DEFAULT):
        if key not in self:
            if default is NO_DEFAULT:
                if self._box_config['default_box'] and self._box_config['default_box_none_transform']:
                    return self.__get_default(key)
                else:
                    return None
            if isinstance(default, dict) and not isinstance(default, Box):
                return Box(default, box_settings=self._box_config.get("box_settings"))
            if isinstance(default, list) and not isinstance(default, box.BoxList):
                return box.BoxList(default)
            return default
        return self[key]

    def copy(self):
        return Box(super().copy(), **self.__box_config())

    def __copy__(self):
        return Box(super().copy(), **self.__box_config())

    def __deepcopy__(self, memodict=None):
        frozen = self._box_config['frozen_box']
        config = self.__box_config()
        config['frozen_box'] = False
        out = self.__class__(**config)
        memodict = memodict or {}
        memodict[id(self)] = out
        for k, v in self.items():
            out[copy.deepcopy(k, memodict)] = copy.deepcopy(v, memodict)
        out._box_config['frozen_box'] = frozen
        return out

    def __setstate__(self, state):
        self._box_config = state['_box_config']
        self.__dict__.update(state)

    def keys(self):
        return super().keys()

    def values(self):
        return [self[x] for x in self.keys()]

    def items(self):
        return [(x, self[x]) for x in self.keys()]

    def __get_default(self, item):
        default_value = self._box_config['default_box_attr']
        if default_value in (self.__class__, dict):
            value = self.__class__(**self.__box_config())
        elif isinstance(default_value, dict):
            value = self.__class__(**self.__box_config(), **default_value)
        elif isinstance(default_value, list):
            value = box.BoxList(**self.__box_config())
        elif isinstance(default_value, Callable):
            value = default_value()
        elif hasattr(default_value, 'copy'):
            value = default_value.copy()
        else:
            value = default_value
        self.__convert_and_store(item, value)
        return value

    def __box_config(self):
        out = {}
        for k, v in self._box_config.copy().items():
            if not k.startswith('__'):
                out[k] = v
        return out

    def __recast(self, item, value):
        if self._box_config['box_recast'] and item in self._box_config['box_recast']:
            try:
                return self._box_config['box_recast'][item](value)
            except ValueError:
                raise BoxValueError(f'Cannot convert {value} to {self._box_config["box_recast"][item]}') from None
        return value

    def __convert_and_store(self, item, value):
        if self._box_config['conversion_box']:
            safe_key = self._safe_attr(item)
            self._box_config['__safe_keys'][safe_key] = item
        if isinstance(value, (int, float, str, bytes, bytearray, bool, complex, set, frozenset)):
            return super().__setitem__(item, value)
        # If the value has already been converted or should not be converted, return it as-is
        if self._box_config['box_intact_types'] and isinstance(value, self._box_config['box_intact_types']):
            return super().__setitem__(item, value)
        # This is the magic sauce that makes sub dictionaries into new box objects
        if isinstance(value, dict) and not isinstance(value, Box):
            value = self.__class__(value, **self.__box_config())
        elif isinstance(value, list) and not isinstance(value, box.BoxList):
            if self._box_config['frozen_box']:
                value = _recursive_tuples(value,
                                          self.__class__,
                                          recreate_tuples=self._box_config['modify_tuples_box'],
                                          **self.__box_config())
            else:
                value = box.BoxList(value, box_class=self.__class__, **self.__box_config())
        elif self._box_config['modify_tuples_box'] and isinstance(value, tuple):
            value = _recursive_tuples(value, self.__class__, recreate_tuples=True, **self.__box_config())
        super().__setitem__(item, value)

    def __getitem__(self, item, _ignore_default=False):
        try:
            return super().__getitem__(item)
        except KeyError as err:
            if item == '_box_config':
                raise BoxKeyError('_box_config should only exist as an attribute and is never defaulted') from None
            if self._box_config['box_dots'] and isinstance(item, str) and ('.' in item or '[' in item):
                first_item, children = _parse_box_dots(item)
                if first_item in self.keys():
                    if hasattr(self[first_item], '__getitem__'):
                        return self[first_item][children]
            if self._box_config['camel_killer_box'] and isinstance(item, str):
                converted = _camel_killer(item)
                if converted in self.keys():
                    return super().__getitem__(converted)
            if self._box_config['default_box'] and not _ignore_default:
                return self.__get_default(item)
            raise BoxKeyError(str(err)) from None

    def __getattr__(self, item):
        try:
            try:
                value = self.__getitem__(item, _ignore_default=True)
            except KeyError:
                value = object.__getattribute__(self, item)
        except AttributeError as err:
            if item == '__getstate__':
                raise BoxKeyError(item) from None
            if item == '_box_config':
                raise BoxError('_box_config key must exist') from None
            if self._box_config['conversion_box']:
                safe_key = self._safe_attr(item)
                if safe_key in self._box_config['__safe_keys']:
                    return self.__getitem__(self._box_config['__safe_keys'][safe_key])
            if self._box_config['default_box']:
                return self.__get_default(item)
            raise BoxKeyError(str(err)) from None
        return value

    def __setitem__(self, key, value):
        if key != '_box_config' and self._box_config['__created'] and self._box_config['frozen_box']:
            raise BoxError('Box is frozen')
        if self._box_config['box_dots'] and isinstance(key, str) and '.' in key:
            first_item, children = _parse_box_dots(key)
            if first_item in self.keys():
                if hasattr(self[first_item], '__setitem__'):
                    return self[first_item].__setitem__(children, value)
        value = self.__recast(key, value)
        if key not in self.keys() and self._box_config['camel_killer_box']:
            if self._box_config['camel_killer_box'] and isinstance(key, str):
                key = _camel_killer(key)
        if self._box_config['conversion_box'] and self._box_config['box_duplicates'] != 'ignore':
            self._conversion_checks(key)
        self.__convert_and_store(key, value)

    def __setattr__(self, key, value):
        if key != '_box_config' and self._box_config['frozen_box'] and self._box_config['__created']:
            raise BoxError('Box is frozen')
        if key in self._protected_keys:
            raise BoxKeyError(f'Key name "{key}" is protected')
        if key == '_box_config':
            return object.__setattr__(self, key, value)
        value = self.__recast(key, value)
        safe_key = self._safe_attr(key)
        if safe_key in self._box_config['__safe_keys']:
            key = self._box_config['__safe_keys'][safe_key]
        self.__setitem__(key, value)

    def __delitem__(self, key):
        if self._box_config['frozen_box']:
            raise BoxError('Box is frozen')
        if key not in self.keys() and self._box_config['box_dots'] and isinstance(key, str) and '.' in key:
            first_item, children = key.split('.', 1)
            if first_item in self.keys() and isinstance(self[first_item], dict):
                return self[first_item].__delitem__(children)
        if key not in self.keys() and self._box_config['camel_killer_box']:
            if self._box_config['camel_killer_box'] and isinstance(key, str):
                for each_key in self:
                    if _camel_killer(key) == each_key:
                        key = each_key
                        break
        super().__delitem__(key)

    def __delattr__(self, item):
        if self._box_config['frozen_box']:
            raise BoxError('Box is frozen')
        if item == '_box_config':
            raise BoxError('"_box_config" is protected')
        if item in self._protected_keys:
            raise BoxKeyError(f'Key name "{item}" is protected')
        try:
            self.__delitem__(item)
        except KeyError as err:
            if self._box_config['conversion_box']:
                safe_key = self._safe_attr(item)
                if safe_key in self._box_config['__safe_keys']:
                    self.__delitem__(self._box_config['__safe_keys'][safe_key])
                    del self._box_config['__safe_keys'][safe_key]
                    return
            raise BoxKeyError(err)

    def pop(self, key, *args):
        if args:
            if len(args) != 1:
                raise BoxError('pop() takes only one optional argument "default"')
            try:
                item = self[key]
            except KeyError:
                return args[0]
            else:
                del self[key]
                return item
        try:
            item = self[key]
        except KeyError:
            raise BoxKeyError('{0}'.format(key)) from None
        else:
            del self[key]
            return item

    def clear(self):
        super().clear()
        self._box_config['__safe_keys'].clear()

    def popitem(self):
        try:
            key = next(self.__iter__())
        except StopIteration:
            raise BoxKeyError('Empty box') from None
        return key, self.pop(key)

    def __repr__(self):
        return f'<Box: {self.to_dict()}>'

    def __str__(self):
        return str(self.to_dict())

    def __iter__(self):
        for key in self.keys():
            yield key

    def __reversed__(self):
        for key in reversed(list(self.keys())):
            yield key

    def to_dict(self):
        """
        Turn the Box and sub Boxes back into a native python dictionary.

        :return: python dictionary of this Box
        """
        out_dict = dict(self)
        for k, v in out_dict.items():
            if v is self:
                out_dict[k] = out_dict
            elif isinstance(v, Box):
                out_dict[k] = v.to_dict()
            elif isinstance(v, box.BoxList):
                out_dict[k] = v.to_list()
        return out_dict

    def update(self, __m=None, **kwargs):
        if __m:
            if hasattr(__m, 'keys'):
                for k in __m:
                    self.__convert_and_store(k, __m[k])
            else:
                for k, v in __m:
                    self.__convert_and_store(k, v)
        for k in kwargs:
            self.__convert_and_store(k, kwargs[k])

    def merge_update(self, __m=None, **kwargs):
        def convert_and_set(k, v):
            intact_type = (self._box_config['box_intact_types'] and isinstance(v, self._box_config['box_intact_types']))
            if isinstance(v, dict) and not intact_type:
                # Box objects must be created in case they are already
                # in the `converted` box_config set
                v = self.__class__(v, **self.__box_config())
                if k in self and isinstance(self[k], dict):
                    if isinstance(self[k], Box):
                        self[k].merge_update(v)
                    else:
                        self[k].update(v)
                    return
            if isinstance(v, list) and not intact_type:
                v = box.BoxList(v, **self.__box_config())
            self.__setitem__(k, v)

        if __m:
            if hasattr(__m, 'keys'):
                for key in __m:
                    convert_and_set(key, __m[key])
            else:
                for key, value in __m:
                    convert_and_set(key, value)
        for key in kwargs:
            convert_and_set(key, kwargs[key])

    def setdefault(self, item, default=None):
        if item in self:
            return self[item]

        if isinstance(default, dict):
            default = self.__class__(default, **self.__box_config())
        if isinstance(default, list):
            default = box.BoxList(default, box_class=self.__class__, **self.__box_config())
        self[item] = default
        return default

    def _safe_attr(self, attr):
        """Convert a key into something that is accessible as an attribute"""
        allowed = string.ascii_letters + string.digits + '_'

        if isinstance(attr, tuple):
            attr = "_".join([str(x) for x in attr])

        attr = attr.decode('utf-8', 'ignore') if isinstance(attr, bytes) else str(attr)
        if self.__box_config()['camel_killer_box']:
            attr = _camel_killer(attr)

        out = []
        last_safe = 0
        for i, character in enumerate(attr):
            if character in allowed:
                last_safe = i
                out.append(character)
            elif not out:
                continue
            else:
                if last_safe == i - 1:
                    out.append('_')

        out = "".join(out)[:last_safe + 1]

        try:
            int(out[0])
        except (ValueError, IndexError):
            pass
        else:
            out = f'{self.__box_config()["box_safe_prefix"]}{out}'

        if out in kwlist:
            out = f'{self.__box_config()["box_safe_prefix"]}{out}'

        return out

    def _conversion_checks(self, item):
        """
        Internal use for checking if a duplicate safe attribute already exists

        :param item: Item to see if a dup exists
        :param keys: Keys to check against
        """
        safe_item = self._safe_attr(item)

        if safe_item in self._box_config['__safe_keys']:
            dups = [f'{item}({safe_item})', f'{self._box_config["__safe_keys"][safe_item]}({safe_item})']
            if self._box_config['box_duplicates'].startswith('warn'):
                warnings.warn(f'Duplicate conversion attributes exist: {dups}', BoxWarning)
            else:
                raise BoxError(f'Duplicate conversion attributes exist: {dups}')

    def to_json(self, filename: Union[str, Path] = None, encoding: str = 'utf-8', errors: str = 'strict',
                **json_kwargs):
        """
        Transform the Box object into a JSON string.

        :param filename: If provided will save to file
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param json_kwargs: additional arguments to pass to json.dump(s)
        :return: string of JSON (if no filename provided)
        """
        return _to_json(self.to_dict(), filename=filename, encoding=encoding, errors=errors, **json_kwargs)

    @classmethod
    def from_json(cls, json_string: str = None, filename: Union[str, Path] = None, encoding: str = 'utf-8',
                  errors: str = 'strict', **kwargs):
        """
        Transform a json object string into a Box object. If the incoming
        json is a list, you must use BoxList.from_json.

        :param json_string: string to pass to `json.loads`
        :param filename: filename to open and pass to `json.load`
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param kwargs: parameters to pass to `Box()` or `json.loads`
        :return: Box object from json data
        """
        box_args = {}
        for arg in kwargs.copy():
            if arg in BOX_PARAMETERS:
                box_args[arg] = kwargs.pop(arg)

        data = _from_json(json_string, filename=filename, encoding=encoding, errors=errors, **kwargs)

        if not isinstance(data, dict):
            raise BoxError(f'json data not returned as a dictionary, but rather a {type(data).__name__}')
        return cls(data, **box_args)

    def to_yaml(self, filename: Union[str, Path] = None, default_flow_style: bool = False, encoding: str = 'utf-8',
                errors: str = 'strict', **yaml_kwargs):
        """
        Transform the Box object into a YAML string.

        :param filename:  If provided will save to file
        :param default_flow_style: False will recursively dump dicts
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param yaml_kwargs: additional arguments to pass to yaml.dump
        :return: string of YAML (if no filename provided)
        """
        return _to_yaml(self.to_dict(), filename=filename, default_flow_style=default_flow_style,
                        encoding=encoding, errors=errors, **yaml_kwargs)

    @classmethod
    def from_yaml(cls, yaml_string: str = None, filename: Union[str, Path] = None, encoding: str = 'utf-8',
                  errors: str = 'strict', **kwargs):
        """
        Transform a yaml object string into a Box object. By default will use SafeLoader.

        :param yaml_string: string to pass to `yaml.load`
        :param filename: filename to open and pass to `yaml.load`
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param kwargs: parameters to pass to `Box()` or `yaml.load`
        :return: Box object from yaml data
        """
        box_args = {}
        for arg in kwargs.copy():
            if arg in BOX_PARAMETERS:
                box_args[arg] = kwargs.pop(arg)

        data = _from_yaml(yaml_string=yaml_string, filename=filename, encoding=encoding, errors=errors, **kwargs)
        if not isinstance(data, dict):
            raise BoxError(f'yaml data not returned as a dictionary but rather a {type(data).__name__}')
        return cls(data, **box_args)

    def to_toml(self, filename: Union[str, Path] = None, encoding: str = 'utf-8', errors: str = 'strict'):
        """
        Transform the Box object into a toml string.

        :param filename: File to write toml object too
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :return: string of TOML (if no filename provided)
        """
        return _to_toml(self.to_dict(), filename=filename, encoding=encoding, errors=errors)

    @classmethod
    def from_toml(cls, toml_string: str = None, filename: Union[str, Path] = None,
                  encoding: str = 'utf-8', errors: str = 'strict', **kwargs):
        """
        Transforms a toml string or file into a Box object

        :param toml_string: string to pass to `toml.load`
        :param filename: filename to open and pass to `toml.load`
        :param encoding: File encoding
        :param errors: How to handle encoding errors
        :param kwargs: parameters to pass to `Box()`
        :return:
        """
        box_args = {}
        for arg in kwargs.copy():
            if arg in BOX_PARAMETERS:
                box_args[arg] = kwargs.pop(arg)

        data = _from_toml(toml_string=toml_string, filename=filename, encoding=encoding, errors=errors)
        return cls(data, **box_args)
