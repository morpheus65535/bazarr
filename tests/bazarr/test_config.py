from bazarr.app import config


def test_get_settings():
    assert isinstance(config.get_settings(), dict)


def test_sportarr_tag_filter_accepts_the_labels_returned_by_sportarr():
    assert config.validate_sportarr_tags(['No Subs', 'UFC'])


def test_sportarr_tag_filter_rejects_empty_or_padded_labels():
    assert not config.validate_sportarr_tags([''])
    assert not config.validate_sportarr_tags([' UFC '])
    assert not config.validate_sportarr_tags([None])


def test_sportarr_base_url_is_normalized_when_saved(monkeypatch):
    from sportarr import sse_client

    old_base_url = config.settings.sportarr.base_url
    monkeypatch.setattr(config.settings.general, 'use_sportarr', False)
    monkeypatch.setattr(config, 'write_config', lambda: None)
    monkeypatch.setattr(sse_client.sportarr_sse_client, 'restart', lambda: None)

    try:
        config.save_settings([('settings-sportarr-base_url', ['//sportarr'])])
        assert config.settings.sportarr.base_url == '/sportarr'
    finally:
        config.settings.sportarr.base_url = old_base_url
