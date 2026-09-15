from bazarr.subtitles.manual import _build_release_info


class FakeSubtitle:
    def __init__(self, release_info=None, extra_release_info=None):
        self.release_info = release_info
        if extra_release_info is not None:
            self.extra_release_info = extra_release_info


def test_build_release_info_plain():
    subtitle = FakeSubtitle(release_info="Movie.en.srt")
    assert _build_release_info(subtitle) == ["Movie.en.srt"]


def test_build_release_info_multiple_comma_separated():
    subtitle = FakeSubtitle(release_info="Movie.en.srt,Some.Other.Release")
    assert _build_release_info(subtitle) == ["Movie.en.srt", "Some.Other.Release"]


def test_build_release_info_with_extra_release_info():
    subtitle = FakeSubtitle(
        release_info="Movie.en.srt", extra_release_info=["Duration: 1:42:18"]
    )
    assert _build_release_info(subtitle) == ["Movie.en.srt", "Duration: 1:42:18"]


def test_build_release_info_without_extra_release_info():
    subtitle = FakeSubtitle(release_info="Movie.en.srt")
    assert not hasattr(subtitle, "extra_release_info")
    assert _build_release_info(subtitle) == ["Movie.en.srt"]


def test_build_release_info_none():
    subtitle = FakeSubtitle(release_info=None)
    assert _build_release_info(subtitle) == []
