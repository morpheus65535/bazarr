from functools import partial
from unittest.mock import Mock

from sqlalchemy import delete
from sqlalchemy import insert


def _single_provider_list():
    return ["provider"]


def _empty_provider_list():
    return []


def _capture_generate_subtitles(calls, *args, **kwargs):
    calls.append((args, kwargs))
    return iter(())


def _generated_languages(generate_subtitles):
    return generate_subtitles.call_args.args[1]


def _captured_languages(generate_calls):
    return generate_calls[0][0][1]


def _record_provider_call(calls):
    calls.append(True)
    return ["provider"]


def _refresh_movie_missing_subtitles(module, movie_id, **kwargs):
    module.database.execute(
        delete(module.TableMissingSubtitles)
        .where(module.TableMissingSubtitles.media_type == "movie")
        .where(module.TableMissingSubtitles.media_id == movie_id)
    )
    module.database.execute(
        insert(module.TableMissingSubtitles),
        [{"media_type": "movie", "media_id": movie_id, "language": "en"}],
    )


def _refresh_episode_missing_subtitles(module, episode_id, **kwargs):
    module.database.execute(
        delete(module.TableMissingSubtitles)
        .where(module.TableMissingSubtitles.media_type == "series")
        .where(module.TableMissingSubtitles.media_id == episode_id)
    )
    module.database.execute(
        insert(module.TableMissingSubtitles),
        [{"media_type": "series", "media_id": episode_id, "language": "en"}],
    )


def _invalidate_movie_row_after_missing_refresh(module, movie_id, **kwargs):
    module.database.execute(
        module.update(module.TableMovies)
        .values(radarrId=-1)
        .where(module.TableMovies.radarrId == movie_id)
    )


def test_wanted_movie_refreshes_missing_state_before_search(
    monkeypatch, wanted_module, movie_row_factory, movie_subtitle_row_factory
):
    movie = movie_row_factory(missing_languages=None, failed_attempts=[])
    movie_subtitle_row_factory(radarrId=movie.radarrId)
    captured_languages = []

    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(
        wanted_module,
        "list_missing_subtitles_movies",
        partial(_refresh_movie_missing_subtitles, wanted_module, movie.radarrId),
    )
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, captured_languages))

    wanted_module.wanted_download_subtitles_movie(movie.radarrId, job_id="job")

    assert _captured_languages(captured_languages) == [("en", "False", "False")]


def test_wanted_episode_refreshes_missing_state_before_search(
    monkeypatch, wanted_module, show_row_factory, episode_row_factory, episode_subtitle_row_factory
):
    show_row_factory(sonarrSeriesId=3, title="Series")
    episode = episode_row_factory(missing_languages=None, failed_attempts=[])
    episode_subtitle_row_factory(sonarrEpisodeId=episode.sonarrEpisodeId)
    captured_languages = []

    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(
        wanted_module,
        "list_missing_subtitles",
        partial(_refresh_episode_missing_subtitles, wanted_module, episode.sonarrEpisodeId),
    )
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, captured_languages))

    wanted_module.wanted_download_subtitles(episode.sonarrEpisodeId, job_id="job")

    assert _captured_languages(captured_languages) == [("en", "False", "False")]


def test_movie_download_wrapper_does_not_refresh_details_after_success(
    monkeypatch, wanted_module, movie_row_factory, movie_subtitle_row_factory
):
    movie = movie_row_factory(missing_languages=["en"], failed_attempts=[])
    movie_subtitle_row_factory(radarrId=movie.radarrId)
    store_subtitles_movie = Mock()
    list_missing_subtitles_movies = Mock(return_value=None)
    generated_calls = []

    monkeypatch.setattr(wanted_module, "store_subtitles_movie", store_subtitles_movie)
    monkeypatch.setattr(wanted_module, "list_missing_subtitles_movies", list_missing_subtitles_movies)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generated_calls))

    wanted_module.wanted_download_subtitles_movie(movie.radarrId, job_id="job")

    assert store_subtitles_movie.call_count == 0
    assert list_missing_subtitles_movies.call_count == 0
    assert _captured_languages(generated_calls) == [("en", "False", "False")]


def test_series_download_wrapper_does_not_refresh_details_after_success(
    monkeypatch, wanted_module, show_row_factory, episode_row_factory, episode_subtitle_row_factory
):
    show_row_factory(sonarrSeriesId=3, title="Series")
    episode = episode_row_factory(missing_languages=["en"], failed_attempts=[])
    episode_subtitle_row_factory(sonarrEpisodeId=episode.sonarrEpisodeId)
    store_subtitles = Mock()
    list_missing_subtitles = Mock(return_value=None)
    generated_calls = []

    monkeypatch.setattr(wanted_module, "store_subtitles", store_subtitles)
    monkeypatch.setattr(wanted_module, "list_missing_subtitles", list_missing_subtitles)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", partial(_capture_generate_subtitles, generated_calls))

    wanted_module.wanted_download_subtitles(episode.sonarrEpisodeId, job_id="job")

    assert store_subtitles.call_count == 0
    assert list_missing_subtitles.call_count == 0
    assert _captured_languages(generated_calls) == [("en", "False", "False")]


