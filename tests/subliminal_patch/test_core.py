from pathlib import Path

from subliminal_patch import core


def test_scan_video_movie(tmpdir):
    video_path = Path(tmpdir, "Taxi Driver 1976 Bluray 720p x264.mkv")
    video_path.touch()

    result = core.scan_video(str(video_path))
    assert isinstance(result, core.Movie)


def test_scan_video_episode(tmpdir):
    video_path = Path(tmpdir, "The Wire S01E01 Bluray 720p x264.mkv")
    video_path.touch()

    result = core.scan_video(str(video_path))
    assert isinstance(result, core.Episode)
