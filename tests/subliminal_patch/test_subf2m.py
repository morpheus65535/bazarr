import pytest

from subliminal_patch.providers.subf2m import Subf2mProvider
from subliminal_patch.providers.subf2m import Subf2mSubtitle
from subzero.language import Language


@pytest.mark.parametrize(
    "title,year,expected_url",
    [
        (
            "Dead Man's Chest",
            2006,
            "/subtitles/pirates-of-the-caribbean-2-dead-mans-chest",
        ),
        ("Dune", 2021, "/subtitles/dune-2021"),
        ("Cure", 1997, "/subtitles/cure-kyua"),
    ],
)
def test_search_movie(movies, title, year, expected_url):
    movie = list(movies.values())[0]
    movie.title = title
    movie.year = year

    with Subf2mProvider() as provider:
        result = provider._search_movie(movie.title, movie.year)
        assert result == expected_url


@pytest.mark.parametrize(
    "title,season,expected_url",
    [
        ("Breaking Bad", 1, "/subtitles/breaking-bad-first-season"),
        ("House Of The Dragon", 1, "/subtitles/house-of-the-dragon-first-season"),
        ("The Bear", 1, "/subtitles/the-bear-first-season"),
        ("Courage the Cowardly Dog", 1, "/subtitles/courage-the-cowardly-dog"),
    ],
)
def test_search_tv_show_season(episodes, title, season, expected_url):
    episode = list(episodes.values())[0]
    episode.name = title
    episode.series = title
    episode.season = season

    with Subf2mProvider() as provider:
        result = provider._search_tv_show_season(episode.series, episode.season)
        assert result == expected_url


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


def test_find_episode_subtitles_from_complete_series_path():
    path = "/subtitles/courage-the-cowardly-dog"

    with Subf2mProvider() as provider:
        for sub in provider._find_episode_subtitles(
            path, 1, 1, Language.fromalpha2("en")
        ):
            assert sub.language == Language.fromalpha2("en")


def test_list_and_download_subtitles_complete_series_pack(episodes):
    episode = list(episodes.values())[0]

    episode.series = "Sam & Max: Freelance Police"
    episode.name = "The Glazed McGuffin Affair"
    episode.title = "The Glazed McGuffin Affair"
    episode.season = 1
    episode.episode = 21

    with Subf2mProvider() as provider:
        subtitles = provider.list_subtitles(episode, {Language.fromalpha2("en")})
        assert subtitles

        subtitle = subtitles[0]
        provider.download_subtitle(subtitle)

        assert subtitle.is_valid()


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
        7,
    )


def test_subtitle_get_matches(subtitle, movies):
    matches = subtitle.get_matches(movies["dune"])  # type: set
    assert matches.issuperset(
        ("title", "year", "source", "video_codec", "resolution", "release_group")
    )


def test_subtitle_get_matches_episode(subtitle_episode, episodes):
    matches = subtitle_episode.get_matches(episodes["breaking_bad_s01e01"])  # type: set
    assert matches.issuperset(("title", "series", "season", "episode"))
    assert "source" not in matches


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


def test_download_subtitle_episode_with_title():
    sub = Subf2mSubtitle(
        Language.fromalpha2("en"),
        "https://subf2m.co/subtitles/courage-the-cowardly-dog/english/2232402",
        "Season 3 complete.",
        13,
    )

    sub.episode_title = "Feast of the Bullfrogs"
    with Subf2mProvider() as provider:
        provider.download_subtitle(sub)
        assert sub.is_valid()
