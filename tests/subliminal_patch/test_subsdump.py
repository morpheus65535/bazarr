from unittest.mock import Mock

import pytest
from requests import Session
from requests.exceptions import ConnectionError, SSLError, Timeout
from subliminal.exceptions import AuthenticationError, ConfigurationError, ProviderError
from subliminal_patch.providers import subsdump
from subliminal_patch.providers.subsdump import SubsDumpProvider
from subzero.language import Language

BASE_URL = "https://subsdump.example.com"


def _record(
    *,
    subtitle_id=42,
    title="Dune",
    language="ara",
    media_type="movie",
    year=2021,
    season=None,
    episode=None,
    hearing_impaired=False,
):
    return {
        "id": subtitle_id,
        "media": {
            "type": media_type,
            "title": title,
            "imdb_id": "tt1160419",
            "year": year,
            "season": season,
            "episode": episode,
        },
        "language": {"code": language, "name": "Arabic"},
        "releases": ["Dune.2021.1080p.WEBRip.DD5.1.x264-SHITBOX"],
        "hearing_impaired": hearing_impaired,
        "uploader": "contributor",
        "links": {
            "page": f"/subtitles/{subtitle_id}",
            "archive": f"/api/v1/subtitles/{subtitle_id}/archive",
            "content": f"/api/v1/subtitles/{subtitle_id}/content",
        },
    }


def _provider(api_key=""):
    provider = SubsDumpProvider(BASE_URL, api_key)
    provider.session = Session()
    if api_key:
        provider.session.headers["X-API-Key"] = api_key
    return provider


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "subsdump.example.com",
        "ftp://subsdump.example.com",
        "https://user:secret@subsdump.example.com",
        "https://subsdump.example.com?key=value",
        "https://subsdump.example.com#fragment",
    ],
)
def test_base_url_validation(url):
    with pytest.raises(ConfigurationError):
        SubsDumpProvider(url)


def test_initialize_uses_optional_api_key_and_cleanup(requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/info",
        json={"name": "SubsDump", "version": "2.1.0", "api_version": "v1"},
    )
    provider = SubsDumpProvider(f"{BASE_URL}/", "api-secret")

    provider.initialize()

    assert provider.base_url == BASE_URL
    assert requests_mock.last_request.headers["X-API-Key"] == "api-secret"
    assert provider.session is not None
    provider.terminate()
    assert provider.session is None


def test_initialize_without_api_key(requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/info",
        json={"name": "SubsDump", "version": "2.1.0", "api_version": "v1"},
    )
    provider = SubsDumpProvider(BASE_URL)

    provider.initialize()

    assert "X-API-Key" not in requests_mock.last_request.headers
    provider.terminate()


def test_initialize_rejects_an_incompatible_service_and_closes_session(monkeypatch):
    response = Mock(status_code=200, content=b"{}")
    response.json.return_value = {"name": "Another service", "api_version": "v1"}
    session = Mock(headers={})
    session.get.return_value = response
    monkeypatch.setattr(subsdump, "Session", lambda: session)
    provider = SubsDumpProvider(BASE_URL)

    with pytest.raises(ConfigurationError, match="SubsDump v1 API"):
        provider.initialize()

    session.close.assert_called_once_with()
    assert provider.session is None


def test_movie_lookup_returns_matches_and_page_link(movies, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles",
        json={"subtitles": [_record()]},
    )
    provider = _provider()

    results = provider.list_subtitles(movies["dune"], {Language("ara")})

    assert len(results) == 1
    subtitle = results[0]
    assert subtitle.provider_name == "subsdump"
    assert subtitle.page_link == f"{BASE_URL}/subtitles/42"
    assert subtitle.content_path == "/api/v1/subtitles/42/content"
    assert subtitle.release_info == "Dune.2021.1080p.WEBRip.DD5.1.x264-SHITBOX"
    assert subtitle.uploader == "contributor"
    assert {"title", "year", "release_group"}.issubset(
        subtitle.get_matches(movies["dune"])
    )
    assert requests_mock.last_request.qs["language"] == ["ara"]


def test_episode_lookup_maps_season_episode_and_release(episodes, requests_mock):
    record = _record(
        title="Game of Thrones",
        media_type="episode",
        year=None,
        season=3,
        episode=10,
    )
    requests_mock.get(
        f"{BASE_URL}/api/v1/series/tt0944947/seasons/3/episodes/10/subtitles",
        json={"subtitles": [record]},
    )
    provider = _provider()

    results = provider.list_subtitles(episodes["got_s03e10"], {Language("ara")})

    assert len(results) == 1
    assert {"series", "season", "episode"}.issubset(
        results[0].get_matches(episodes["got_s03e10"])
    )
    assert requests_mock.last_request.qs["release"] == [
        "game.of.thrones.s03e10.mhysa.720p.web-dl.dd5.1.h.264-ntb.mkv"
    ]


