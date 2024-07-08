import os
import typing
from logging import NullHandler, getLogger

import yaml

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files  # type: ignore[assignment,no-redef,import-not-found]

from knowit.serializer import get_yaml_loader

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class _Value(typing.NamedTuple):
    code: str
    default: str
    human: str
    technical: str


_valid_aliases = _Value._fields


class Config:
    """Application config class."""

    @classmethod
    def build(cls, path: typing.Optional[typing.Union[str, os.PathLike]] = None) -> 'Config':
        """Build config instance."""
        loader = get_yaml_loader()
        config_file = files(__package__).joinpath('defaults.yml')
        with config_file.open('rb') as stream:
            cfgs = [yaml.load(stream, Loader=loader)]

        if path:
            with open(path, 'rb') as stream:
                cfgs.append(yaml.load(stream, Loader=loader))

        profiles_data = {}
        for cfg in cfgs:
            if 'profiles' in cfg:
                profiles_data.update(cfg['profiles'])

        knowledge_data = {}
        for cfg in cfgs:
            if 'knowledge' in cfg:
                knowledge_data.update(cfg['knowledge'])

        data: typing.Dict[str, typing.MutableMapping] = {'general': {}}
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
                    data[class_name][str(detection_value)] = value

        config = Config()
        config.__dict__ = data
        return config
