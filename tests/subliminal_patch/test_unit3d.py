import io
import logging
import zipfile

import pytest
from requests import Session
from requests.exceptions import ConnectionError, Timeout
from subliminal.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ProviderError,
    ServiceUnavailable,
)
from subliminal_patch.core import Movie
from subliminal_patch.exceptions import ForbiddenError, TooManyRequests
from subliminal_patch.providers import unit3d
from subliminal_patch.providers.unit3d import Unit3dProvider, check_connection
from subzero.language import Language

BASE_URL = "https://tracker.example.com"
API_KEY = "s3cr3t-unit3d-api-key-0123456789"
STATUS_URL = f"{BASE_URL}/api/subtitles/status"
SEARCH_URL = f"{BASE_URL}/api/subtitles"
RELEASE = "The.Shawshank.Redemption.1994.1080p.BluRay.x264-GRP"
SRT = b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello\r\n"


@pytest.fixture(autouse=True)
def plain_session(monkeypatch):
    # Bazarr injects a retrying session into providers; retries only slow the tests down
    monkeypatch.setattr(unit3d, "Session", Session)


@pytest.fixture
def provider():
    provider = Unit3dProvider(f"{BASE_URL}/", API_KEY)
    provider.initialize()
    yield provider
    provider.terminate()


@pytest.fixture
def video():
    movie = Movie(
        f"{RELEASE}.mkv",
        "The Shawshank Redemption",
        year=1994,
        source="Blu-ray",
        resolution="1080p",
        video_codec="H.264",
        release_group="GRP",
        imdb_id="tt0111161",
    )
    # Set by Bazarr's database refiner, like in production
    movie.tmdb_id = 278
    return movie


def _record(subtitle_id=123, language="en", **overrides):
    return {
        "id": subtitle_id,
        "language": language,
        "language_name": "English",
        "extension": "srt",
        "filename": f"[English.Subtitle]{RELEASE}.srt",
        "size": 12345,
        "downloads": 42,
        "forced": None,
        "hearing_impaired": None,
        "torrent_id": 456,
        "release": RELEASE,
        "tmdb_id": 278,
        "imdb_id": "tt0111161",
        "created_at": "2025-01-01T00:00:00+00:00",
        "download_url": f"/api/subtitles/{subtitle_id}/download",
        **overrides,
    }


def _search_response(records, matched_by="tmdb", total=None):
    return {
        "data": records,
        "meta": {"matched_by": matched_by, "total": len(records) if total is None else total},
    }


def _zip(name, content):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(name, content)
    return stream.getvalue()


# Configuration


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "tracker.example.com",
        "ftp://tracker.example.com",
        "https://user:secret@tracker.example.com",
        "https://tracker.example.com?key=value",
        "https://tracker.example.com#fragment",
    ],
)
def test_url_validation(url):
    with pytest.raises(ConfigurationError):
        Unit3dProvider(url, API_KEY)


@pytest.mark.parametrize("api_key", [None, ""])
def test_api_key_is_required(api_key):
    with pytest.raises(ConfigurationError, match="API key is required"):
        Unit3dProvider(BASE_URL, api_key)


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://tracker.example.com", "https://tracker.example.com"),
        ("https://tracker.example.com/", "https://tracker.example.com"),
        (" https://tracker.example.com// ", "https://tracker.example.com"),
        ("http://10.0.0.2:8000/unit3d/", "http://10.0.0.2:8000/unit3d"),
    ],
)
def test_url_normalization(url, expected):
    assert Unit3dProvider(url, API_KEY).base_url == expected


def test_trailing_slash_does_not_create_double_slash(requests_mock, provider):
    requests_mock.get(STATUS_URL, json={"status": "ok", "provider": "unit3d", "version": "v9.2.0"})

    provider.status()

    assert requests_mock.last_request.url == STATUS_URL


def test_initialize_sets_auth_headers_and_terminate_cleans_up():
    provider = Unit3dProvider(BASE_URL, API_KEY)
    provider.initialize()

    assert provider.session.headers["Authorization"] == f"Bearer {API_KEY}"
    assert provider.session.headers["Accept"] == "application/json"

    provider.terminate()
    assert provider.session is None


