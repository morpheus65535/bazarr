import pytest
from subliminal_patch.providers.subtitrarinoi import SubtitrarinoiProvider
from subliminal_patch.providers.subtitrarinoi import SubtitrarinoiSubtitle
from subzero.language import Language

romanian = Language("ron")


def test_list_subtitles(episodes):
    episode = episodes["breaking_bad_s01e01"]
    with SubtitrarinoiProvider() as provider:
        assert provider.list_subtitles(episode, [romanian])


@pytest.fixture
def subtitrari_subtitle():
    yield SubtitrarinoiSubtitle(
        romanian,
        "https://www.subtitrari-noi.ro/7493-subtitrari noi.ro\ ",
        3,
        "Sezonul 1 ep. 1-7 Sincronizari si pentru variantele HDTV x264 (Sincro atty)",
        "Breaking Bad",
        "tt0903747/",
        "Alice",
        "https://www.subtitrari-noi.ro/index.php?page=movie_details&act=1&id=7493",
        2008,
        4230,
        True,
        1,
    )


@pytest.mark.parametrize("comment", ["season 01", "Sezonul 1 ep. 1-7", "S01"])
def test_subtitle_get_matches_episode(subtitrari_subtitle, episodes, comment):
    episode = episodes["breaking_bad_s01e01"]
    episode.episode = 1
    subtitrari_subtitle.comments = comment
    assert {"season", "episode", "series", "imdb_id"}.issubset(
        subtitrari_subtitle.get_matches(episode)
    )


@pytest.mark.parametrize("comment", ["season 02", "Sezonul 2 ep. 1-7", "version 01"])
def test_subtitle_get_matches_episode_false(subtitrari_subtitle, episodes, comment):
    episode = episodes["breaking_bad_s01e01"]
    episode.episode = 1
    subtitrari_subtitle.comments = comment
    assert not {"season", "episode"}.issubset(subtitrari_subtitle.get_matches(episode))


def test_provider_download_subtitle(subtitrari_subtitle):
    with SubtitrarinoiProvider() as provider:
        provider.download_subtitle(subtitrari_subtitle)
        assert subtitrari_subtitle.is_valid()
