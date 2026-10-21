#!/usr/bin/env python
"""Archive / image / artwork container tests.

#272 (archive containers) and #273 (metadata/image files): the extension must be
recognised as a container and must NOT leak into release_group / title / etc.
"""

from __future__ import annotations

from .. import guessit


def test_archive_extensions_recognised_and_no_leak() -> None:
    rar = guessit("Show.Name.S01E01.720p.HDTV.x264-GRP.rar")
    assert rar["release_group"] == "GRP"
    assert rar["container"] == "rar"

    split = guessit("Movie.2020.1080p.x264.r00")  # split RAR volume
    assert split["container"] == "r00"
    assert "release_group" not in split

    sevenz = guessit("Show.S01E01.7z")
    assert sevenz["container"] == "7z"
    assert "episode_title" not in sevenz

    zip_ = guessit("Movie.2020.1080p-GRP.zip")
    assert zip_["release_group"] == "GRP"
    assert zip_["container"] == "zip"


def test_image_extensions_recognised_and_no_leak() -> None:
    jpg = guessit("Show.S01E01.720p-GRP.jpg")
    assert jpg["release_group"] == "GRP"
    assert jpg["container"] == "jpg"


def test_artwork_files_classified_as_other() -> None:
    assert guessit("poster.jpg")["other"] == "Poster"
    assert guessit("poster.jpg")["container"] == "jpg"

    fanart = guessit("Movie.2020-fanart.jpg")
    assert fanart["title"] == "Movie"
    assert fanart["other"] == "Fanart"

    assert guessit("banner.jpg")["other"] == "Banner"
    assert guessit("Show.S01-thumb.tbn")["other"] == "Thumbnail"


def test_artwork_keyword_in_real_title_not_clobbered() -> None:
    result = guessit("The.Poster.2020.1080p.BluRay.x264-GRP.mkv")
    assert result["title"] == "The Poster"
    assert "other" not in result
