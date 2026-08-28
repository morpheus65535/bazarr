# -*- coding: utf-8 -*-
import gzip
import io
import os
import zipfile

import pytest
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers.opensubtitlesorg import OpenSubtitlesOrgProvider
from subliminal_patch.providers.opensubtitlesorg import OpenSubtitlesOrgSubtitle
from subzero.language import Language

_SERVER_URL = "https://api.opensubtitles.org"

# Well-formed SRT content (a trailing blank line is required for pysubs2 to
# auto-detect the format).
_SRT_CONTENT = (
    "1\n00:00:01,000 --> 00:00:02,000\nHello world\n\n"
    "2\n00:00:03,000 --> 00:00:04,000\nSecond line\n\n"
).encode("utf-8")


@pytest.fixture
def provider():
    with OpenSubtitlesOrgProvider(user_agent="Mozilla/5.0 (BazarrTest)") as provider:
        yield provider


@pytest.fixture
def matrix_resurrections():
    return Movie(
        "The.Matrix.Resurrections.2021.1080p.WEBRip.x265-RARBG.mkv",
        "The Matrix Resurrections",
        year=2021,
        imdb_id="tt10838180",
        resolution="1080p",
        source="Web",
        video_codec="H.265",
        release_group="RARBG",
    )


@pytest.fixture
def breaking_bad_s01e01():
    return Episode(
        "Breaking.Bad.S01E01.720p.BluRay.X264-REWARD.mkv",
        "Breaking Bad",
        1,
        1,
        source="Blu-Ray",
        series_tvdb_id=81189,
        series_imdb_id="tt0903747",
        release_group="REWARD",
        resolution="720p",
        video_codec="H.264",
    )


def _register_movie_search(requests_mock, data, language_code="eng"):
    with open(
        os.path.join(data, "opensubtitlesorg_movie_search.html"), "rb"
    ) as f:
        content = f.read()

    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-The%20Matrix%20Resurrections/sublanguageid-{language_code}",
        content=content,
    )
    # The provider queries once per requested language; register the same
    # fixture for every language used across the tests below.
    for code in ("eng", "kor", "rum", "spa"):
        requests_mock.get(
            f"{_SERVER_URL}/en/search/moviename-The%20Matrix%20Resurrections/sublanguageid-{code}",
            content=content,
        )


def _register_episode_search(requests_mock, data):
    with open(
        os.path.join(data, "opensubtitlesorg_episode_search.html"), "rb"
    ) as f:
        content = f.read()

    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Breaking%20Bad%20S01E01/sublanguageid-eng",
        content=content,
    )
    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Breaking%20Bad/sublanguageid-eng",
        content=content,
    )


_DETAIL_PAGE_URL = f"{_SERVER_URL}/en/subtitles/13303030/the-matrix-resurrections-en"
_REAL_DOWNLOAD_URL = "https://dl.opensubtitles.org/en/download/file/1957556258"


def _register_detail_page(requests_mock, data, page_url=_DETAIL_PAGE_URL):
    with open(
        os.path.join(data, "opensubtitlesorg_detail_page.html"), "rb"
    ) as f:
        content = f.read()
    requests_mock.get(page_url, content=content)


def test_provider_requires_no_credentials():
    # Should not raise and should not accept username/password kwargs.
    with OpenSubtitlesOrgProvider() as provider:
        assert provider is not None

    with pytest.raises(TypeError):
        OpenSubtitlesOrgProvider(username="foo", password="bar")


def test_list_subtitles_movie(provider, requests_mock, data, matrix_resurrections):
    _register_movie_search(requests_mock, data)

    subtitles = provider.list_subtitles(
        matrix_resurrections, {Language.fromalpha2("en")}
    )

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.language == Language.fromalpha2("en")
    assert subtitle.download_id == "13303030"
    assert subtitle.uploader == "bairesxpress"
    assert subtitle.hearing_impaired is False
    assert "imdb_id" in subtitle.matches


def test_list_subtitles_movie_multiple_languages(
    provider, requests_mock, data, matrix_resurrections
):
    _register_movie_search(requests_mock, data)

    subtitles = provider.list_subtitles(
        matrix_resurrections,
        {Language.fromalpha2("en"), Language.fromalpha2("ko"), Language.fromalpha2("ro")},
    )

    languages_found = {subtitle.language for subtitle in subtitles}
    assert languages_found == {
        Language.fromalpha2("en"),
        Language.fromalpha2("ko"),
        Language.fromalpha2("ro"),
    }


