import os

import pytest
from subliminal_patch import core
from subliminal_patch.score import compute_score
from subliminal_patch import core_persistent as corep
from subliminal_patch import Provider
from subliminal_patch import Subtitle
from subliminal_patch.core import SZProviderPool as Pool
from subzero.language import Language


class FakeProviderSubtitle(Subtitle):
    provider_name = "fake"

    def __init__(self, language, id, matches=None):
        super().__init__(language, page_link=id)
        self._id = id
        self._matches = set(matches or [])

        self.release_info = id

    def get_matches(self, video):
        return self._matches

    def id(self):
        return self.id


_ENGLISH = Language.fromietf("en")


class FakeProvider(Provider):
    languages = {_ENGLISH}
    video_types = (core.Movie, core.Episode)

    def __init__(self, fake_subtitles=None):
        self._fake_subtitles = fake_subtitles

    def initialize(self):
        pass

    def terminate(self):
        pass

    def list_subtitles(self, video, languages):
        return self._fake_subtitles

    def download_subtitle(self, subtitle):
        filename = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "data", "dummy.srt"
        )
        with open(filename, "rb") as f:
            subtitle.content = f.read()


core.provider_registry.register("fake", FakeProvider)


def test_pool_init_default():
    with Pool() as pool:
        assert pool


def test_pool_init_w_providers():
    with Pool(
        providers={"opensubtitles"},
        provider_configs={"opensubtitles": {"username": "foo", "password": "bar"}},
    ) as pool:
        assert pool.providers is not None
        assert isinstance(pool.provider_configs, core._ProviderConfigs)


def test_pool_init_w_blacklist():
    with Pool(blacklist=[("foo", "bar")]) as pool:
        assert isinstance(pool.blacklist, core._Blacklist)


def test_pool_init_w_ban_list():
    with Pool(ban_list={"must_contain": ["foo"], "must_not_contain": ["bar"]}) as pool:
        assert isinstance(pool.ban_list, core._Banlist)


def test_pool_init_w_throttle_callback():
    with Pool(throttle_callback=None) as pool:
        pool.throttle_callback("foo", "bar")


@pytest.fixture(scope="module")
def fake_subtitle():
    yield FakeProviderSubtitle(_ENGLISH, "foo")


@pytest.fixture(scope="module")
def fake_pool(fake_subtitle):
    with Pool(
        providers={"fake"},
        provider_configs={"fake": {"fake_subtitles": [fake_subtitle]}},
    ) as pool:
        yield pool


def test_pool_list_subtitles_provider(fake_pool, fake_subtitle, movies):
    result = fake_pool.list_subtitles_provider("fake", movies["dune"], {_ENGLISH})
    assert fake_subtitle in result


def test_pool_list_subtitles(fake_pool, fake_subtitle, movies):
    result = fake_pool.list_subtitles(movies["dune"], {_ENGLISH})
    assert fake_subtitle in result


def test_pool_download_subtitle(fake_pool, fake_subtitle):
    downloaded = fake_pool.download_subtitle(fake_subtitle)
    assert downloaded is True


def test_pool_download_best_subtitles(fake_pool, fake_subtitle, movies):
    result = fake_pool.download_best_subtitles(
        [fake_subtitle], movies["dune"], [_ENGLISH], compute_score=compute_score
    )
    assert result == [fake_subtitle]


@pytest.fixture(scope="module")
def empty_pool():
    with Pool() as pool:
        yield pool


def test_pool_core_persistent_list_all_subtitles(movies, empty_pool):
    assert corep.list_all_subtitles([movies["dune"]], {_ENGLISH}, empty_pool) == {
        movies["dune"]: []
    }


def test_pool_core_persistent_list_supported_languages(empty_pool):
    assert corep.list_supported_languages(empty_pool) == []


def test_pool_core_persistent_list_supported_video_types(empty_pool):
    assert corep.list_supported_video_types(empty_pool) == []


def test_pool_core_persistent_download_subtitles(empty_pool):
    corep.download_subtitles([], empty_pool)


def test_pool_core_persistent_download_best_subtitles(movies, empty_pool):
    assert corep.download_best_subtitles([movies["dune"]], {_ENGLISH}, empty_pool) == {
        movies["dune"]: []
    }
