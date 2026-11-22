from types import SimpleNamespace

import pytest

from api.episodes import episodes_subtitles
from api.movies import movies_subtitles


def _call_resource_method(method, resource):
    return method.__wrapped__(resource)


@pytest.fixture
def movies_api_module():
    return movies_subtitles


@pytest.fixture
def episodes_api_module():
    return episodes_subtitles


def test_movies_subtitles_patch_normalizes_malformed_flags(movies_api_module, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        movies_api_module.MoviesSubtitles,
        "patch_request_parser",
        SimpleNamespace(parse_args=lambda: {"radarrid": 7, "language": "en", "hi": None, "forced": {}}),
    )
    monkeypatch.setattr(
        movies_api_module,
        "movie_download_specific_subtitles",
        lambda **kwargs: captured.update(kwargs),
    )

    result = _call_resource_method(movies_api_module.MoviesSubtitles.patch, movies_api_module.MoviesSubtitles())

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"


def test_episodes_subtitles_patch_normalizes_malformed_flags(episodes_api_module, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        episodes_api_module.EpisodesSubtitles,
        "patch_request_parser",
        SimpleNamespace(
            parse_args=lambda: {"seriesid": 5, "episodeid": 11, "language": "fr", "hi": None, "forced": 123}
        ),
    )
    monkeypatch.setattr(
        episodes_api_module, "episode_download_specific_subtitles", lambda **kwargs: captured.update(kwargs)
    )

    result = _call_resource_method(episodes_api_module.EpisodesSubtitles.patch, episodes_api_module.EpisodesSubtitles())

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"