def test_list_subtitles_movie_excludes_wrong_imdb_id(
    provider, requests_mock, data, matrix_resurrections
):
    """The fixture also contains a Matrix Revolutions (different IMDB id)
    row for the Spanish language; it must never be returned for a
    Resurrections search."""
    _register_movie_search(requests_mock, data)

    subtitles = provider.list_subtitles(
        matrix_resurrections, {Language.fromalpha2("es")}
    )

    assert subtitles == []


def test_list_subtitles_inexistent_movie(provider, requests_mock, data):
    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Some%20Inexistent%20Movie/sublanguageid-eng",
        content=b"<html><body><table><tbody></tbody></table></body></html>",
    )

    movie = Movie(
        "some.inexistent.movie.2050.mkv", "Some Inexistent Movie", year=2050
    )

    assert provider.list_subtitles(movie, {Language.fromalpha2("en")}) == []


def test_list_subtitles_unsupported_language_returns_empty(
    provider, matrix_resurrections
):
    # "und" (undefined) is never a valid OpenSubtitles.org language.
    assert provider.list_subtitles(matrix_resurrections, {Language("und")}) == []


def test_list_subtitles_episode(
    provider, requests_mock, data, breaking_bad_s01e01
):
    _register_episode_search(requests_mock, data)

    subtitles = provider.list_subtitles(
        breaking_bad_s01e01, {Language.fromalpha2("en")}
    )

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.download_id == "20000001"
    assert subtitle.episode_number == 1
    assert "season" in subtitle.matches
    assert "episode" in subtitle.matches
    assert "imdb_id" in subtitle.matches


def test_list_subtitles_inexistent_episode(provider, requests_mock, data):
    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Some%20Show%20S01E01/sublanguageid-eng",
        content=b"<html><body><table><tbody></tbody></table></body></html>",
    )
    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Some%20Show/sublanguageid-eng",
        content=b"<html><body><table><tbody></tbody></table></body></html>",
    )

    episode = Episode(
        "Some.Show.S01E01.mkv", "Some Show", 1, 1, series_imdb_id="tt0000000"
    )

    assert provider.list_subtitles(episode, {Language.fromalpha2("en")}) == []


def test_subtitle_get_matches_movie(matrix_resurrections):
    subtitle = OpenSubtitlesOrgSubtitle(
        Language.fromalpha2("en"),
        f"{_SERVER_URL}/en/subtitles/13303030/the-matrix-resurrections-en",
        "13303030",
        "The.Matrix.4.Resurrections.2021.1080p.WEBRip.x265-RARBG",
        imdb_match=True,
    )

    matches = subtitle.get_matches(matrix_resurrections)

    assert matches.issuperset(
        {"title", "year", "imdb_id", "resolution", "video_codec", "release_group"}
    )


def test_subtitle_get_matches_episode(breaking_bad_s01e01):
    subtitle = OpenSubtitlesOrgSubtitle(
        Language.fromalpha2("en"),
        f"{_SERVER_URL}/en/subtitles/20000001/breaking-bad-en",
        "20000001",
        "Breaking.Bad.S01E01.720p.BluRay.X264-REWARD",
        imdb_match=True,
        episode_number=1,
    )

    matches = subtitle.get_matches(breaking_bad_s01e01)

    assert matches.issuperset(
        {"title", "series", "season", "episode", "imdb_id", "resolution", "release_group"}
    )


def test_subtitle_id_is_download_id():
    subtitle = OpenSubtitlesOrgSubtitle(
        Language.fromalpha2("en"), "https://example.org/x", "42", "Some.Release"
    )
    assert subtitle.id == "42"


def _make_subtitle(page_link=_DETAIL_PAGE_URL):
    return OpenSubtitlesOrgSubtitle(
        Language.fromalpha2("en"), page_link, "13303030", "Some.Release-GROUP"
    )


def test_download_subtitle_zip_archive(provider, requests_mock, data):
    _register_detail_page(requests_mock, data)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("subtitle.srt", _SRT_CONTENT)

    requests_mock.get(_REAL_DOWNLOAD_URL, content=buf.getvalue())

    subtitle = _make_subtitle()
    provider.download_subtitle(subtitle)

    assert subtitle.is_valid()


