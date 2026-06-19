from functools import partial
from types import SimpleNamespace

import pytest
from sqlalchemy import delete
from sqlalchemy import insert


def _english_audio_languages(audio_language):
    return [{"name": "English"}]


def _malformed_audio_languages(audio_language):
    return [None, {"bad": "shape"}]


def _single_provider_list():
    return ["provider"]


def _empty_provider_list():
    return []


def _indexed_subtitles(**kwargs):
    return [{"path": "/subtitles/sub.srt", "embedded_track_id": 1}]


def _no_exclusions(media_type):
    return []


def _path_exists(path):
    return True


def _path_missing(path):
    return False


def _capture_generate_subtitles(calls, results=None):
    result_items = [] if results is None else results

    def _generate(*args, **kwargs):
        calls.append((args, kwargs))
        return iter(result_items)

    return _generate


def _capture_call(calls):
    def _record(*args, **kwargs):
        calls.append((args, kwargs))

    return _record


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


def test_movies_download_subtitles_builds_language_tuples_and_records_downloads(
    monkeypatch,
    mass_download_module,
    movie_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    movie = movie_row_factory(missing_languages=["en", "fr:forced"], profileId=44)
    generated = []
    stored = []
    history = []
    notifications = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "get_providers", _single_provider_list)
    monkeypatch.setattr(module, "store_subtitles_movie", lambda movie_id: stored.append(movie_id))
    monkeypatch.setattr(module, "history_log_movie", _capture_call(history))
    monkeypatch.setattr(module, "send_notifications_movie", _capture_call(notifications))
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(
        module,
        "generate_subtitles",
        _capture_generate_subtitles(generated, [SimpleNamespace(message="downloaded")]),
    )

    module.movies_download_subtitles(movie.radarrId, job_id="job")

    assert generated[0][0][1] == [("en", "False", "False"), ("fr", "False", "True")]
    assert stored == [movie.radarrId]
    assert len(history) == 1
    assert notifications == [((movie.radarrId, "downloaded"), {})]


def test_movies_download_subtitles_refreshes_missing_state_before_search(
    monkeypatch,
    mass_download_module,
    movie_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    movie = movie_row_factory(missing_languages=None)
    generated = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "get_providers", _single_provider_list)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(
        module,
        "list_missing_subtitles_movies",
        partial(_refresh_movie_missing_subtitles, module, movie.radarrId),
    )
    monkeypatch.setattr(module, "generate_subtitles", _capture_generate_subtitles(generated))

    module.movies_download_subtitles(movie.radarrId, job_id="job")

    assert generated[0][0][1] == [("en", "False", "False")]


def test_mass_download_uses_legacy_missing_cache_helper(mass_download_module):
    module = mass_download_module
    assert module.legacy_missing_cache_needs_rebuild(None) is True
    assert module.legacy_missing_cache_needs_rebuild("[]") is False


def test_movies_download_subtitles_reports_throttled_when_no_providers(
    monkeypatch,
    mass_download_module,
    movie_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    movie = movie_row_factory(missing_languages=["en"])
    progress = []
    names = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "get_providers", _empty_provider_list)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory(progress_updates=progress, names=names))

    module.movies_download_subtitles(movie.radarrId, job_id="job")

    assert progress[-1]["progress_message"] == "All providers throttled"
    assert names == [f"Downloaded missing subtitles for {movie.title} ({movie.year})"]


def test_movies_download_subtitles_raises_when_path_missing(
    monkeypatch,
    mass_download_module,
    movie_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    movie = movie_row_factory(missing_languages=["en"])
    progress = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_missing)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory(progress_updates=progress))

    with pytest.raises(OSError):
        module.movies_download_subtitles(movie.radarrId, job_id="job")

    assert "Movie path doesn't exists" in progress[-1]["progress_message"]


