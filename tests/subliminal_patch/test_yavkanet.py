import io
from zipfile import ZipFile

import pytest
from dogpile.cache.api import NO_VALUE
from requests import HTTPError, Session, Timeout

from subliminal.exceptions import ConfigurationError, ProviderError
from subliminal_patch.providers.yavkanet import YavkaNetProvider
from subzero.language import Language


SEARCH_URL = "https://yavka.net/imdb/tt1160419"
SOLVER_URL = "http://flaresolverr:8191/v1"
CHALLENGE = "<html><title>Just a moment...</title></html>"
USER_AGENT = "FlareSolverr browser User-Agent"


@pytest.fixture
def provider():
    instance = YavkaNetProvider(flaresolverr_url="http://flaresolverr:8191")
    instance.initialize()
    yield instance
    instance.terminate()


@pytest.fixture
def solver_result():
    return {
        "status": "ok",
        "solution": {
            "status": 200,
            "userAgent": USER_AGENT,
            "cookies": [
                {
                    "name": "cf_clearance",
                    "value": "clearance-token",
                    "domain": ".yavka.net",
                    "path": "/",
                    "secure": True,
                },
                {"name": "unrelated", "value": "ignored", "domain": ".example.com"},
            ],
        },
    }


def test_query_reports_cloudflare_block(requests_mock, movies):
    requests_mock.get(
        SEARCH_URL,
        status_code=403,
        text=CHALLENGE,
        headers={"Server": "cloudflare"},
    )
    provider = YavkaNetProvider()
    provider.session = Session()

    with pytest.raises(HTTPError):
        provider.query(Language("bul"), movies["dune"])


@pytest.mark.parametrize("method,status_code", [("GET", 403), ("GET", 503), ("POST", 403)])
def test_request_reuses_solver_browser_session(requests_mock, provider, solver_result, method, status_code):
    requests_mock.register_uri(method, SEARCH_URL, [
        {"status_code": status_code, "text": CHALLENGE, "headers": {"Server": "cloudflare"}},
        {"text": "subtitles"},
    ])
    requests_mock.post(SOLVER_URL, json=solver_result)
    kwargs = {"data": {"id": "123"}, "allow_redirects": False} if method == "POST" else {}

    response = provider._request(method, SEARCH_URL, **kwargs)

    assert response.text == "subtitles"
    assert requests_mock.call_count == 3
    original, solver, retried = requests_mock.request_history
    assert solver.json() == {"cmd": "request.get", "url": SEARCH_URL, "maxTimeout": 60000}
    assert "Cookie" not in solver.headers
    assert retried.headers["User-Agent"] == USER_AGENT
    assert retried.headers["Cookie"] == "cf_clearance=clearance-token"
    assert retried.body == original.body
    assert provider.session.cookies.get("unrelated") is None


def test_request_without_challenge_does_not_use_solver(requests_mock, provider):
    requests_mock.get(SEARCH_URL, text="subtitles")

    assert provider._request("GET", SEARCH_URL).text == "subtitles"
    assert requests_mock.call_count == 1


def test_request_does_not_solve_unrelated_http_error(requests_mock, provider):
    requests_mock.get(SEARCH_URL, status_code=403, text="Forbidden", headers={"Server": "cloudflare"})

    with pytest.raises(HTTPError):
        provider._request("GET", SEARCH_URL)

    assert requests_mock.call_count == 1


def test_request_recognizes_challenge_header(requests_mock, provider, solver_result):
    requests_mock.get(SEARCH_URL, [
        {"status_code": 403, "text": "blocked", "headers": {"cf-mitigated": "challenge"}},
        {"text": "subtitles"},
    ])
    requests_mock.post(SOLVER_URL, json=solver_result)

    assert provider._request("GET", SEARCH_URL).text == "subtitles"


def test_request_does_not_loop_on_rejected_clearance(requests_mock, provider, solver_result):
    requests_mock.get(SEARCH_URL, status_code=403, text=CHALLENGE, headers={"Server": "cloudflare"})
    solver = requests_mock.post(SOLVER_URL, json=solver_result)

    with pytest.raises(HTTPError):
        provider._request("GET", SEARCH_URL)

    assert requests_mock.call_count == 3
    assert solver.call_count == 1


@pytest.mark.parametrize("result", [
    {"status": "error", "message": "Challenge timed out"},
    {"status": "ok", "solution": {"status": 403}},
    {"status": "ok", "solution": {"status": 200, "cookies": []}},
    {"status": "ok", "solution": {"status": 200, "userAgent": USER_AGENT, "cookies": "invalid"}},
    [],
])
def test_solver_failure_is_reported(requests_mock, provider, result):
    requests_mock.get(SEARCH_URL, status_code=403, text=CHALLENGE, headers={"Server": "cloudflare"})
    requests_mock.post(SOLVER_URL, json=result)

    with pytest.raises(ProviderError, match="FlareSolverr could not solve"):
        provider._request("GET", SEARCH_URL)

    assert requests_mock.call_count == 2


