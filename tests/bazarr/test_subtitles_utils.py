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


def _dry_run_parse_video(monkeypatch):
    """Route the real ``parse_video`` through dry-run so the tests do not need media files on disk."""
    real_parse_video = subtitle_utils.parse_video

    def parse_video(path, **kwargs):
        return real_parse_video(path, **{**kwargs, "dry_run": True})

    monkeypatch.setattr(subtitle_utils, "parse_video", parse_video)
    monkeypatch.setattr(subtitle_utils, "registered_refiners", {})
    monkeypatch.setattr(subtitle_utils.settings.general, "skip_hashing", True)


def test_get_video_episode_scene_name_overrides_path_year_and_release_group(monkeypatch):
    from subliminal_patch.providers.wizdom import WizdomSubtitle
    from subliminal_patch.score import compute_score
    from subzero.language import Language

    _dry_run_parse_video(monkeypatch)
    path = ("/tv/The Rainmaker (2025) {imdb-tt6151526}/Season 2/"
            "The Rainmaker (2025) - S02E01 - Dear Uncle Rudy [AMZN WEBDL-1080p][EAC3 5.1][h264].mkv")
    scene_name = "The.Rainmaker.S02E01.Dear.Uncle.Rudy.1080p.AMZN.WEB-DL.DD+5.1.H.264-playWEB"

    video = subtitle_utils.get_video(path, "The Rainmaker", scene_name, media_type="series")

    assert video.year == 2025
    assert video.original_series is True
    assert video.release_group == "playWEB"

    subtitle = WizdomSubtitle(Language("heb"), False, "http://example.invalid", "The Rainmaker", 2, 1,
                              "Dear Uncle Rudy", "tt6151526", "1",
                              "The.Rainmaker.S02E01.Dear.Uncle.Rudy.1080p.AMZN.WEB-DL.DD.5.1.H.264-playWEB")
    matches = subtitle.get_matches(video)
    score, _ = compute_score(matches, subtitle, video, hearing_impaired=False)
    assert score == 359


def test_get_video_movie_keeps_original_series_from_path(monkeypatch):
    _dry_run_parse_video(monkeypatch)
    path = "/movies/The Movie (2010) {imdb-tt1234567}/The.Movie.2010.1080p.BluRay-GRP.mkv"

    video = subtitle_utils.get_video(path, "The Movie", "The.Movie.1080p.BluRay-GRP", media_type="movie")

    assert not hasattr(video, "original_series")
    assert video.year == 2010


def test_sync_original_series_skips_movies_and_missing_inputs():
    from subliminal import Movie

    movie = Movie("The.Movie.2010", "The Movie", 2010)
    movie.original_series = False
    scene = SimpleNamespace(original_series=True)

    assert subtitle_utils.sync_original_series_from_scenename(movie, scene, "movie").original_series is False
    assert subtitle_utils.sync_original_series_from_scenename(None, scene, "series") is None

    episode = SimpleNamespace(original_series=False)
    subtitle_utils.sync_original_series_from_scenename(episode, SimpleNamespace(), "series")
    assert episode.original_series is False
