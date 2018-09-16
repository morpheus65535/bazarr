#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Options
"""

try:
    from collections import OrderedDict
except ImportError:  # pragma: no-cover
    from ordereddict import OrderedDict  # pylint:disable=import-error
import babelfish

import yaml

from .rules.common.quantity import BitRate, FrameRate, Size


class OrderedDictYAMLLoader(yaml.Loader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    From https://gist.github.com/enaeseth/844388
    """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:  # pragma: no cover
            raise yaml.constructor.ConstructorError(None, None,
                                                    'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:  # pragma: no cover
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                                                        node.start_mark, 'found unacceptable key (%s)'
                                                        % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


class CustomDumper(yaml.SafeDumper):
    """
    Custom YAML Dumper.
    """
    pass


def default_representer(dumper, data):
    """Default representer"""
    return dumper.represent_str(str(data))


CustomDumper.add_representer(babelfish.Language, default_representer)
CustomDumper.add_representer(babelfish.Country, default_representer)
CustomDumper.add_representer(BitRate, default_representer)
CustomDumper.add_representer(FrameRate, default_representer)
CustomDumper.add_representer(Size, default_representer)


def ordered_dict_representer(dumper, data):
    """OrderedDict representer"""
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


CustomDumper.add_representer(OrderedDict, ordered_dict_representer)