def test_uninitialized_provider_raises():
    with pytest.raises(ProviderError, match="not initialized"):
        Unit3dProvider(BASE_URL, API_KEY).status()


# Connection test / status


def test_check_connection_success(requests_mock):
    requests_mock.get(
        STATUS_URL,
        json={"status": "ok", "provider": "unit3d", "version": "v9.2.0", "api_version": 1},
    )

    assert check_connection(f"{BASE_URL}/", API_KEY) == {"status": True, "version": "UNIT3D v9.2.0"}
    request = requests_mock.last_request
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert request.headers["Accept"] == "application/json"
    assert API_KEY not in request.url


@pytest.mark.parametrize(
    "permissions, message",
    [
        ({"search": False, "download": True}, "missing the search permission"),
        ({"search": True, "download": False}, "missing the download permission"),
        ({"search": False, "download": False}, "missing the search and download permission"),
    ],
)
def test_check_connection_requires_permissions(requests_mock, permissions, message):
    requests_mock.get(
        STATUS_URL,
        json={"status": "ok", "provider": "unit3d", "version": "v9.2.0", "permissions": permissions},
    )

    result = check_connection(BASE_URL, API_KEY)

    assert result == {"status": False, "error": f"UNIT3D API key is {message}"}


def test_check_connection_with_permissions(requests_mock):
    requests_mock.get(
        STATUS_URL,
        json={
            "status": "ok",
            "provider": "unit3d",
            "version": "v9.2.0",
            "permissions": {"search": True, "download": True},
        },
    )

    assert check_connection(BASE_URL, API_KEY) == {"status": True, "version": "UNIT3D v9.2.0"}


@pytest.mark.parametrize(
    "response, message",
    [
        ({"status_code": 401, "json": {"message": "Unauthenticated."}}, "rejected the API key"),
        ({"status_code": 403, "json": {}}, "denied access"),
        ({"status_code": 404, "text": "Not Found"}, "does not provide the subtitle API"),
        ({"status_code": 429, "json": {}}, "rate limit"),
        ({"status_code": 500, "text": "Server Error"}, "HTTP 500"),
        ({"status_code": 503, "text": "Maintenance"}, "HTTP 503"),
        ({"status_code": 302, "headers": {"Location": "https://evil.example.com"}}, "redirected"),
        ({"status_code": 200, "text": "<html>"}, "malformed JSON"),
        ({"status_code": 200, "json": ["unexpected"]}, "unexpected response"),
        ({"status_code": 200, "json": {"status": "ok", "provider": "other"}}, "does not provide"),
        ({"status_code": 200, "json": {"message": "You are banned"}}, "refused the request"),
        ({"exc": Timeout}, "timed out"),
        ({"exc": ConnectionError}, "unreachable"),
    ],
)
def test_check_connection_failures(requests_mock, response, message):
    requests_mock.get(STATUS_URL, **response)

    result = check_connection(BASE_URL, API_KEY)

    assert result["status"] is False
    assert message in result["error"]
    assert API_KEY not in result["error"]


@pytest.mark.parametrize(
    "url, api_key, message",
    [
        ("", API_KEY, "URL is required"),
        ("tracker.example.com", API_KEY, "must begin with http"),
        (BASE_URL, "", "API key is required"),
    ],
)
def test_check_connection_configuration_errors(requests_mock, url, api_key, message):
    result = check_connection(url, api_key)

    assert result["status"] is False
    assert message in result["error"]
    assert not requests_mock.called


def test_redirects_are_not_followed(requests_mock, provider):
    requests_mock.get(STATUS_URL, status_code=301, headers={"Location": "http://evil.example.com/steal"})
    requests_mock.get("http://evil.example.com/steal", json={"status": "ok", "provider": "unit3d"})

    with pytest.raises(ConfigurationError, match="redirected"):
        provider.status()

    assert requests_mock.call_count == 1


def test_ping(requests_mock, provider):
    requests_mock.get(STATUS_URL, [{"json": {"status": "ok", "provider": "unit3d"}}, {"status_code": 401}])

    assert provider.ping() is True
    assert provider.ping() is False


# Search


