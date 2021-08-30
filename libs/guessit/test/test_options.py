#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name, pointless-string-statement
import os

import pytest

from ..options import get_options_file_locations, merge_options, load_config_file, ConfigurationException, \
    load_config

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_config_locations():
    homedir = '/root'
    cwd = '/root/cwd'

    locations = get_options_file_locations(homedir, cwd, True)
    assert len(locations) == 9

    assert '/root/.guessit/options.json' in locations
    assert '/root/.guessit/options.yml' in locations
    assert '/root/.guessit/options.yaml' in locations
    assert '/root/.config/guessit/options.json' in locations
    assert '/root/.config/guessit/options.yml' in locations
    assert '/root/.config/guessit/options.yaml' in locations
    assert '/root/cwd/guessit.options.json' in locations
    assert '/root/cwd/guessit.options.yml' in locations
    assert '/root/cwd/guessit.options.yaml' in locations


def test_merge_configurations():
    c1 = {'param1': True, 'param2': True, 'param3': False}
    c2 = {'param1': False, 'param2': True, 'param3': False}
    c3 = {'param1': False, 'param2': True, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert not merged['param1']
    assert merged['param2']
    assert not merged['param3']

    merged = merge_options(c3, c2, c1)
    assert merged['param1']
    assert merged['param2']
    assert not merged['param3']


def test_merge_configurations_lists():
    c1 = {'param1': [1], 'param2': True, 'param3': False}
    c2 = {'param1': [2], 'param2': True, 'param3': False}
    c3 = {'param1': [3], 'param2': True, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert merged['param1'] == [1, 2, 3]
    assert merged['param2']
    assert not merged['param3']

    merged = merge_options(c3, c2, c1)
    assert merged['param1'] == [3, 2, 1]
    assert merged['param2']
    assert not merged['param3']


def test_merge_configurations_deep():
    c1 = {'param1': [1], 'param2': {'d1': [1]}, 'param3': False}
    c2 = {'param1': [2], 'param2': {'d1': [2]}, 'param3': False}
    c3 = {'param1': [3], 'param2': {'d3': [3]}, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert merged['param1'] == [1, 2, 3]
    assert merged['param2']['d1'] == [1, 2]
    assert merged['param2']['d3'] == [3]
    assert 'd2' not in merged['param2']
    assert not merged['param3']

    merged = merge_options(c3, c2, c1)
    assert merged['param1'] == [3, 2, 1]
    assert merged['param2']
    assert merged['param2']['d1'] == [2, 1]
    assert 'd2' not in merged['param2']
    assert merged['param2']['d3'] == [3]
    assert not merged['param3']


def test_merge_configurations_pristine_all():
    c1 = {'param1': [1], 'param2': True, 'param3': False}
    c2 = {'param1': [2], 'param2': True, 'param3': False, 'pristine': True}
    c3 = {'param1': [3], 'param2': True, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert merged['param1'] == [2, 3]
    assert merged['param2']
    assert not merged['param3']

    merged = merge_options(c3, c2, c1)
    assert merged['param1'] == [2, 1]
    assert merged['param2']
    assert not merged['param3']


def test_merge_configurations_pristine_properties():
    c1 = {'param1': [1], 'param2': False, 'param3': True}
    c2 = {'param1': [2], 'param2': True, 'param3': False, 'pristine': ['param2', 'param3']}
    c3 = {'param1': [3], 'param2': True, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert merged['param1'] == [1, 2, 3]
    assert merged['param2']
    assert not merged['param3']


def test_merge_configurations_pristine_properties_deep():
    c1 = {'param1': [1], 'param2': {'d1': False}, 'param3': True}
    c2 = {'param1': [2], 'param2': {'d1': True}, 'param3': False, 'pristine': ['param2', 'param3']}
    c3 = {'param1': [3], 'param2': {'d1': True}, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert merged['param1'] == [1, 2, 3]
    assert merged['param2']
    assert not merged['param3']


def test_merge_configurations_pristine_properties2():
    c1 = {'param1': [1], 'param2': False, 'param3': True}
    c2 = {'param1': [2], 'param2': True, 'param3': False, 'pristine': ['param1', 'param2', 'param3']}
    c3 = {'param1': [3], 'param2': True, 'param3': False}

    merged = merge_options(c1, c2, c3)
    assert merged['param1'] == [2, 3]
    assert merged['param2']
    assert not merged['param3']


def test_load_config_file():
    json_config = load_config_file(os.path.join(__location__, 'config', 'test.json'))
    yml_config = load_config_file(os.path.join(__location__, 'config', 'test.yml'))
    yaml_config = load_config_file(os.path.join(__location__, 'config', 'test.yaml'))

    assert json_config['expected_title'] == ['The 100', 'OSS 117']
    assert yml_config['expected_title'] == ['The 100', 'OSS 117']
    assert yaml_config['expected_title'] == ['The 100', 'OSS 117']

    assert json_config['yaml'] is False
    assert yml_config['yaml'] is True
    assert yaml_config['yaml'] is True

    with pytest.raises(ConfigurationException) as excinfo:
        load_config_file(os.path.join(__location__, 'config', 'dummy.txt'))

    assert excinfo.match('Configuration file extension is not supported for ".*?dummy.txt" file\\.')


def test_load_config():
    config = load_config({'no_default_config': True, 'param1': 'test',
                          'config': [os.path.join(__location__, 'config', 'test.yml')]})

    assert not config.get('param1')

    assert config.get('advanced_config')  # advanced_config is still loaded from default
    assert config['expected_title'] == ['The 100', 'OSS 117']
    assert config['yaml'] is True

    config = load_config({'no_default_config': True, 'param1': 'test'})

    assert not config.get('param1')

    assert 'expected_title' not in config
    assert 'yaml' not in config

    config = load_config({'no_default_config': True, 'param1': 'test', 'config': ['false']})

    assert not config.get('param1')

    assert 'expected_title' not in config
    assert 'yaml' not in config
