from types import SimpleNamespace

import pytest
from sqlalchemy import delete

from api.providers import providers_episodes
from api.providers import providers_movies


def _call_resource_method(method, resource):
    return method.__wrapped__(resource)


@pytest.fixture
def provider_movies(bind_wanted_database, monkeypatch):
    bind_wanted_database(providers_movies, "movies")
    monkeypatch.setattr(
        providers_movies.ProviderMovies,
        "get_request_parser",
        SimpleNamespace(parse_args=lambda: {"radarrid": 7}),
    )
    monkeypatch.setattr(providers_movies.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(providers_movies.os.path, "exists", lambda path: True)
    monkeypatch.setattr(providers_movies, "get_providers", lambda: ["provider"])
    return providers_movies


@pytest.fixture
def provider_episodes(bind_wanted_database, monkeypatch):
    bind_wanted_database(providers_episodes, "series")
    monkeypatch.setattr(
        providers_episodes.ProviderEpisodes,
        "get_request_parser",
        SimpleNamespace(parse_args=lambda: {"episodeid": 11}),
    )
    monkeypatch.setattr(providers_episodes.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(providers_episodes.os.path, "exists", lambda path: True)
    monkeypatch.setattr(providers_episodes, "get_providers", lambda: ["provider"])
    return providers_episodes


@pytest.mark.parametrize("indexed_state", ["empty", "unindexed-external"])
def test_provider_movies_get_reindexes_incomplete_subtitle_indexes(
    provider_movies, movie_row_factory, movie_subtitle_row_factory, monkeypatch, indexed_state
):
    movie_row_factory(radarrId=7)
    if indexed_state == "unindexed-external":
        movie_subtitle_row_factory(radarrId=7, path=None, embedded_track_id=None)
    store_calls = []

    monkeypatch.setattr(provider_movies, "store_subtitles_movie", store_calls.append)
    monkeypatch.setattr(provider_movies, "manual_search", lambda *args, **kwargs: [])

    result = _call_resource_method(provider_movies.ProviderMovies.get, provider_movies.ProviderMovies())

    assert store_calls == [7]
    assert result == {"data": []}


@pytest.mark.parametrize("indexed_state", ["empty", "unindexed-external"])
def test_provider_episodes_get_reindexes_incomplete_subtitle_indexes(
    provider_episodes, episode_row_factory, episode_subtitle_row_factory, monkeypatch, indexed_state
):
    episode_row_factory(sonarrEpisodeId=11)
    if indexed_state == "unindexed-external":
        episode_subtitle_row_factory(sonarrEpisodeId=11, path=None, embedded_track_id=None)
    store_calls = []

    monkeypatch.setattr(provider_episodes, "store_subtitles", store_calls.append)
    monkeypatch.setattr(provider_episodes, "manual_search", lambda *args, **kwargs: [])

    result = _call_resource_method(provider_episodes.ProviderEpisodes.get, provider_episodes.ProviderEpisodes())

    assert store_calls == [11]
    assert result == {"data": []}


def test_provider_movies_get_returns_not_found_when_row_disappears_after_reindex(
    provider_movies, movie_row_factory, wanted_search_tables, transactional_session, monkeypatch
):
    movie_row_factory(radarrId=7)

    def delete_movie(radarr_id):
        assert radarr_id == 7
        transactional_session.execute(
            delete(wanted_search_tables.movie).where(wanted_search_tables.movie.c.radarrId == radarr_id)
        )
        transactional_session.flush()

    monkeypatch.setattr(provider_movies, "store_subtitles_movie", delete_movie)

    result = _call_resource_method(provider_movies.ProviderMovies.get, provider_movies.ProviderMovies())

    assert result == ("Movie not found", 404)


def test_provider_episodes_get_returns_not_found_when_row_disappears_after_reindex(
    provider_episodes, episode_row_factory, wanted_search_tables, transactional_session, monkeypatch
):
    episode_row_factory(sonarrEpisodeId=11)

    def delete_episode(episode_id):
        assert episode_id == 11
        transactional_session.execute(
            delete(wanted_search_tables.episode).where(wanted_search_tables.episode.c.sonarrEpisodeId == episode_id)
        )
        transactional_session.flush()

    monkeypatch.setattr(provider_episodes, "store_subtitles", delete_episode)

    result = _call_resource_method(provider_episodes.ProviderEpisodes.get, provider_episodes.ProviderEpisodes())

    assert result == ("Episode not found", 404)


def test_provider_movies_get_returns_file_missing_when_path_is_none(
    provider_movies, movie_row_factory, movie_subtitle_row_factory
):
    movie_row_factory(radarrId=7, path=None)
    movie_subtitle_row_factory(radarrId=7)

    result = _call_resource_method(provider_movies.ProviderMovies.get, provider_movies.ProviderMovies())

    assert result == ("Movie file not found. Path mapping issue?", 500)


def test_provider_episodes_get_returns_file_missing_when_path_is_none(
    provider_episodes, episode_row_factory, episode_subtitle_row_factory
):
    episode_row_factory(sonarrEpisodeId=11, path=None)
    episode_subtitle_row_factory(sonarrEpisodeId=11)

    result = _call_resource_method(provider_episodes.ProviderEpisodes.get, provider_episodes.ProviderEpisodes())

    assert result == ("Episode file not found. Path mapping issue?", 500)


def test_provider_movies_post_normalizes_malformed_flags(provider_movies, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        provider_movies.ProviderMovies,
        "post_request_parser",
        SimpleNamespace(
            parse_args=lambda: {
                "radarrid": 7,
                "hi": None,
                "forced": 1,
                "original_format": "not-a-bool",
                "provider": "provider",
                "subtitle": "sub-id",
            }
        ),
    )
    monkeypatch.setattr(
        provider_movies,
        "movie_manually_download_specific_subtitle",
        lambda **kwargs: captured.update(kwargs),
    )

    result = _call_resource_method(provider_movies.ProviderMovies.post, provider_movies.ProviderMovies())

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"
    assert captured["use_original_format"] == "False"


def test_provider_episodes_post_normalizes_malformed_flags(provider_episodes, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        provider_episodes.ProviderEpisodes,
        "post_request_parser",
        SimpleNamespace(
            parse_args=lambda: {
                "seriesid": 5,
                "episodeid": 11,
                "hi": None,
                "forced": {},
                "original_format": "truthy",
                "provider": "provider",
                "subtitle": "sub-id",
            }
        ),
    )
    monkeypatch.setattr(
        provider_episodes, "episode_manually_download_specific_subtitle", lambda **kwargs: captured.update(kwargs)
    )

    result = _call_resource_method(provider_episodes.ProviderEpisodes.post, provider_episodes.ProviderEpisodes())

    assert result == ("", 204)
    assert captured["hi"] == "False"
    assert captured["forced"] == "False"
    assert captured["use_original_format"] == "False"
