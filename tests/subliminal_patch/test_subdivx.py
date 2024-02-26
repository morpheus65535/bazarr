# -*- coding: utf-8 -*-

import pytest
import copy

from subliminal_patch.providers.subdivx import SubdivxSubtitlesProvider
from subliminal_patch.providers.subdivx import SubdivxSubtitle
from subliminal_patch.core import SZProviderPool
from subliminal_patch.core import Episode
from subzero.language import Language


def test_list_subtitles_movie(movies):
    item = movies["dune"]
    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        assert len(subtitles) >= 9


def test_list_subtitles_movie_with_year_fallback(movies):
    item = list(movies.values())[0]
    item.title = "Everything Everywhere All at Once"
    item.year = 2022

    with SubdivxSubtitlesProvider() as provider:
        assert provider.list_subtitles(item, {Language("spa", "MX")})


def test_list_subtitles_movie_with_one_difference_year(movies):
    item = list(movies.values())[0]
    item.title = "Sisu"
    item.year = 2023

    with SubdivxSubtitlesProvider() as provider:
        assert provider.list_subtitles(item, {Language("spa", "MX")})


@pytest.mark.parametrize(
    "episode_key,expected", [("breaking_bad_s01e01", 15), ("inexistent", 0)]
)
def test_list_subtitles_episode(episodes, episode_key, expected):
    item = episodes[episode_key]
    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        assert len(subtitles) >= expected


def test_list_subtitles_episode_with_year(episodes):
    item = list(episodes.values())[0]

    item.series = "The Twilight Zone"
    item.name = "The Twilight Zone"
    item.year = 1959
    item.season = 1
    item.episode = 1

    with SubdivxSubtitlesProvider() as provider:
        assert provider.list_subtitles(item, {Language.fromietf("es")})


def test_list_subtitles_castillian_spanish(episodes):
    item = episodes["better_call_saul_s06e04"]
    with SubdivxSubtitlesProvider() as provider:
        assert provider.list_subtitles(item, {Language.fromietf("es")})


def test_list_subtitles_episode_with_title_only_fallback(episodes):
    item = list(episodes.values())[0]
    item.series = "The Bear"
    item.name = "The Bear"
    item.season = 1
    item.episode = 1

    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        assert len(subtitles) > 2


def test_list_subtitles_episode_with_episode_title_fallback(episodes):
    item = list(episodes.values())[0]
    item.series = "30 for 30"
    item.title = "The Two Escobars"
    item.season = 1
    item.episode = 16

    with SubdivxSubtitlesProvider() as provider:
        sub = provider.list_subtitles(item, {Language("spa", "MX")})[0]
        assert sub.get_matches(item)
        provider.download_subtitle(sub)
        assert sub.is_valid()


def test_download_subtitle(movies):
    subtitle = SubdivxSubtitle(
        Language("spa", "MX"),
        movies["dune"],
        "https://www.subdivx.com/X66XNjMxMTAxX-dune--2021-aka-dune-part-one.html",
        "Dune",
        "",
        "",
        "https://www.subdivx.com/descargar.php?id=631101",
    )
    with SubdivxSubtitlesProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None


def test_download_subtitle_episode_pack(episodes):
    video = copy.copy(episodes["breaking_bad_s01e01"])
    video.episode = 3

    subtitle = SubdivxSubtitle(
        Language("spa", "MX"),
        video,
        "https://www.subdivx.com/X66XMzY1NjEwX-breaking-bad-s01e0107.html",
        "Breaking Bad S01E01-07",
        "Son los del torrent que vienen Formato / Dimensiones 624x352 / Tamaño 351 MB -Incluye los Torrents-",
        "",
        "https://www.subdivx.com/descargar.php?id=365610",
    )
    with SubdivxSubtitlesProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None


@pytest.fixture
def video():
    return Episode(
        **{
            "name": "/tv/SEAL Team/Season 5/SEAL.Team.S05E11.1080p.WEB.H264-CAKES[rarbg].mkv",
            "release_group": "CAKES",
            "series": "SEAL Team",
            "source": "Web",
            "resolution": "1080p",
            "video_codec": "H.264",
            "season": 5,
            "episode": 11,
            "title": "Violence of Action",
            "alternative_series": [],
        }
    )


def test_subtitle_description_not_lowercase(video):
    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(video, {Language("spa", "MX")})
        assert subtitles
        assert not subtitles[0]._description.islower()


def test_subtitle_matches(video):
    subtitle = SubdivxSubtitle(
        Language("spa", "MX"),
        video,
        "SEAL Team S05E10",
        "https://www.subdivx.com/X66XNjM1MTAxX-seal-team-s05e10.html",
        (
            "Mi subtítulo y sincronización en Español neutro, para SEAL TEAM -Temp 05x10 "
            "Head On para WEB.H265-GGWP, NTb 1080p, WEB-H264.CAKES, WEBRip.x264-ION10 y "
            "otras seguramente, gracias por sus comentarios, saludos."
        ),
        "tolobich",
        "https://www.subdivx.com/descargar.php?id=635101",
    )

    matches = subtitle.get_matches(video)
    assert "source" in matches
    assert "resolution" in matches
    assert "video_codec" in matches
    assert "release_group" in matches


def test_latin_1_subtitles():
    item = Episode.fromname(
        "/tv/Grey's Anatomy/Season 19/Greys.Anatomy.S19E13.1080p.WEB.h264-ELEANOR[rarbg].mkv"
    )

    item.series = "Grey's Anatomy"
    item.season = 19
    item.episode = 13

    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language.fromietf("es")})
        subtitle = subtitles[0]

        provider.download_subtitle(subtitle)

        assert subtitle.is_valid()