def test_solver_invalid_json_is_reported(requests_mock, provider):
    requests_mock.get(SEARCH_URL, status_code=403, text=CHALLENGE, headers={"Server": "cloudflare"})
    requests_mock.post(SOLVER_URL, text="not JSON")

    with pytest.raises(ProviderError, match="FlareSolverr could not solve"):
        provider._request("GET", SEARCH_URL)


def test_solver_http_error_is_reported(requests_mock, provider):
    requests_mock.get(SEARCH_URL, status_code=403, text=CHALLENGE, headers={"Server": "cloudflare"})
    requests_mock.post(SOLVER_URL, status_code=500)

    with pytest.raises(HTTPError):
        provider._request("GET", SEARCH_URL)


def test_retry_reissues_request_on_empty_body(requests_mock, provider, mocker):
    requests_mock.get(SEARCH_URL, [{"content": b""}, {"text": "subtitles"}])
    sleep = mocker.patch("subliminal_patch.providers.yavkanet.time.sleep")

    response = provider.retry(lambda: provider._request("GET", SEARCH_URL), limit=2)

    assert response.text == "subtitles"
    assert requests_mock.call_count == 2
    sleep.assert_called_once_with(5)


@pytest.mark.parametrize("url", ["flaresolverr:8191", "ftp://flaresolverr", "http://flaresolverr/#fragment"])
def test_invalid_solver_url_is_rejected(url):
    with pytest.raises(ConfigurationError, match="FlareSolverr URL"):
        YavkaNetProvider(flaresolverr_url=url)


@pytest.mark.parametrize("url", ["http://flaresolverr:8191", " http://flaresolverr:8191/ ", SOLVER_URL])
def test_solver_url_is_normalized(url):
    assert YavkaNetProvider(flaresolverr_url=url).flaresolverr_url == SOLVER_URL


@pytest.mark.parametrize("blocked_stage", ["search", "details", "download"])
def test_search_and_archive_download_with_challenge(requests_mock, provider, solver_result, movies, mocker,
                                                  blocked_stage):
    cache = mocker.patch("subliminal_patch.providers.yavkanet.region")
    cache.get.return_value = NO_VALUE
    mocker.patch("subliminal_patch.providers.yavkanet.time.sleep")
    subtitle_content = b"1\r\n00:00:01,000 --> 00:00:02,000\r\nDune\r\n"
    archive = io.BytesIO()
    with ZipFile(archive, "w") as archive_file:
        archive_file.writestr("Dune.2021.srt", subtitle_content)

    challenge = {"status_code": 403, "text": CHALLENGE, "headers": {"cf-mitigated": "challenge"}}
    search = {"text": (
        '<table><tr><td><a class="balon" href="/subs/123" '
        'content="Dune release">Dune</a><span>(2021)</span></td></tr></table>'
    )}
    details = {"text": '<form method="POST"><input name="token" value="abc"></form>'}
    download = {"content": archive.getvalue()}
    requests_mock.get(SEARCH_URL, [challenge, search] if blocked_stage == "search" else [search])
    requests_mock.get("https://yavka.net/subs/123", [challenge, details] if blocked_stage == "details" else [details])
    requests_mock.post("https://yavka.net/subs/123/", [challenge, download] if blocked_stage == "download" else [download])
    solver = requests_mock.post(SOLVER_URL, json=solver_result)

    subtitles = provider.list_subtitles(movies["dune"], {Language("bul")})

    assert len(subtitles) == 1
    assert subtitles[0].filename == "Dune.2021.srt"
    assert subtitles[0].year == 2021
    assert subtitles[0].content == subtitle_content.replace(b"\r\n", b"\n")
    assert solver.call_count == 1
    assert requests_mock.request_history[-1].body == "token=abc"
    assert requests_mock.request_history[-1].headers["Cookie"] == "cf_clearance=clearance-token"
    assert requests_mock.request_history[-1].headers["User-Agent"] == USER_AGENT
    cache.set.assert_called_once()
    cache.delete.assert_not_called()

    request_count = requests_mock.call_count
    provider.download_subtitle(subtitles[0])
    assert requests_mock.call_count == request_count


def test_challenge_page_is_not_cached_as_archive(requests_mock, provider, solver_result, movies, mocker):
    cache = mocker.patch("subliminal_patch.providers.yavkanet.region")
    cache.get.return_value = NO_VALUE
    mocker.patch("subliminal_patch.providers.yavkanet.time.sleep")
    requests_mock.post(SEARCH_URL, text=CHALLENGE, headers={"cf-mitigated": "challenge"})
    requests_mock.post(SOLVER_URL, json=solver_result)

    with pytest.raises(ProviderError, match="Cloudflare challenge"):
        provider.download_archive_and_add_subtitle_files(SEARCH_URL, Language("bul"), movies["dune"], None, {})

    cache.set.assert_not_called()


def test_solver_timeout_is_reported(requests_mock, provider):
    requests_mock.get(SEARCH_URL, status_code=403, text=CHALLENGE, headers={"cf-mitigated": "challenge"})
    requests_mock.post(SOLVER_URL, exc=Timeout)

    with pytest.raises(Timeout):
        provider._request("GET", SEARCH_URL)

    assert requests_mock.call_count == 2