def test_series_download_subtitles_dispatches_each_episode(
    monkeypatch,
    mass_download_module,
    show_row_factory,
    episode_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    show = show_row_factory(sonarrSeriesId=5, title="Series")
    episode_one = episode_row_factory(sonarrSeriesId=show.sonarrSeriesId, sonarrEpisodeId=11, episode=1)
    episode_two = episode_row_factory(sonarrSeriesId=show.sonarrSeriesId, sonarrEpisodeId=22, episode=2)
    calls = []
    progress = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_providers", _single_provider_list)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory(progress_updates=progress))
    monkeypatch.setattr(module, "episode_download_subtitles", lambda **kwargs: calls.append(kwargs))

    module.series_download_subtitles(show.sonarrSeriesId, job_id="job")

    assert [call["no"] for call in calls] == [episode_one.sonarrEpisodeId, episode_two.sonarrEpisodeId]
    assert progress[0]["progress_max"] == 2
    assert progress[-1]["progress_message"] == "Search completed"


def test_series_download_subtitles_returns_when_series_row_is_missing(
    monkeypatch,
    mass_download_module,
    jobs_queue_factory,
):
    module = mass_download_module
    progress = []
    names = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory(progress_updates=progress, names=names))

    module.series_download_subtitles(404, job_id="job")

    assert progress[-1]["progress_message"] == "Series not found in database."
    assert names == []


