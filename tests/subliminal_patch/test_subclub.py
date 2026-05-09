# -*- coding: utf-8 -*-
import pytest

from subliminal_patch.core import Episode, Movie
from subliminal_patch.providers.subclub import (
    SubclubProvider,
    SubclubSubtitle,
    TITLE_RE,
)
from subzero.language import Language


@pytest.mark.parametrize(
    "anchor_text,expected",
    [
        (
            "Inception (2010)",
            {"title": "Inception", "year": "2010", "season": None, "episode": None},
        ),
        (
            "Game of Thrones (2011) [01x02]",
            {"title": "Game of Thrones", "year": "2011", "season": "01", "episode": "02"},
        ),
        (
            "House M.D. (2004) [03x12]",
            {"title": "House M.D.", "year": "2004", "season": "03", "episode": "12"},
        ),
        (
            "The Simpsons Movie (2007)",
            {"title": "The Simpsons Movie", "year": "2007", "season": None, "episode": None},
        ),
    ],
)
def test_title_regex(anchor_text, expected):
    m = TITLE_RE.match(anchor_text)
    assert m is not None, anchor_text
    assert m.groupdict() == expected


def test_subtitle_movie_matches():
    sub = SubclubSubtitle(
        language=Language("est"),
        page_link="https://www.subclub.eu/down.php?id=10100",
        download_link="https://www.subclub.eu/down.php?id=10100&filename=X",
        archive_id="10100",
        filename="Inception.720p.BluRay.x264-CROSSBOW.srt",
        title="Inception",
        year=2010,
        season=None,
        episode=None,
        imdb_id="tt1375666",
        fps=23.976,
        rating=5.0,
        uploader="schnappi",
    )
    movie = Movie(
        "Inception.2010.720p.BluRay.x264-CROSSBOW.mkv",
        "Inception",
        year=2010,
        imdb_id="tt1375666",
    )
    matches = sub.get_matches(movie)
    assert {"title", "year", "imdb_id"} <= matches


def test_subtitle_episode_matches():
    sub = SubclubSubtitle(
        language=Language("est"),
        page_link="https://www.subclub.eu/down.php?id=11232",
        download_link="https://www.subclub.eu/down.php?id=11232&filename=X",
        archive_id="11232",
        filename="Game.of.Thrones.S01E01.720p.BluRay.X264-REWARD.srt",
        title="Game of Thrones",
        year=2011,
        season=1,
        episode=1,
        imdb_id="tt0944947",
        fps=23.976,
        rating=5.0,
        uploader="Orav",
    )
    ep = Episode(
        "Game.of.Thrones.S01E01.720p.BluRay.X264-REWARD.mkv",
        "Game of Thrones",
        1,
        1,
        series_imdb_id="tt0944947",
        year=2011,
    )
    matches = sub.get_matches(ep)
    assert {"series", "season", "episode", "year", "series_imdb_id"} <= matches


def test_list_subtitles_skips_when_no_estonian():
    with SubclubProvider() as provider:
        # English-only request must short-circuit without hitting the network.
        result = provider.list_subtitles(
            Movie("Inception.mkv", "Inception", year=2010), [Language("eng")]
        )
        assert result == []


@pytest.mark.vcr
def test_list_subtitles_movie_inception():
    """Inception has a working per-file listing; expect direct download URLs."""
    movie = Movie(
        "Inception.2010.720p.BluRay.x264-CROSSBOW.mkv",
        "Inception",
        year=2010,
        imdb_id="tt1375666",
    )
    with SubclubProvider() as provider:
        subs = provider.list_subtitles(movie, [Language("est")])
    assert subs, "expected at least one Inception subtitle"
    # Every returned sub references the same archive id.
    assert {s.archive_id for s in subs} == {"10100"}
    # The site exposes per-file URLs; nothing should be pre-extracted here.
    assert all(s.download_link and not s.content for s in subs)
    assert any("CROSSBOW" in s.filename for s in subs)


@pytest.mark.vcr
def test_list_subtitles_movie_shrek2_archive_fallback():
    """Shrek 2 has an empty per-file listing — must fall back to whole-archive
    extraction so the user still gets the individual releases."""
    movie = Movie(
        "Shrek.2.2004.WS.XviD.AC3-FOO.mkv",
        "Shrek 2",
        year=2004,
        imdb_id="tt0298148",
    )
    with SubclubProvider() as provider:
        subs = provider.list_subtitles(movie, [Language("est")])
    assert subs, "expected fallback to extract Shrek 2 subtitles"
    # Fallback path always pre-populates content during query().
    assert all(s.content for s in subs)
    # Filenames come from inside the archive — release-named entries should
    # be present alongside any plain CD splits.
    assert any("BRUTUS" in s.filename or "ShareConnector" in s.filename for s in subs)


@pytest.mark.vcr
def test_list_subtitles_movie_simpsons_movie_mixed():
    """The Simpsons Movie has two archives uploaded:
    - id=5270 has a working per-file listing (rar, but listed)
    - id=5159 has an empty listing (zip) and needs the archive fallback
    Both should be returned as a single combined result set.
    """
    movie = Movie(
        "The.Simpsons.Movie.2007.720p.BluRay.x264.mkv",
        "The Simpsons Movie",
        year=2007,
        imdb_id="tt0462538",
    )
    with SubclubProvider() as provider:
        subs = provider.list_subtitles(movie, [Language("est")])
    assert subs, "expected Simpsons Movie subtitles"
    archives = {s.archive_id for s in subs}
    assert {"5270", "5159"} <= archives, archives
    # The fallback archive should have its content pre-populated.
    fallback_subs = [s for s in subs if s.archive_id == "5159"]
    assert fallback_subs and all(s.content for s in fallback_subs)


@pytest.mark.vcr
def test_list_subtitles_episode_got_s01e01():
    ep = Episode(
        "Game.of.Thrones.S01E01.720p.BluRay.X264-REWARD.mkv",
        "Game of Thrones",
        1,
        1,
        series_imdb_id="tt0944947",
        year=2011,
    )
    with SubclubProvider() as provider:
        subs = provider.list_subtitles(ep, [Language("est")])
    assert subs
    # Filtering by season/episode keeps only the matching archive.
    assert {s.archive_id for s in subs} == {"11232"}
    assert any("REWARD" in s.filename for s in subs)