def test_title_fallback_for_episode_without_imdb_id(episodes, requests_mock):
    requests_mock.get(f"{BASE_URL}/api/v1/subtitles", json={"subtitles": []})
    provider = _provider()

    assert provider.list_subtitles(
        episodes["better_call_saul_s06e04"], {Language("ara")}
    ) == []
    assert requests_mock.last_request.qs["title"] == ["better call saul"]
    assert requests_mock.last_request.qs["media_type"] == ["episode"]
    assert requests_mock.last_request.qs["season"] == ["6"]
    assert requests_mock.last_request.qs["episode"] == ["4"]


def test_language_mapping_and_hearing_impaired_metadata(movies, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles",
        json={"subtitles": [_record(language="por-BR", hearing_impaired=True)]},
    )
    provider = _provider()

    results = provider.list_subtitles(movies["dune"], {Language("por", "BR", hi=True)})

    assert len(results) == 1
    assert results[0].language == Language("por", "BR", hi=True)
    assert results[0].hearing_impaired is True
    assert requests_mock.last_request.qs["language"] == ["por-br"]


def test_no_results(movies, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles",
        json={"subtitles": []},
    )
    assert _provider().list_subtitles(movies["dune"], {Language("ara")}) == []


def test_malformed_json(movies, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles", text="not JSON"
    )
    with pytest.raises(ProviderError, match="malformed JSON"):
        _provider().list_subtitles(movies["dune"], {Language("ara")})


@pytest.mark.parametrize("status_code", [404, 500])
def test_search_http_error(movies, requests_mock, status_code):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles", status_code=status_code
    )
    with pytest.raises(ProviderError, match=f"HTTP {status_code}"):
        _provider().list_subtitles(movies["dune"], {Language("ara")})


def test_malformed_subtitle_record_is_ignored(movies, requests_mock):
    record = _record()
    record["links"]["page"] = "/subtitles/different"
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles",
        json={"subtitles": [record]},
    )
    assert _provider().list_subtitles(movies["dune"], {Language("ara")}) == []


def test_invalid_authentication(movies, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles", status_code=401
    )
    with pytest.raises(AuthenticationError, match="API key"):
        _provider("wrong-key").list_subtitles(movies["dune"], {Language("ara")})


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (Timeout(), "timed out"),
        (ConnectionError(), "unreachable"),
        (SSLError(), "TLS verification"),
    ],
)
def test_remote_request_errors(movies, requests_mock, error, message):
    requests_mock.get(
        f"{BASE_URL}/api/v1/movies/tt1160419/subtitles", exc=error
    )
    with pytest.raises(ProviderError, match=message):
        _provider().list_subtitles(movies["dune"], {Language("ara")})


def test_download_uses_native_content_endpoint(requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/subtitles/42/content",
        content=b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello\r\n",
    )
    provider = _provider("api-secret")
    subtitle = Mock(content_path="/api/v1/subtitles/42/content", content=None)

    provider.download_subtitle(subtitle)

    assert subtitle.content == b"1\n00:00:01,000 --> 00:00:02,000\nHello\n"
    assert requests_mock.last_request.headers["X-API-Key"] == "api-secret"


@pytest.mark.parametrize(
    ("status_code", "exception", "message"),
    [
        (401, AuthenticationError, "API key"),
        (404, ProviderError, "HTTP 404"),
        (500, ProviderError, "HTTP 500"),
    ],
)
def test_download_http_errors(requests_mock, status_code, exception, message):
    requests_mock.get(
        f"{BASE_URL}/api/v1/subtitles/42/content", status_code=status_code
    )
    provider = _provider("api-secret")
    subtitle = Mock(content_path="/api/v1/subtitles/42/content", content=None)

    with pytest.raises(exception, match=message):
        provider.download_subtitle(subtitle)


def test_download_rejects_empty_content(requests_mock):
    requests_mock.get(f"{BASE_URL}/api/v1/subtitles/42/content", content=b"")
    provider = _provider()
    subtitle = Mock(content_path="/api/v1/subtitles/42/content", content=None)

    with pytest.raises(ProviderError, match="invalid subtitle file"):
        provider.download_subtitle(subtitle)


def test_download_timeout(requests_mock):
    requests_mock.get(
        f"{BASE_URL}/api/v1/subtitles/42/content", exc=Timeout()
    )
    provider = _provider()
    subtitle = Mock(content_path="/api/v1/subtitles/42/content", content=None)

    with pytest.raises(ProviderError, match="download timed out"):
        provider.download_subtitle(subtitle)
