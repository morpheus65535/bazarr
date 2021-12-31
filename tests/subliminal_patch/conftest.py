# -*- coding: utf-8 -*-

import pytest
import os

from subliminal_patch.core import Movie, Episode


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    return os.path.join("tests/subliminal_patch/cassettes", request.module.__name__)


@pytest.fixture
def movies():
    return {
        "dune": Movie(
            "Dune.2021.1080p.WEBRip.DD5.1.x264-SHITBOX",
            "Dune",
            year=2021,
            resolution="1080p",
            source="Web",
            # other="Rip",
            alternative_titles=["Dune: Part One"],
            audio_codec="Dolby Digital",
            video_codec="H.264",
            release_group="SHITBOX",
        ),
        "man_of_steel": Movie(
            os.path.join(
                "Man of Steel (2013)", "man.of.steel.2013.720p.bluray.x264-felony.mkv"
            ),
            "Man of Steel",
            source="Blu-Ray",
            release_group="felony",
            resolution="720p",
            video_codec="H.264",
            audio_codec="DTS",
            imdb_id="tt0770828",
            size=7033732714,
            year=2013,
            hashes={
                "napiprojekt": "6303e7ee6a835e9fcede9fb2fb00cb36",
                "opensubtitles": "5b8f8f4e41ccb21e",
                "shooter": "314f454ab464775498ae6f1f5ad813a9;fdaa8b702d8936feba2122e93ba5c44f;"
                "0a6935e3436aa7db5597ef67a2c494e3;4d269733f36ddd49f71e92732a462fe5",
                "thesubdb": "ad32876133355929d814457537e12dc2",
            },
        ),
        "enders_game": Movie(
            "enders.game.2013.720p.bluray.x264-sparks.mkv",
            "Ender's Game",
            source="Blu-Ray",
            release_group="sparks",
            resolution="720p",
            video_codec="H.264",
            year=2013,
        ),
        "blade_runner": Movie(
            "Alien (1979) Theatrical HDR 1080p UHD BluRay x265 HEVC EAC3-SARTRE",
            "Alien",
            source="Ultra HD Blu-ray",
            release_group="SARTRE",
            resolution="1080p",
            video_codec="H.265",
            audio_codec="Dolby Digital Plus",
            imdb_id="tt0078748",
            year=1979,
        ),
    }


@pytest.fixture
def episodes():
    return {
        "got_s03e10": Episode(
            os.path.join(
                "Game of Thrones",
                "Season 03",
                "Game.of.Thrones.S03E10.Mhysa.720p.WEB-DL.DD5.1.H.264-NTb.mkv",
            ),
            "Game of Thrones",
            3,
            10,
            title="Mhysa",
            tvdb_id=4517466,
            series_tvdb_id=121361,
            series_imdb_id="tt0944947",
            source="Web",
            release_group="NTb",
            resolution="720p",
            video_codec="H.264",
            audio_codec="AC3",
            imdb_id="tt2178796",
            size=2142810931,
            hashes={
                "napiprojekt": "6303e7ee6a835e9fcede9fb2fb00cb36",
                "opensubtitles": "b850baa096976c22",
                "shooter": "b02d992c04ad74b31c252bd5a097a036;ef1b32f873b2acf8f166fc266bdf011a;"
                "82ce34a3bcee0c66ed3b26d900d31cca;78113770551f3efd1e2d4ec45898c59c",
                "thesubdb": "b1f899c77f4c960b84b8dbf840d4e42d",
            },
        ),
        "breaking_bad_s01e01": Episode(
            "Breaking.Bad.S01E01.720p.BluRay.X264-REWARD.mkv",
            "Breaking Bad",
            1,
            1,
            source="Blu-Ray",
            release_group="REWARD",
            resolution="720p",
            video_codec="H.264",
        ),
    }
