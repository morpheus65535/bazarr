# -*- coding: utf-8 -*-
from types import SimpleNamespace

from bazarr.app import config


def test_rename_enabled_providers_replaces_renamed_key_in_place():
    result = config.rename_enabled_providers(['opensubtitles', 'animetosho_xyz', 'subdl'],
                                             {'animetosho_xyz': 'animetosho_net'})

    assert result == ['opensubtitles', 'animetosho_net', 'subdl']


def test_rename_enabled_providers_keeps_new_name_once_when_both_present():
    result = config.rename_enabled_providers(['animetosho_xyz', 'animetosho_net'],
                                             {'animetosho_xyz': 'animetosho_net'})

    assert result == ['animetosho_net']


def test_rename_enabled_providers_returns_copy_when_nothing_renamed():
    original = ['opensubtitles', 'subdl']

    result = config.rename_enabled_providers(original, {'animetosho_xyz': 'animetosho_net'})

    assert result == original
    assert result is not original


def test_rename_enabled_providers_empty_list():
    assert config.rename_enabled_providers([], config.RENAMED_PROVIDERS) == []


def test_renamed_providers_maps_animetosho_xyz_to_net():
    assert config.RENAMED_PROVIDERS['animetosho_xyz'] == 'animetosho_net'


def test_migrate_renamed_providers_updates_settings_and_writes(monkeypatch):
    fake_settings = SimpleNamespace(general=SimpleNamespace(enabled_providers=['animetosho_xyz', 'subdl']))
    writes = []
    monkeypatch.setattr(config, 'settings', fake_settings)
    monkeypatch.setattr(config, 'write_config', lambda: writes.append(True))

    config.migrate_renamed_providers()

    assert fake_settings.general.enabled_providers == ['animetosho_net', 'subdl']
    assert writes == [True]


def test_migrate_renamed_providers_does_not_write_when_unchanged(monkeypatch):
    fake_settings = SimpleNamespace(general=SimpleNamespace(enabled_providers=['opensubtitles', 'subdl']))
    writes = []
    monkeypatch.setattr(config, 'settings', fake_settings)
    monkeypatch.setattr(config, 'write_config', lambda: writes.append(True))

    config.migrate_renamed_providers()

    assert fake_settings.general.enabled_providers == ['opensubtitles', 'subdl']
    assert writes == []


def test_migrate_renamed_providers_ignores_non_list(monkeypatch):
    fake_settings = SimpleNamespace(general=SimpleNamespace(enabled_providers='animetosho_xyz'))
    writes = []
    monkeypatch.setattr(config, 'settings', fake_settings)
    monkeypatch.setattr(config, 'write_config', lambda: writes.append(True))

    config.migrate_renamed_providers()

    assert fake_settings.general.enabled_providers == 'animetosho_xyz'
    assert writes == []
