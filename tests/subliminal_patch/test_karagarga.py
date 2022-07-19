import os
import tempfile

import pytest
from subliminal.cache import region
from subliminal_patch.providers.karagarga import ConfigurationError
from subliminal_patch.providers.karagarga import KaragargaProvider
from subliminal_patch.providers.karagarga import KaragargaSubtitle
from subliminal_patch.providers.karagarga import Language

_USER = os.environ.get("KARAGARGA_USER")
_PASSWORD = os.environ.get("KARAGARGA_PASSWORD")

# TODO: maybe move this region to subliminal_patch's conftest.py

region.configure(
    "dogpile.cache.dbm",
    arguments={
        "filename": os.path.join(tempfile.gettempdir(), "subliminal_patch_tests.db")
    },
)

pytestmark = pytest.mark.skipif(
    _USER is None or _PASSWORD is None,
    reason="KARAGARGA_USER KARAGARGA_PASSWORD env vars not provided",
)


@pytest.fixture(scope="module")
def provider():
    with KaragargaProvider(_USER, _PASSWORD) as provider:
        yield provider


def test_init_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        assert KaragargaProvider("", "")


def test_login(provider):
    assert provider


@pytest.mark.parametrize(
    "title,year,expected_subs_len",
    [("Paradise", 2009, 2), ("Her Way", 2021, 2), ("Batrachian's Ballad", 2016, 1)],
)
def test_search_movie(provider, title, year, expected_subs_len):
    subtitles = provider._search_movie(title, year)
    assert len(subtitles) >= expected_subs_len


def test_list_subtitles(provider, movies):
    item = list(movies.values())[0]
    item.title = "Paradise"
    item.year = 2009

    assert provider.list_subtitles(item, {Language.fromietf("en")})


def test_download_subtitle(provider):
    subtitle = KaragargaSubtitle(
        Language.fromietf("en"),
        "https://forum.karagarga.in/index.php?app=core&module=attach&section=attach&attach_id=49324",
        "foo",
        1,
    )
    provider.download_subtitle(subtitle)
    assert subtitle.is_valid()


def test_subtitle_get_matches(movies):
    subtitle = KaragargaSubtitle(Language.fromietf("en"), "foo", "Foo.2019", 0)
    assert {"title", "year"}.issubset(subtitle.get_matches(movies["inexistent"]))