def test_wanted_download_subtitles_movie_returns_early_when_movie_not_found(monkeypatch, wanted_module):
    providers_calls = []

    monkeypatch.setattr(wanted_module, "get_providers", partial(_record_provider_call, providers_calls))

    result = wanted_module.wanted_download_subtitles_movie(9999, job_id="job")

    assert result is None
    assert not providers_calls


def test_wanted_download_subtitles_returns_early_when_episode_not_found(monkeypatch, wanted_module):
    providers_calls = []

    monkeypatch.setattr(wanted_module, "get_providers", partial(_record_provider_call, providers_calls))

    result = wanted_module.wanted_download_subtitles(9999, job_id="job")

    assert result is None
    assert not providers_calls


def test_wanted_download_subtitles_movie_skips_search_when_no_providers(
    monkeypatch, wanted_module, movie_row_factory, movie_subtitle_row_factory
):
    movie = movie_row_factory(missing_languages=["en"])
    movie_subtitle_row_factory(radarrId=movie.radarrId)
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(wanted_module, "get_providers", _empty_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", generate_subtitles)

    wanted_module.wanted_download_subtitles_movie(movie.radarrId, job_id="job")

    assert generate_subtitles.call_count == 0


def test_wanted_download_subtitles_skips_search_when_no_providers(
    monkeypatch, wanted_module, show_row_factory, episode_row_factory, episode_subtitle_row_factory
):
    show_row_factory(sonarrSeriesId=3, title="Series")
    episode = episode_row_factory(missing_languages=["en"])
    episode_subtitle_row_factory(sonarrEpisodeId=episode.sonarrEpisodeId)
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(wanted_module, "get_providers", _empty_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", generate_subtitles)

    wanted_module.wanted_download_subtitles(episode.sonarrEpisodeId, job_id="job")

    assert generate_subtitles.call_count == 0


def test_wanted_download_subtitles_movie_refreshes_empty_index_list(monkeypatch, wanted_module, movie_row_factory):
    movie = movie_row_factory(missing_languages=["en"], failed_attempts=[])
    store_subtitles_movie = Mock()
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(wanted_module, "store_subtitles_movie", store_subtitles_movie)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", generate_subtitles)

    wanted_module.wanted_download_subtitles_movie(movie.radarrId, job_id="job")

    assert store_subtitles_movie.call_args.args[0] == movie.radarrId
    assert _generated_languages(generate_subtitles) == [("en", "False", "False")]


def test_wanted_download_subtitles_refreshes_empty_index_list(monkeypatch, wanted_module, show_row_factory, episode_row_factory):
    show_row_factory(sonarrSeriesId=3, title="Series")
    episode = episode_row_factory(missing_languages=["en"], failed_attempts=[])
    store_subtitles = Mock()
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(wanted_module, "store_subtitles", store_subtitles)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", generate_subtitles)

    wanted_module.wanted_download_subtitles(episode.sonarrEpisodeId, job_id="job")

    assert store_subtitles.call_args.args[0] == episode.sonarrEpisodeId
    assert _generated_languages(generate_subtitles) == [("en", "False", "False")]


def test_wanted_download_subtitles_movie_refreshes_unindexed_external_subtitle(
    monkeypatch, wanted_module, movie_row_factory, movie_subtitle_row_factory
):
    movie = movie_row_factory(missing_languages=["en"], failed_attempts=[])
    movie_subtitle_row_factory(radarrId=movie.radarrId, path=None, embedded_track_id=None)
    store_subtitles_movie = Mock()
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(wanted_module, "store_subtitles_movie", store_subtitles_movie)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", generate_subtitles)

    wanted_module.wanted_download_subtitles_movie(movie.radarrId, job_id="job")

    assert store_subtitles_movie.call_args.args[0] == movie.radarrId
    assert _generated_languages(generate_subtitles) == [("en", "False", "False")]


def test_wanted_download_subtitles_refreshes_unindexed_external_subtitle(
    monkeypatch, wanted_module, show_row_factory, episode_row_factory, episode_subtitle_row_factory
):
    show_row_factory(sonarrSeriesId=3, title="Series")
    episode = episode_row_factory(missing_languages=["en"], failed_attempts=[])
    episode_subtitle_row_factory(sonarrEpisodeId=episode.sonarrEpisodeId, path=None, embedded_track_id=None)
    store_subtitles = Mock()
    generate_subtitles = Mock(return_value=iter(()))

    monkeypatch.setattr(wanted_module, "store_subtitles", store_subtitles)
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)
    monkeypatch.setattr(wanted_module, "generate_subtitles", generate_subtitles)

    wanted_module.wanted_download_subtitles(episode.sonarrEpisodeId, job_id="job")

    assert store_subtitles.call_args.args[0] == episode.sonarrEpisodeId
    assert _generated_languages(generate_subtitles) == [("en", "False", "False")]


def test_wanted_movie_wrapper_handles_missing_row_after_missing_refresh(
    monkeypatch, wanted_module, movie_row_factory, movie_subtitle_row_factory
):
    movie = movie_row_factory(missing_languages=None)
    movie_subtitle_row_factory(radarrId=movie.radarrId)

    monkeypatch.setattr(
        wanted_module,
        "list_missing_subtitles_movies",
        partial(_invalidate_movie_row_after_missing_refresh, wanted_module, movie.radarrId),
    )
    monkeypatch.setattr(wanted_module, "get_providers", _single_provider_list)

    result = wanted_module.wanted_download_subtitles_movie(movie.radarrId, job_id="job")
    assert result is None
