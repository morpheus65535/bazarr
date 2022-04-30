import pytest

from subliminal_patch.providers.subf2m import Subf2mProvider
from subliminal_patch.providers.subf2m import Subf2mSubtitle
from subzero.language import Language


def test_search_movie(movies):
    movie = movies["dune"]

    with Subf2mProvider() as provider:
        result = provider._search_movie(movie.title, movie.year)
        assert result == "/subtitles/dune-2021"


def test_search_tv_show_season(episodes):
    episode = episodes["breaking_bad_s01e01"]

    with Subf2mProvider() as provider:
        result = provider._search_tv_show_season(episode.series, episode.season)
        assert result == "/subtitles/breaking-bad-first-season"


@pytest.mark.parametrize("language", [Language.fromalpha2("en"), Language("por", "BR")])
def test_find_movie_subtitles(language):
    path = "/subtitles/dune-2021"
    with Subf2mProvider() as provider:
        for sub in provider._find_movie_subtitles(path, language):
            assert sub.language == language


@pytest.mark.parametrize("language", [Language.fromalpha2("en"), Language("por", "BR")])
def test_find_episode_subtitles(language):
    path = "/subtitles/breaking-bad-first-season"
    with Subf2mProvider() as provider:
        for sub in provider._find_episode_subtitles(path, 1, 1, language):
            assert sub.language == language


@pytest.fixture
def subtitle():
    release_info = """Dune-2021.All.WEBDLL
        Dune.2021.WEBRip.XviD.MP3-XVID
        Dune.2021.WEBRip.XviD.MP3-SHITBOX
        Dune.2021.WEBRip.x264-SHITBOX
        Dune.2021.WEBRip.x264-ION10
        Dune.2021.HDRip.XviD-EVO[TGx]
        Dune.2021.HDRip.XviD-EVO
        Dune.2021.720p.HDRip.900MB.x264-GalaxyRG
        Dune.2021.1080p.HDRip.X264-EVO
        Dune.2021.1080p.HDRip.1400MB.x264-GalaxyRG"""

    return Subf2mSubtitle(
        Language.fromalpha3b("per"),
        "https://subf2m.co/subtitles/dune-2021/farsi_persian/2604701",
        release_info,
    )


@pytest.fixture
def subtitle_episode():
    return Subf2mSubtitle(
        Language.fromalpha2("en"),
        "https://subf2m.co/subtitles/breaking-bad-first-season/english/161227",
        "Breaking.Bad.S01E01-7.DSR-HDTV.eng",
    )


def test_subtitle_get_matches(subtitle, movies):
    assert subtitle.get_matches(movies["dune"])


def test_subtitle_get_matches_episode(subtitle_episode, episodes):
    assert subtitle_episode.get_matches(episodes["breaking_bad_s01e01"])


def test_list_subtitles_movie(movies):
    with Subf2mProvider() as provider:
        assert provider.list_subtitles(movies["dune"], {Language.fromalpha2("en")})


def test_list_subtitles_inexistent_movie(movies):
    with Subf2mProvider() as provider:
        assert (
            provider.list_subtitles(movies["inexistent"], {Language.fromalpha2("en")})
            == []
        )


def test_list_subtitles_episode(episodes):
    with Subf2mProvider() as provider:
        assert provider.list_subtitles(
            episodes["breaking_bad_s01e01"], {Language.fromalpha2("en")}
        )


def test_list_subtitles_inexistent_episode(episodes):
    with Subf2mProvider() as provider:
        assert (
            provider.list_subtitles(episodes["inexistent"], {Language.fromalpha2("en")})
            == []
        )


def test_download_subtitle(subtitle):
    with Subf2mProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.is_valid()


def test_download_subtitle_episode(subtitle_episode):
    with Subf2mProvider() as provider:
        provider.download_subtitle(subtitle_episode)
        assert subtitle_episode.is_valid()