@pytest.mark.parametrize("bad_value", [None, "1", "x", 1.5])
def test_series_download_subtitles_handles_noninteger_episode_numbers(
    monkeypatch,
    bad_value,
    mass_download_module,
    show_row_factory,
    episode_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    show = show_row_factory(sonarrSeriesId=5, title="Series")
    episode = episode_row_factory(
        sonarrSeriesId=show.sonarrSeriesId,
        sonarrEpisodeId=11,
        season=bad_value,
        episode=bad_value,
    )
    progress = []
    calls = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_providers", _single_provider_list)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory(progress_updates=progress))
    monkeypatch.setattr(module, "episode_download_subtitles", lambda **kwargs: calls.append(kwargs))

    module.series_download_subtitles(show.sonarrSeriesId, job_id="job")

    assert calls[0]["no"] == episode.sonarrEpisodeId
    assert any("progress_message" in update for update in progress)


def test_episode_download_subtitles_uses_missing_languages_and_records_downloads(
    monkeypatch,
    mass_download_module,
    show_row_factory,
    episode_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    show = show_row_factory(sonarrSeriesId=5, title="Series")
    episode = episode_row_factory(
        sonarrSeriesId=show.sonarrSeriesId,
        sonarrEpisodeId=11,
        missing_languages=["en", "fr:hi"],
        profileId=44,
    )
    generated = []
    stored = []
    history = []
    notifications = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "store_subtitles", lambda episode_id: stored.append(episode_id))
    monkeypatch.setattr(module, "history_log", _capture_call(history))
    monkeypatch.setattr(module, "send_notifications", _capture_call(notifications))
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(
        module,
        "generate_subtitles",
        _capture_generate_subtitles(generated, [SimpleNamespace(message="done")]),
    )

    module.episode_download_subtitles(
        episode.sonarrEpisodeId,
        job_id="job",
        job_sub_function=True,
        providers_list=["provider"],
        fallback_allowed=True,
    )

    assert generated[0][0][1] == [("en", "False", "False"), ("fr", "True", "False")]
    assert generated[0][1]["fallback_allowed"] is True
    assert stored == [episode.sonarrEpisodeId]
    assert len(history) == 1
    assert notifications == [((show.sonarrSeriesId, episode.sonarrEpisodeId, "done"), {})]


def test_episode_download_subtitles_refreshes_missing_state_before_search(
    monkeypatch,
    mass_download_module,
    show_row_factory,
    episode_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    show = show_row_factory(sonarrSeriesId=5, title="Series")
    episode = episode_row_factory(sonarrSeriesId=show.sonarrSeriesId, sonarrEpisodeId=11, missing_languages=None)
    generated = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(
        module,
        "list_missing_subtitles",
        partial(_refresh_episode_missing_subtitles, module, episode.sonarrEpisodeId),
    )
    monkeypatch.setattr(module, "generate_subtitles", _capture_generate_subtitles(generated))

    module.episode_download_subtitles(
        episode.sonarrEpisodeId,
        job_id="job",
        job_sub_function=True,
        providers_list=["provider"],
    )

    assert generated[0][0][1] == [("en", "False", "False")]


@pytest.mark.parametrize("kind", ["movies", "series"])
def test_mass_download_handles_malformed_audio_profile_languages(
    monkeypatch,
    kind,
    mass_download_module,
    movie_row_factory,
    show_row_factory,
    episode_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    generated = []

    monkeypatch.setattr(module, "get_exclusion_clause", _no_exclusions)
    monkeypatch.setattr(module, "get_subtitles", _indexed_subtitles)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _malformed_audio_languages)
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory())
    monkeypatch.setattr(module, "generate_subtitles", _capture_generate_subtitles(generated))

    if kind == "movies":
        row = movie_row_factory(missing_languages=["en"])
        monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
        monkeypatch.setattr(module, "get_providers", _single_provider_list)
        module.movies_download_subtitles(row.radarrId, job_id="job")
    else:
        show = show_row_factory(sonarrSeriesId=5)
        row = episode_row_factory(sonarrSeriesId=show.sonarrSeriesId, sonarrEpisodeId=11, missing_languages=["en"])
        monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
        module.episode_download_subtitles(
            row.sonarrEpisodeId,
            job_id="job",
            job_sub_function=True,
            providers_list=["provider"],
        )

    assert generated[0][0][2] is None


def test_episode_download_specific_subtitles_records_success(
    monkeypatch,
    mass_download_module,
    show_row_factory,
    episode_row_factory,
    jobs_queue_factory,
):
    module = mass_download_module
    show = show_row_factory(sonarrSeriesId=5, title="Series")
    episode = episode_row_factory(
        sonarrSeriesId=show.sonarrSeriesId,
        sonarrEpisodeId=11,
        season=1,
        episode=2,
        episodeTitle="Second",
    )
    stored = []
    history = []
    notifications = []
    names = []

    monkeypatch.setattr(module.path_mappings, "path_replace", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_exists)
    monkeypatch.setattr(module, "get_audio_profile_languages", _english_audio_languages)
    monkeypatch.setattr(module, "store_subtitles", lambda episode_id: stored.append(episode_id))
    monkeypatch.setattr(module, "history_log", _capture_call(history))
    monkeypatch.setattr(module, "send_notifications", _capture_call(notifications))
    monkeypatch.setattr(module, "jobs_queue", jobs_queue_factory(names=names))
    monkeypatch.setattr(
        module,
        "generate_subtitles",
        _capture_generate_subtitles([], [SimpleNamespace(message="done")]),
    )

    result = module.episode_download_specific_subtitles(
        show.sonarrSeriesId,
        episode.sonarrEpisodeId,
        "fr",
        "True",
        "False",
        job_id="job",
    )

    assert result == ("", 204)
    assert stored == [episode.sonarrEpisodeId]
    assert len(history) == 1
    assert notifications == [((show.sonarrSeriesId, episode.sonarrEpisodeId, "done"), {})]
    assert names == [
        "Searching FR:HI for Series - S01E02 - Second",
        "Searched FR:HI for Series - S01E02 - Second",
    ]


def test_movie_download_specific_subtitles_returns_not_found(monkeypatch, mass_download_module):
    module = mass_download_module

    assert module.movie_download_specific_subtitles(404, "fr", "False", "False", job_id="job") == (
        "Movie not found",
        404,
    )


def test_movie_download_specific_subtitles_returns_file_missing(
    monkeypatch,
    mass_download_module,
    movie_row_factory,
):
    module = mass_download_module
    movie = movie_row_factory()

    monkeypatch.setattr(module.path_mappings, "path_replace_movie", lambda path: path)
    monkeypatch.setattr(module.os.path, "exists", _path_missing)

    assert module.movie_download_specific_subtitles(movie.radarrId, "fr", "False", "False", job_id="job") == (
        "Movie file not found. Path mapping issue?",
        500,
    )
