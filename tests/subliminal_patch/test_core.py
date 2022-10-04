from pathlib import Path

import pytest

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


@pytest.fixture
def pool_instance():
    yield core.SZProviderPool({"argenteam"}, {})


def test_pool_update_w_nothing(pool_instance):
    pool_instance.update({}, {}, [], {})
    assert pool_instance.providers == set()
    assert pool_instance.discarded_providers == set()


def test_pool_update_w_multiple_providers(pool_instance):
    assert pool_instance.providers == {"argenteam"}
    pool_instance.update({"argenteam", "subdivx", "subf2m"}, {}, [], {})
    assert pool_instance.providers == {"argenteam", "subdivx", "subf2m"}


def test_pool_update_discarded_providers(pool_instance):
    assert pool_instance.providers == {"argenteam"}

    # Provider was discarded internally
    pool_instance.discarded_providers = {"argenteam"}

    assert pool_instance.discarded_providers == {"argenteam"}

    # Provider is set to be used again
    pool_instance.update({"subdivx", "argenteam"}, {}, [], {})

    assert pool_instance.providers == {"argenteam", "subdivx"}

    # Provider should disappear from discarded providers
    assert pool_instance.discarded_providers == set()


def test_pool_update_discarded_providers_2(pool_instance):
    assert pool_instance.providers == {"argenteam"}

    # Provider was discarded internally
    pool_instance.discarded_providers = {"argenteam"}

    assert pool_instance.discarded_providers == {"argenteam"}

    # Provider is not set to be used again
    pool_instance.update({"subdivx"}, {}, [], {})

    assert pool_instance.providers == {"subdivx"}

    # Provider should not disappear from discarded providers
    assert pool_instance.discarded_providers == {"argenteam"}