def test_search_by_tmdb_id(requests_mock, provider, video):
    requests_mock.get(SEARCH_URL, json=_search_response([_record()]))

    subtitles = provider.list_subtitles(video, {Language("eng")})

    assert len(subtitles) == 1
    assert requests_mock.last_request.qs == {
        "tmdb_id": ["278"],
        "imdb_id": ["tt0111161"],
        "language": ["en"],
        "perpage": ["50"],
    }


def test_search_by_imdb_id_when_tmdb_id_is_unknown(requests_mock, provider, video):
    video.tmdb_id = None
    requests_mock.get(SEARCH_URL, json=_search_response([_record(tmdb_id=None)], matched_by="imdb"))

    subtitles = provider.list_subtitles(video, {Language("eng")})

    assert len(subtitles) == 1
    qs = requests_mock.last_request.qs
    assert qs["imdb_id"] == ["tt0111161"]
    assert "tmdb_id" not in qs and "title" not in qs
    assert "imdb_id" in subtitles[0].matches


def test_search_by_title_and_year_when_no_id_is_known(requests_mock, provider, video):
    video.tmdb_id = None
    video.imdb_id = None
    requests_mock.get(SEARCH_URL, json=_search_response([_record()], matched_by="title"))

    subtitles = provider.list_subtitles(video, {Language("eng")})

    assert len(subtitles) == 1
    qs = requests_mock.last_request.qs
    assert qs["title"] == ["the shawshank redemption"]
    assert qs["year"] == ["1994"]
    assert "tmdb_id" not in qs and "imdb_id" not in qs
    assert {"title", "year"} <= subtitles[0].matches


def test_search_never_uses_title_when_an_id_is_known(requests_mock, provider, video):
    video.imdb_id = None
    requests_mock.get(SEARCH_URL, json=_search_response([]))

    provider.list_subtitles(video, {Language("eng")})

    assert "title" not in requests_mock.last_request.qs


@pytest.mark.parametrize("tmdb_id, imdb_id", [(0, "tt0000000"), ("", "0111161"), (None, "tt")])
def test_search_ignores_invalid_ids(requests_mock, provider, video, tmdb_id, imdb_id):
    video.tmdb_id = tmdb_id
    video.imdb_id = imdb_id
    requests_mock.get(SEARCH_URL, json=_search_response([], matched_by="title"))

    provider.list_subtitles(video, {Language("eng")})

    qs = requests_mock.last_request.qs
    assert "tmdb_id" not in qs and "imdb_id" not in qs
    assert qs["year"] == ["1994"]


def test_search_is_skipped_without_identifiers(requests_mock, provider, video):
    video.tmdb_id = None
    video.imdb_id = None
    video.year = None

    assert provider.list_subtitles(video, {Language("eng")}) == []
    assert not requests_mock.called


def test_search_requests_all_languages_at_once(requests_mock, provider, video):
    requests_mock.get(
        SEARCH_URL,
        json=_search_response([_record(1, "en"), _record(2, "fr"), _record(3, "de")]),
    )

    subtitles = provider.list_subtitles(video, {Language("eng"), Language("fra")})

    assert requests_mock.call_count == 1
    assert requests_mock.last_request.qs["language"] == ["en,fr"]
    # Records in languages that were not requested are ignored
    assert sorted(str(subtitle.language) for subtitle in subtitles) == ["en", "fr"]


def test_search_does_not_confuse_portuguese_variants(requests_mock, provider, video):
    requests_mock.get(SEARCH_URL, json=_search_response([_record(language="pt")]))

    assert provider.list_subtitles(video, {Language("por", "BR")}) == []
    assert not requests_mock.called

    subtitles = provider.list_subtitles(video, {Language("por")})
    assert requests_mock.last_request.qs["language"] == ["pt"]
    assert subtitles[0].language == Language("por")


