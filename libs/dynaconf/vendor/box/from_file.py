#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from json import JSONDecodeError
from pathlib import Path
from typing import Union
from dynaconf.vendor.tomllib import TOMLDecodeError
from dynaconf.vendor.ruamel.yaml import YAMLError


from .exceptions import BoxError
from .box import Box
from .box_list import BoxList

__all__ = ['box_from_file']


def _to_json(data):
    try:
        return Box.from_json(data)
    except JSONDecodeError:
        raise BoxError('File is not JSON as expected')
    except BoxError:
        return BoxList.from_json(data)


def _to_yaml(data):
    try:
        return Box.from_yaml(data)
    except YAMLError:
        raise BoxError('File is not YAML as expected')
    except BoxError:
        return BoxList.from_yaml(data)


def _to_toml(data):
    try:
        return Box.from_toml(data)
    except TOMLDecodeError:
        raise BoxError('File is not TOML as expected')


def box_from_file(file: Union[str, Path], file_type: str = None,
                  encoding: str = "utf-8", errors: str = "strict") -> Union[Box, BoxList]:
    """
    Loads the provided file and tries to parse it into a Box or BoxList object as appropriate.

    :param file: Location of file
    :param encoding: File encoding
    :param errors: How to handle encoding errors
    :param file_type: manually specify file type: json, toml or yaml
    :return: Box or BoxList
    """

    if not isinstance(file, Path):
        file = Path(file)
    if not file.exists():
        raise BoxError(f'file "{file}" does not exist')
    data = file.read_text(encoding=encoding, errors=errors)
    if file_type:
        if file_type.lower() == 'json':
            return _to_json(data)
        if file_type.lower() == 'yaml':
            return _to_yaml(data)
        if file_type.lower() == 'toml':
            return _to_toml(data)
        raise BoxError(f'"{file_type}" is an unknown type, please use either toml, yaml or json')
    if file.suffix in ('.json', '.jsn'):
        return _to_json(data)
    if file.suffix in ('.yaml', '.yml'):
        return _to_yaml(data)
    if file.suffix in ('.tml', '.toml'):
        return _to_toml(data)
    raise BoxError(f'Could not determine file type based off extension, please provide file_type')
