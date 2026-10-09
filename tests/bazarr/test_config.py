from bazarr.app import config


def test_get_settings():
    assert isinstance(config.get_settings(), dict)