def test_download_subtitle_gzip_raw_file(provider, requests_mock, data):
    """A raw gzip-compressed file body (no Content-Encoding header) must
    still be handled defensively, even though live testing showed the
    real endpoint uses standard HTTP Content-Encoding: gzip (already
    transparently decoded by `requests`)."""
    _register_detail_page(requests_mock, data)
    requests_mock.get(_REAL_DOWNLOAD_URL, content=gzip.compress(_SRT_CONTENT))

    subtitle = _make_subtitle()
    provider.download_subtitle(subtitle)

    assert subtitle.is_valid()


def test_download_subtitle_raw_uncompressed_file(provider, requests_mock, data):
    """Matches the real, live-confirmed response: a plain-text .srt body
    (requests already decoded the transport-level gzip encoding)."""
    _register_detail_page(requests_mock, data)
    requests_mock.get(_REAL_DOWNLOAD_URL, content=_SRT_CONTENT)

    subtitle = _make_subtitle()
    provider.download_subtitle(subtitle)

    assert subtitle.is_valid()


def test_download_subtitle_unrecognized_content_raises(provider, requests_mock, data):
    _register_detail_page(requests_mock, data)
    requests_mock.get(
        _REAL_DOWNLOAD_URL, content=b"<html><body>not a subtitle</body></html>"
    )

    subtitle = _make_subtitle()
    with pytest.raises(APIThrottled):
        provider.download_subtitle(subtitle)


def test_download_subtitle_extracts_token_from_detail_page(
    provider, requests_mock, data
):
    """The download token is dynamic and must be scraped fresh from the
    subtitle's own detail page -- not derived/guessed from the search
    result's subtitle id."""
    _register_detail_page(requests_mock, data)
    requests_mock.get(_REAL_DOWNLOAD_URL, content=_SRT_CONTENT)

    subtitle = _make_subtitle()
    provider.download_subtitle(subtitle)

    detail_page_request = requests_mock.request_history[0]
    download_request = requests_mock.request_history[1]
    assert detail_page_request.url == _DETAIL_PAGE_URL
    assert download_request.url == _REAL_DOWNLOAD_URL


def test_download_subtitle_missing_page_link_raises(provider):
    subtitle = OpenSubtitlesOrgSubtitle(
        Language.fromalpha2("en"), None, "13303030", "Some.Release-GROUP"
    )
    with pytest.raises(APIThrottled):
        provider.download_subtitle(subtitle)


def test_download_subtitle_no_token_on_detail_page_raises(
    provider, requests_mock
):
    requests_mock.get(
        _DETAIL_PAGE_URL, content=b"<html><body>no download link here</body></html>"
    )

    subtitle = _make_subtitle()
    with pytest.raises(APIThrottled):
        provider.download_subtitle(subtitle)


def test_languages_do_not_require_credentials():
    # No username/password attribute should exist on the provider at all.
    assert not hasattr(OpenSubtitlesOrgProvider, "username")
    assert not hasattr(OpenSubtitlesOrgProvider, "password")


def test_languages_contains_common_codes():
    assert Language.fromalpha2("en") in OpenSubtitlesOrgProvider.languages
    assert Language("por", "BR") in OpenSubtitlesOrgProvider.languages
    assert Language("srp") in OpenSubtitlesOrgProvider.languages


# ---------------------------------------------------------------------------
# End-to-end integration test: Reacher S04E05 ("Bridge"), Bulgarian.
#
# Built from a real live test run against opensubtitles.org (not captured as
# raw HTML files, but confirmed real data points):
#   subtitle id:    14004171
#   detail URL:     https://api.opensubtitles.org/en/subtitles/14004171/reacher-bridge-bg
#   download token: 1962567586
#   download URL:   https://dl.opensubtitles.org/en/download/file/1962567586
#   filename:       "Reacher S04E05 Bridge 1080p AMZN WEB-DL DDP5 1 H 264-NTb.bg.srt"
#
# This test drives the provider's public API only (list_subtitles +
# download_subtitle) -- it does not call requests directly.
# ---------------------------------------------------------------------------

_REACHER_DETAIL_URL = (
    f"{_SERVER_URL}/en/subtitles/14004171/reacher-bridge-bg"
)
_REACHER_DOWNLOAD_URL = "https://dl.opensubtitles.org/en/download/file/1962567586"

