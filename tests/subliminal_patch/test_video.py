from subliminal import Episode, Movie
from subliminal_patch.video import Video


def test_video_fromguess_episode():
    video = Video.fromguess(
        "Breaking.Bad.S01E01.Bluray.mkv",
        {"type": "episode", "streaming_service": "foo", "random_key": "bar"},
    )
    assert video.streaming_service == "foo"
    assert video.other is None
    assert isinstance(video, Episode)


def test_video_fromguess_movie():
    video = Video.fromguess(
        "Taxi.Driver.1976.Bluray.mkv",
        {"type": "movie", "edition": "foo", "random_key": "bar", "other": "Proper"},
    )
    assert video.edition == "foo"
    assert video.other == "Proper"
    assert isinstance(video, Movie)


def test_video_fromname_episode():
    video = Video.fromname("Breaking.Bad.S01E01.NF.WEB-DL.1080p.x264-FOO.mkv")

    assert video.series == "Breaking Bad"
    assert video.title is None
    assert video.season == 1
    assert video.episode == 1
    assert video.source == "Web"
    assert video.streaming_service == "Netflix"
    assert video.resolution == "1080p"
    assert video.video_codec == "H.264"
    assert video.release_group == "FOO"


def test_video_fromname_movie():
    video = Video.fromname("Some.Flick.2022.UHD.Bluray.Proper.2160p.FLAC.HEVC-FOO.mkv")

    assert video.source == "Ultra HD Blu-ray"
    assert video.title == "Some Flick"
    assert video.year == 2022
    assert video.other == "Proper"
    assert video.resolution == "2160p"
    assert video.video_codec == "H.265"
    assert video.audio_codec == "FLAC"
