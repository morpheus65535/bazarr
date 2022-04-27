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


@pytest.mark.parametrize(
    "episode_key,expected", [("breaking_bad_s01e01", 15), ("inexistent", 0)]
)
def test_list_subtitles_episode(episodes, episode_key, expected):
    item = episodes[episode_key]
    with SubdivxSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(item, {Language("spa", "MX")})
        assert len(subtitles) >= expected


def test_download_subtitle(movies):
    subtitle = SubdivxSubtitle(
        Language("spa", "MX"),
        movies["dune"],
        "https://www.subdivx.com/X66XNjMxMTAxX-dune--2021-aka-dune-part-one.html",
        "Dune",
        "",
        "",
        "https://www.subdivx.com/bajar.php?id=631101&u=9",
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
        "https://www.subdivx.com/bajar.php?id=365610&u=7",
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
        assert not subtitles[0].description.islower()


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
        "https://www.subdivx.com/bajar.php?id=635101&u=9",
    )

    matches = subtitle.get_matches(video)
    assert "source" in matches
    assert "resolution" in matches
    assert "video_codec" in matches
    assert "release_group" in matches