_REACHER_SRT_CONTENT = (
    "1\n00:00:01,000 --> 00:00:03,000\n"
    "\u041f\u0440\u0435\u0434\u0438\u0448\u043d\u043e...\n\n"
    "2\n00:00:03,500 --> 00:00:06,000\n"
    "\u0422\u043e\u0432\u0430 \u0435 \u043c\u043e\u0441\u0442.\n\n"
    "3\n00:00:06,500 --> 00:00:09,000\n"
    "\u0422\u0440\u044f\u0431\u0432\u0430 \u0434\u0430 "
    "\u0433\u043e \u043f\u0440\u0435\u043c\u0438\u043d\u0435\u043c.\n\n"
).encode("utf-8")


@pytest.fixture
def reacher_s04e05():
    return Episode(
        "Reacher.S04E05.Bridge.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.mkv",
        "Reacher",
        4,
        5,
        title="Bridge",
        series_imdb_id="tt9288812",
        release_group="NTb",
        resolution="1080p",
        streaming_service="AMZN",
        source="Web",
    )


def _register_reacher_search(requests_mock, data):
    with open(
        os.path.join(data, "opensubtitlesorg_reacher_episode_search.html"), "rb"
    ) as f:
        content = f.read()

    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Reacher%20S04E05/sublanguageid-bul",
        content=content,
    )
    requests_mock.get(
        f"{_SERVER_URL}/en/search/moviename-Reacher/sublanguageid-bul",
        content=content,
    )


def _register_reacher_detail_and_download(requests_mock, data):
    with open(
        os.path.join(data, "opensubtitlesorg_reacher_detail_page.html"), "rb"
    ) as f:
        detail_content = f.read()

    requests_mock.get(_REACHER_DETAIL_URL, content=detail_content)
    requests_mock.get(
        _REACHER_DOWNLOAD_URL,
        content=_REACHER_SRT_CONTENT,
        headers={
            "Content-Type": "application/force-download",
            "Content-Disposition": (
                'attachment; filename="Reacher S04E05 Bridge 1080p AMZN '
                'WEB-DL DDP5 1 H 264-NTb.bg.srt"'
            ),
        },
    )


def test_integration_reacher_s04e05_bulgarian_list_subtitles(
    provider, requests_mock, data, reacher_s04e05
):
    """OpenSubtitlesOrgProvider.list_subtitles() must find the Bulgarian
    Reacher S04E05 subtitle through the provider's public API only."""
    _register_reacher_search(requests_mock, data)

    bulgarian = Language.fromalpha2("bg")
    assert bulgarian in OpenSubtitlesOrgProvider.languages

    subtitles = provider.list_subtitles(reacher_s04e05, {bulgarian})

    assert len(subtitles) == 1
    subtitle = subtitles[0]
    assert subtitle.language == bulgarian
    assert subtitle.download_id == "14004171"
    assert subtitle.page_link == _REACHER_DETAIL_URL
    assert subtitle.episode_number == 5
    assert {"series", "season", "episode", "imdb_id"}.issubset(subtitle.matches)


def test_integration_reacher_s04e05_bulgarian_full_flow(
    provider, requests_mock, data, reacher_s04e05
):
    """Full, real-mechanism, end-to-end flow through the provider's public
    API: list_subtitles() -> download_subtitle() -> valid SRT content.

    Confirms, via the actual provider code path (not a standalone script):
      - search finds the subtitle for season=4, episode=5, language=bg
      - download_subtitle() opens the detail page
      - the dynamic dl.opensubtitles.org token is extracted from it
      - the subtitle is downloaded and produces valid SRT content
    """
    _register_reacher_search(requests_mock, data)
    _register_reacher_detail_and_download(requests_mock, data)

    bulgarian = Language.fromalpha2("bg")
    subtitles = provider.list_subtitles(reacher_s04e05, {bulgarian})
    assert len(subtitles) == 1
    subtitle = subtitles[0]

    provider.download_subtitle(subtitle)

    # The two calls download_subtitle() must have made, in order:
    # 1) the subtitle detail page, 2) the resolved dl.opensubtitles.org URL.
    urls_called = [r.url for r in requests_mock.request_history[-2:]]
    assert urls_called == [_REACHER_DETAIL_URL, _REACHER_DOWNLOAD_URL]

    assert subtitle.content is not None
    assert subtitle.is_valid()

    decoded = subtitle.content.decode("utf-8")
    assert "00:00:01,000 --> 00:00:03,000" in decoded
    assert decoded.count("-->") == 3  # 3 SRT timecodes in the fixture

    matches = subtitle.get_matches(reacher_s04e05)
    assert {"series", "season", "episode", "imdb_id"}.issubset(matches)
