from bazarr.app import config


def test_get_settings():
    assert isinstance(config.get_settings(), dict)


def test_get_scores():
    assert isinstance(config.get_scores()["movie"], dict)
    assert isinstance(config.get_scores()["episode"], dict)
