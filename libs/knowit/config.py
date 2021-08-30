# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple
from logging import NullHandler, getLogger

from pkg_resources import resource_stream
from six import text_type
import yaml

from .serializer import get_yaml_loader

logger = getLogger(__name__)
logger.addHandler(NullHandler())

_valid_aliases = ('code', 'default', 'human', 'technical')
_Value = namedtuple('_Value', _valid_aliases)


class Config(object):
    """Application config class."""

    @classmethod
    def build(cls, path=None):
        """Build config instance."""
        loader = get_yaml_loader()
        with resource_stream('knowit', 'defaults.yml') as stream:
            cfgs = [yaml.load(stream, Loader=loader)]

        if path:
            with open(path, 'r') as stream:
                cfgs.append(yaml.load(stream, Loader=loader))

        profiles_data = {}
        for cfg in cfgs:
            if 'profiles' in cfg:
                profiles_data.update(cfg['profiles'])

        knowledge_data = {}
        for cfg in cfgs:
            if 'knowledge' in cfg:
                knowledge_data.update(cfg['knowledge'])

        data = {'general': {}}
        for class_name, data_map in knowledge_data.items():
            data.setdefault(class_name, {})
            for code, detection_values in data_map.items():
                alias_map = (profiles_data.get(class_name) or {}).get(code) or {}
                alias_map.setdefault('code', code)
                alias_map.setdefault('default', alias_map['code'])
                alias_map.setdefault('human', alias_map['default'])
                alias_map.setdefault('technical', alias_map['human'])
                value = _Value(**{k: v for k, v in alias_map.items() if k in _valid_aliases})
                for detection_value in detection_values:
                    data[class_name][text_type(detection_value)] = value

        config = Config()
        config.__dict__ = data
        return config