@pytest.mark.parametrize(
    "alpha3, code",
    [
        ("eng", "en"), ("spa", "es"), ("fra", "fr"), ("deu", "de"), ("ita", "it"),
        ("por", "pt"), ("nld", "nl"), ("pol", "pl"), ("tur", "tr"), ("rus", "ru"),
        ("jpn", "ja"), ("kor", "ko"), ("zho", "zh"), ("ara", "ar"),
    ],
)
def test_language_mapping(requests_mock, provider, video, alpha3, code):
    requests_mock.get(SEARCH_URL, json=_search_response([_record(language=code)]))

    subtitles = provider.list_subtitles(video, {Language(alpha3)})

    assert requests_mock.last_request.qs["language"] == [code]
    assert subtitles[0].language == Language(alpha3)


def test_search_with_no_results(requests_mock, provider, video):
    requests_mock.get(SEARCH_URL, json=_search_response([]))

    assert provider.list_subtitles(video, {Language("eng")}) == []


def test_search_with_multiple_results(requests_mock, provider, video):
    requests_mock.get(
        SEARCH_URL,
        json=_search_response(
            [
                _record(1, release=RELEASE),
                _record(2, release="The.Shawshank.Redemption.1994.720p.WEB-DL.DD5.1.H.264-OTHER"),
            ],
            total=70,
        ),
    )

    subtitles = provider.list_subtitles(video, {Language("eng")})

    assert [subtitle.id for subtitle in subtitles] == ["unit3d_1", "unit3d_2"]
    assert {"resolution", "release_group", "source"} <= subtitles[0].matches
    assert "resolution" not in subtitles[1].matches


def test_search_skips_other_movies_and_malformed_records(requests_mock, provider, video):
    requests_mock.get(
        SEARCH_URL,
        json=_search_response(
            [
                _record(1),
                _record(2, tmdb_id=680, imdb_id="tt0110912"),
                _record(3, extension="sup"),
                _record(4, id="4"),
                _record(5, release=None),
                "garbage",
            ]
        ),
    )

    subtitles = provider.list_subtitles(video, {Language("eng")})

    assert [subtitle.subtitle_id for subtitle in subtitles] == [1]


@pytest.mark.parametrize(
    "response, error",
    [
        ({"status_code": 401}, AuthenticationError),
        ({"status_code": 403}, ForbiddenError),
        ({"status_code": 404}, ConfigurationError),
        ({"status_code": 422, "json": {"message": "invalid"}}, ProviderError),
        ({"status_code": 429}, TooManyRequests),
        ({"status_code": 500}, ServiceUnavailable),
        ({"status_code": 200, "json": {"meta": {}}}, ProviderError),
        ({"exc": Timeout}, ProviderError),
    ],
)
def test_search_errors(requests_mock, provider, video, response, error):
    requests_mock.get(SEARCH_URL, **response)

    with pytest.raises(error):
        provider.list_subtitles(video, {Language("eng")})


# Subtitle mapping


def test_subtitle_mapping(requests_mock, provider, video):
    requests_mock.get(SEARCH_URL, json=_search_response([_record(extension="ASS")]))

    subtitle = provider.list_subtitles(video, {Language("eng")})[0]

    assert subtitle.id == "unit3d_123"
    assert subtitle.language == Language("eng")
    assert subtitle.filename == f"[English.Subtitle]{RELEASE}.srt"
    assert subtitle.extension == "ass"
    assert subtitle.release_info == RELEASE
    assert subtitle.hearing_impaired is False
    assert subtitle.language.hi is False
    assert subtitle.language.forced is False
    assert {"title", "year", "source", "resolution", "release_group"} <= subtitle.matches
    assert subtitle.format == "srt"
    subtitle.use_original_format = True
    assert subtitle.format == "ass"


def test_subtitle_mapping_respects_explicit_flags(requests_mock, provider, video):
    requests_mock.get(
        SEARCH_URL,
        json=_search_response([_record(1, forced=True), _record(2, hearing_impaired=True)]),
    )

    forced, hearing_impaired = provider.list_subtitles(video, {Language("eng")})

    assert forced.language.forced is True
    assert forced.hearing_impaired is False
    assert hearing_impaired.hearing_impaired is True
    assert hearing_impaired.language.hi is True


# Download


def _subtitle(requests_mock, provider, video, **overrides):
    requests_mock.get(SEARCH_URL, json=_search_response([_record(**overrides)]))
    return provider.list_subtitles(video, {Language("eng")})[0]


