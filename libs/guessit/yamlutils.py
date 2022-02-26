#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Options
"""

from collections import OrderedDict

import babelfish
import yaml  # pylint:disable=wrong-import-order

from .rules.common.quantity import BitRate, FrameRate, Size


class OrderedDictYAMLLoader(yaml.SafeLoader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    From https://gist.github.com/enaeseth/844388
    """

    def __init__(self, *args, **kwargs):
        yaml.SafeLoader.__init__(self, *args, **kwargs)

        self.add_constructor('tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor('tag:yaml.org,2002:omap', type(self).construct_yaml_map)

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
                                                    f'expected a mapping node, but found {node.id}', node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:  # pragma: no cover
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                                                        node.start_mark, f'found unacceptable key ({exc})'
                                                        , key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


class CustomDumper(yaml.SafeDumper):
    """
    Custom YAML Dumper.
    """
    pass  # pylint:disable=unnecessary-pass


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
