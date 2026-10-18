# coding=utf-8
"""
fallback_allowed must survive the job queue round trip and reach generate_subtitles, otherwise the
Whisper fallback on Sonarr/Radarr import silently does nothing.
"""
from types import SimpleNamespace
from unittest import mock

import pytest

from subtitles.mass_download import movies, series


@pytest.mark.parametrize("module, func", [
    (series, series.episode_download_subtitles),
    (movies, movies.movies_download_subtitles),
])
@pytest.mark.parametrize("fallback_allowed", [True, False])
def test_fallback_allowed_is_queued_with_the_job(module, func, fallback_allowed, monkeypatch):
    feed = mock.MagicMock(return_value=1)
    monkeypatch.setattr(module.jobs_queue, "feed_jobs_pending_queue", feed)

    func(no=1, fallback_allowed=fallback_allowed)

    feed.assert_called_once()
    assert feed.call_args.kwargs["func"] == func.__name__
    assert feed.call_args.kwargs["kwargs"]["fallback_allowed"] is fallback_allowed


@pytest.mark.parametrize("fallback_allowed", [True, False])
def test_movies_download_subtitles_passes_fallback_allowed(fallback_allowed, monkeypatch):
    movie = SimpleNamespace(path="/movies/m.mkv", missing_subtitles_calculated=True, audio_language="English",
                            radarrId=1, sceneName=None, title="Movie", year=2026, tags="[]",
                            monitored="True", profileId=1)
    db = mock.MagicMock()
    db.execute.return_value.first.return_value = movie
    generate = mock.MagicMock(return_value=[])

    monkeypatch.setattr(movies, "database", db)
    monkeypatch.setattr(movies, "jobs_queue", mock.MagicMock())
    monkeypatch.setattr(movies, "get_subtitles", lambda **kwargs: [{"path": "/movies/m.en.srt"}])
    monkeypatch.setattr(movies, "get_audio_profile_languages", lambda _: [{"name": "English"}])
    monkeypatch.setattr(movies, "get_missing_languages", lambda *args: ["en"])
    monkeypatch.setattr(movies, "get_providers", lambda: ["whisperai"])
    monkeypatch.setattr(movies, "generate_subtitles", generate)
    monkeypatch.setattr(movies.os.path, "exists", lambda _: True)

    movies.movies_download_subtitles(no=1, job_id=1, fallback_allowed=fallback_allowed)

    generate.assert_called_once()
    assert generate.call_args.kwargs["fallback_allowed"] is fallback_allowed