def test_download(requests_mock, provider, video):
    subtitle = _subtitle(
        requests_mock, provider, video, download_url="https://evil.example.com/steal"
    )
    requests_mock.get(
        f"{BASE_URL}/api/subtitles/123/download",
        content=SRT,
        headers={"Content-Type": "application/x-subrip"},
    )

    provider.download_subtitle(subtitle)

    # The download location is built from the id, never taken from the response
    assert requests_mock.last_request.url == f"{BASE_URL}/api/subtitles/123/download"
    assert requests_mock.last_request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert subtitle.content == SRT.replace(b"\r\n", b"\n")
    assert subtitle.is_valid()


def test_download_extracts_zip_archives(requests_mock, provider, video):
    subtitle = _subtitle(requests_mock, provider, video, extension="zip")
    requests_mock.get(
        f"{BASE_URL}/api/subtitles/123/download",
        content=_zip("Movie.English.srt", SRT),
        headers={"Content-Type": "application/zip"},
    )

    provider.download_subtitle(subtitle)

    assert subtitle.content == SRT.replace(b"\r\n", b"\n")


@pytest.mark.parametrize(
    "response, error, message",
    [
        ({"status_code": 401}, AuthenticationError, "rejected the API key"),
        ({"status_code": 403, "json": {"message": "revoked"}}, ForbiddenError, "denied access"),
        ({"status_code": 404}, ProviderError, "no longer available"),
        ({"status_code": 500}, ServiceUnavailable, "HTTP 500"),
        ({"status_code": 200, "content": b""}, ProviderError, "invalid subtitle file"),
        (
            {
                "status_code": 200,
                "json": {"message": "You are banned"},
                "headers": {"Content-Type": "application/json"},
            },
            ForbiddenError,
            "refused the download",
        ),
    ],
)
def test_download_errors(requests_mock, provider, video, response, error, message):
    subtitle = _subtitle(requests_mock, provider, video)
    requests_mock.get(f"{BASE_URL}/api/subtitles/123/download", **response)

    with pytest.raises(error, match=message):
        provider.download_subtitle(subtitle)
    assert subtitle.content is None


def test_download_rejects_invalid_archives(requests_mock, provider, video):
    subtitle = _subtitle(requests_mock, provider, video, extension="zip")
    requests_mock.get(f"{BASE_URL}/api/subtitles/123/download", content=b"not a zip file")

    with pytest.raises(ProviderError, match="invalid subtitle archive"):
        provider.download_subtitle(subtitle)


# Security


def test_api_key_is_never_logged_or_exposed(requests_mock, provider, video, caplog):
    caplog.set_level(logging.DEBUG)
    requests_mock.get(STATUS_URL, json={"status": "ok", "provider": "unit3d"})
    requests_mock.get(SEARCH_URL, json=_search_response([_record()]))
    requests_mock.get(f"{BASE_URL}/api/subtitles/123/download", content=SRT)

    provider.status()
    subtitle = provider.list_subtitles(video, {Language("eng")})[0]
    provider.download_subtitle(subtitle)

    errors = []
    for status_code in (401, 403, 404, 500):
        requests_mock.get(SEARCH_URL, status_code=status_code)
        requests_mock.get(f"{BASE_URL}/api/subtitles/123/download", status_code=status_code)
        for call in (
            lambda: provider.list_subtitles(video, {Language("eng")}),
            lambda: provider.download_subtitle(subtitle),
        ):
            with pytest.raises(ProviderError) as error:
                call()
            errors.append(error.value)
    for exception in (Timeout, ConnectionError):
        requests_mock.get(SEARCH_URL, exc=exception(f"failed {SEARCH_URL}"))
        with pytest.raises(ProviderError) as error:
            provider.list_subtitles(video, {Language("eng")})
        errors.append(error.value)

    check_connection(BASE_URL, API_KEY)

    assert API_KEY not in caplog.text
    assert "Authorization" not in caplog.text
    for error in errors:
        assert API_KEY not in str(error)
        assert API_KEY not in repr(error)
    for request in requests_mock.request_history:
        assert API_KEY not in request.url
    assert API_KEY not in repr(provider)
