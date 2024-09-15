import pytest
from subliminal_patch.core import Episode
from subliminal_patch.providers import subf2m
from subliminal_patch.providers.subf2m import ConfigurationError
from subliminal_patch.providers.subf2m import Subf2mProvider
from subliminal_patch.providers.subf2m import Subf2mSubtitle
from subzero.language import Language

_U_A = "Mozilla/5.0 (Linux; Android 10; SM-G996U Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36"


@pytest.fixture
def provider():
    with Subf2mProvider(user_agent=_U_A) as provider:
        yield provider


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
def test_search_movie(provider, title, year, expected_url):
    result = provider._search_movie(title, year)
    assert expected_url in result


def test_init_empty_user_agent_raises_configurationerror():
    with pytest.raises(ConfigurationError):
        with Subf2mProvider(user_agent=" ") as provider:
            assert provider


@pytest.mark.parametrize(
    "series_title,season,year,expected_url",
    [
        ("Breaking Bad", 1, None, "/subtitles/breaking-bad-first-season"),
        ("House Of The Dragon", 1, None, "/subtitles/house-of-the-dragon-first-season"),
        ("The Bear", 1, None, "/subtitles/the-bear-first-season"),
        ("Courage the Cowardly Dog", 1, None, "/subtitles/courage-the-cowardly-dog"),
        (
            "The Twilight Zone",
            2,
            1959,
            "/subtitles/the-twilight-zone-the-complete-original-series",
        ),
    ],
)
def test_search_tv_show_season(provider, series_title, season, year, expected_url):
    result = provider._search_tv_show_season(series_title, season, year)
    assert expected_url in result


@pytest.mark.parametrize("language", [Language.fromalpha2("en"), Language("por", "BR")])
def test_find_movie_subtitles(provider, language, movies):
    path = "/subtitles/dune-2021"
    for sub in provider._find_movie_subtitles(path, language, movies["dune"].imdb_id):
        assert sub.language == language


@pytest.mark.parametrize("language", [Language.fromalpha2("en"), Language("por", "BR")])
def test_find_episode_subtitles(provider, language, episodes):
    path = "/subtitles/breaking-bad-first-season"
    subs = provider._find_episode_subtitles(
        path, 1, 1, language, imdb_id=episodes["breaking_bad_s01e01"].series_imdb_id
    )
    assert subs

    for sub in subs:
        assert sub.language == language


def test_find_episode_subtitles_from_complete_series_path(provider):
    path = "/subtitles/courage-the-cowardly-dog"

    subs = provider._find_episode_subtitles(
        path, 1, 1, Language.fromalpha2("en"), imdb_id="tt0220880"
    )
    assert subs

    for sub in subs:
        assert sub.language == Language.fromalpha2("en")


def test_list_and_download_subtitles_complete_series_pack(provider, episodes):
    episode = list(episodes.values())[0]

    episode.series = "Sam & Max: Freelance Police"
    episode.name = "The Glazed McGuffin Affair"
    episode.title = "The Glazed McGuffin Affair"
    episode.series_imdb_id = "tt0125646"
    episode.season = 1
    episode.episode = 21

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


def test_list_subtitles_movie(provider, movies):
    assert provider.list_subtitles(movies["dune"], {Language.fromalpha2("en")})


def test_list_subtitles_inexistent_movie(provider, movies):
    assert (
        provider.list_subtitles(movies["inexistent"], {Language.fromalpha2("en")}) == []
    )


def test_list_subtitles_episode(provider, episodes):
    assert provider.list_subtitles(
        episodes["breaking_bad_s01e01"], {Language.fromalpha2("en")}
    )


def test_list_subtitles_inexistent_episode(provider, episodes):
    assert (
        provider.list_subtitles(episodes["inexistent"], {Language.fromalpha2("en")})
        == []
    )


def test_download_subtitle(provider, subtitle):
    provider.download_subtitle(subtitle)
    assert subtitle.is_valid()


def test_download_subtitle_episode(provider, subtitle_episode):
    provider.download_subtitle(subtitle_episode)
    assert subtitle_episode.is_valid()


@pytest.mark.parametrize(
    "language,page_link,release_info,episode_number,episode_title",
    [
        (
            "en",
            "https://subf2m.co/subtitles/courage-the-cowardly-dog/english/2232402",
            "Season 3 complete.",
            13,
            "Feast of the Bullfrogs",
        ),
        (
            "en",
            "https://subf2m.co/subtitles/rick-and-morty-sixth-season/english/3060783",
            "Used Subtitle Tools to convert from SUP to SRT, then ran the cleaner to remove HI. Grabbed subs from Rick.and.Morty.S06.1080p.BluRay.x264-STORiES.",
            7,
            "Full Meta Jackrick",
        ),
    ],
)
def test_download_subtitle_episode_with_title(
    provider, language, page_link, release_info, episode_number, episode_title
):
    sub = Subf2mSubtitle(
        Language.fromalpha2(language),
        page_link,
        release_info,
        episode_number,
    )

    sub.episode_title = episode_title
    provider.download_subtitle(sub)
    assert sub.is_valid()


def test_get_episode_from_release():
    assert subf2m._get_episode_from_release(
        "Vinland Saga Season 2 - 05 [Crunchyroll][Crunchyroll] Vinland Saga Season 2 - 05"
    ) == {"season": [2], "episode": [5]}


def test_get_episode_from_release_return_none():
    assert subf2m._get_episode_from_release("Vinland Saga Season 2 - Foo") is None


def test_get_episode_from_release_w_empty_match_return_none():
    assert subf2m._get_episode_from_release("Vinland Saga - 02") is None


def test_complex_episode_name(provider):
    episode = Episode(
        **{
            "name": "Dr.Romantic.S03E16.SBS.x265.1080p-thon.mkv",
            "source": "HDTV",
            "release_group": "thon",
            "resolution": "1080p",
            "video_codec": "H.265",
            "audio_codec": "AAC",
            "subtitle_languages": set(),
            "original_name": "Dr. Romantic - S03E16.mkv",
            "other": None,
            "series": "Dr. Romantic",
            "season": 3,
            "episode": 16,
            "title": "Dreamers",
            "year": 2016,
            "series_imdb_id": "tt6157190",
            "alternative_series": ["Romantic Doctor Teacher Kim"],
        }
    )
    assert provider.list_subtitles(episode, {Language.fromietf("en")})
