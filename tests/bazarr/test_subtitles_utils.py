from types import SimpleNamespace

import subtitles.utils as subtitle_utils


def test_get_video_ignores_missing_scene_name(monkeypatch):
    calls = []

    def parse_video(path, **kwargs):
        calls.append((path, kwargs))
        return SimpleNamespace(title=None)

    monkeypatch.setattr(subtitle_utils, "parse_video", parse_video)
    monkeypatch.setattr(subtitle_utils, "registered_refiners", {})
    monkeypatch.setattr(subtitle_utils.settings.general, "skip_hashing", False)

    assert subtitle_utils.get_video("/movies/movie.mkv", "Movie", None)
    assert subtitle_utils.get_video("/movies/movie.mkv", "Movie", " None ")

    assert [path for path, _ in calls] == ["/movies/movie.mkv", "/movies/movie.mkv"]


def test_get_video_refines_with_real_scene_name(monkeypatch):
    calls = []

    def parse_video(path, **kwargs):
        calls.append((path, kwargs))
        return SimpleNamespace(title=None)

    monkeypatch.setattr(subtitle_utils, "parse_video", parse_video)
    monkeypatch.setattr(subtitle_utils, "registered_refiners", {})
    monkeypatch.setattr(subtitle_utils.settings.general, "skip_hashing", False)

    subtitle_utils.get_video("/movies/movie.mkv", "Movie", " Scene.Release ")

    assert [path for path, _ in calls] == ["/movies/movie.mkv", "Scene.Release.mkv"]
    assert calls[1][1]["dry_run"] is True
