# coding=utf-8
import datetime
import json
import math

import pytest
from babelfish import Language
from requests import Response
from subzero.language import Language as SubzeroLanguage

from subliminal_patch.converters.subsource import SubsourceConverter
from subliminal_patch.core import Movie
from subliminal_patch.exceptions import TooManyRequests
from subliminal_patch.providers.subsource import MAX_INLINE_WAIT, SubsourceProvider


def test_convert_brazilian_portuguese():
    # pt-BR must map to the Brazilian name, not generic Portuguese. The mapping is
    # stored under the two-tuple key ('por', 'BR'), so convert() must look it up.
    converter = SubsourceConverter()
    language = Language("por", "BR")
    assert converter.convert(language.alpha3, language.country, language.script) == "Brazillian Portuguese"


def test_convert_plain_portuguese_still_works():
    converter = SubsourceConverter()
    assert converter.convert("por") == "Portuguese"


def test_convert_brazilian_portuguese_round_trip():
    converter = SubsourceConverter()
    assert converter.convert(*converter.reverse("Brazillian Portuguese")) == "Brazillian Portuguese"


def _rate_limited(body=b"", reset_in=None):
    """A 429 as the API sends it: X-RateLimit-* headers, and retryAfter in the body."""
    response = Response()
    response.status_code = 429
    response._content = body
    if reset_in is not None:
        reset_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=reset_in)
        response.headers["X-RateLimit-Reset"] = reset_at.isoformat().replace("+00:00", "Z")
    return response


def test_retry_after_prefers_the_reset_header():
    # the header is authoritative: it stays right however long the response waited
    response = _rate_limited(body=b'{"retryAfter": 3}', reset_in=26)
    assert SubsourceProvider._retry_after(response) == 26


@pytest.mark.parametrize("body", [b"<html>too many requests</html>", b"", b"[1, 2]", b'{"retryAfter": "26"}'])
def test_retry_after_is_none_when_the_server_does_not_say(body):
    # a 429 from the CDN in front of the API carries neither the headers nor the body
    assert SubsourceProvider._retry_after(_rate_limited(body=body)) is None


def test_retry_after_is_never_zero():
    # the server still refusing past its own reset must not be retried with no delay at all
    assert SubsourceProvider._retry_after(_rate_limited(reset_in=-5)) == 1


@pytest.fixture
def _provider(monkeypatch):
    """`checked` sleeps out short rate limits, which no test should actually wait for."""
    monkeypatch.setattr("subliminal_patch.providers.subsource.time.sleep", lambda seconds: None)
    return SubsourceProvider(api_key="key")


def _responses(*responses):
    """A callable standing in for a request, answering with each response in turn."""
    remaining = list(responses)
    return lambda: remaining.pop(0)


def test_checked_waits_out_a_rate_limit_that_resets_within_the_minute(_provider):
    ok = Response()
    ok.status_code = 200
    fn = _responses(_rate_limited(reset_in=MAX_INLINE_WAIT), ok)

    assert _provider.checked(fn) is ok


def test_checked_throttles_on_a_rate_limit_that_outlasts_the_minute(_provider):
    # an hour or day quota is gone, so waiting it out would stall the search for that long
    fn = _responses(_rate_limited(reset_in=MAX_INLINE_WAIT + 1))

    with pytest.raises(TooManyRequests):
        _provider.checked(fn)


def test_checked_throttles_when_the_server_reports_no_delay(_provider):
    with pytest.raises(TooManyRequests):
        _provider.checked(_responses(_rate_limited()))


def test_checked_waits_only_once(_provider):
    # a server refusing again right after its own reset is not going to yield to more waiting
    fn = _responses(_rate_limited(reset_in=5), _rate_limited(reset_in=5))

    with pytest.raises(TooManyRequests):
        _provider.checked(fn)


def _subsource_item(subtitle_id, language, release, commentary=""):
    """A subtitle entry as the `subtitles` endpoint returns it."""
    return {
        "subtitleId": subtitle_id,
        "language": language,
        "releaseInfo": [release],
        "link": f"/subtitles/{subtitle_id}",
        "uploaderId": 1,
        "contributors": [{"id": 1, "displayname": "uploader"}],
        "commentary": commentary,
        "foreignParts": False,
        "hearingImpaired": False,
    }


def _json_response(payload):
    response = Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode()
    return response


def _fake_subtitles_api(monkeypatch, provider, items_by_language):
    """Answers `subtitles` calls like the API: comma-separated languages, paged by page and limit.

    Returns the list of `(language, page)` pairs requested, in order.
    """
    requested = []

    def fake_get(url, params=None, timeout=None):
        params = dict(params)
        requested.append((params["language"], params.get("page", 1)))
        items = [item for name in params["language"].split(",") for item in items_by_language.get(name, [])]
        size, page = params["limit"], params.get("page", 1)
        chunk = items[(page - 1) * size:page * size]
        pages = max(1, math.ceil(len(items) / size))
        return _json_response({
            "success": True,
            "data": chunk,
            "pagination": {"page": page, "limit": size, "total": len(items), "pages": pages},
        })

    monkeypatch.setattr(provider.session, "get", fake_get)
    return requested


@pytest.fixture
def _query_provider(monkeypatch):
    provider = SubsourceProvider(api_key="key")
    provider.search_titles = lambda *args, **kwargs: 99
    data = {
        "english": [
            _subsource_item(1, "english", "BluRay"),
            _subsource_item(2, "english", "WEB", commentary="SDH"),
        ],
        "spanish": [_subsource_item(10, "spanish", "BluRay")],
    }
    requested = _fake_subtitles_api(monkeypatch, provider, data)
    return provider, requested


def test_query_requests_every_language_in_one_call(_query_provider):
    # the API takes comma-separated languages, so one call covers the whole set
    provider, requested = _query_provider
    video = Movie("Movie.2020.1080p.mkv", "Movie", year=2020, imdb_id="tt1234567")
    languages = {SubzeroLanguage("eng"), SubzeroLanguage("spa")}

    subtitles = SubsourceProvider.query.original(provider, languages, video)

    assert requested == [("english,spanish", 1)]
    assert {subtitle.id for subtitle in subtitles} == {1, 2, 10}


def test_query_requests_a_language_once_when_its_variants_are_requested(_query_provider):
    # forced and HI variants share one API language, so the language is requested once and each subtitle is kept once
    provider, requested = _query_provider
    video = Movie("Movie.2020.1080p.mkv", "Movie", year=2020, imdb_id="tt1234567")
    languages = {SubzeroLanguage("eng"), SubzeroLanguage.rebuild(SubzeroLanguage("eng"), hi=True)}

    subtitles = SubsourceProvider.query.original(provider, languages, video)

    assert requested == [("english", 1)]
    assert sorted(subtitle.id for subtitle in subtitles) == [1, 2]


def test_query_follows_pages_until_the_last_one(monkeypatch):
    # 150 results at 100 per page need a second page, and no page beyond the reported count
    provider = SubsourceProvider(api_key="key")
    provider.search_titles = lambda *args, **kwargs: 99
    items = [_subsource_item(i, "english", "BluRay") for i in range(1, 151)]
    requested = _fake_subtitles_api(monkeypatch, provider, {"english": items})
    video = Movie("Movie.2020.1080p.mkv", "Movie", year=2020, imdb_id="tt1234567")

    subtitles = SubsourceProvider.query.original(provider, {SubzeroLanguage("eng")}, video)

    assert requested == [("english", 1), ("english", 2)]
    assert len(subtitles) == 150


def _archive_response(payload: bytes) -> Response:
    response = Response()
    response.status_code = 200
    response._content = payload
    return response


def test_download_subtitle_extracts_zip_archive(_provider, monkeypatch):
    import io
    import types
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('movie.srt', b'1\n00:00:01,000 --> 00:00:02,000\nhi\n')
    seen = []
    monkeypatch.setattr(_provider, '_get_subtitles_archive', lambda link: _archive_response(buffer.getvalue()))
    monkeypatch.setattr(_provider, 'get_subtitle_from_archive', lambda subtitle, archive: seen.append(type(archive)) or b'ok')

    subtitle = types.SimpleNamespace(id=1, content=None)
    _provider.download_subtitle(subtitle)

    assert seen == [zipfile.ZipFile]
    assert subtitle.content == b'ok'


def test_download_subtitle_extracts_rar_archive(_provider, monkeypatch):
    import types
    import subliminal_patch.providers.subsource as subsource

    opened = []

    class FakeRarFile:
        def __init__(self, stream):
            opened.append(stream)

    monkeypatch.setattr(subsource, 'is_rarfile', lambda stream: True)
    monkeypatch.setattr(subsource, 'RarFile', FakeRarFile)
    monkeypatch.setattr(_provider, '_get_subtitles_archive', lambda link: _archive_response(b'Rar!\x1a\x07\x01\x00'))
    monkeypatch.setattr(_provider, 'get_subtitle_from_archive', lambda subtitle, archive: b'from-rar' if isinstance(archive, FakeRarFile) else None)

    subtitle = types.SimpleNamespace(id=2, content=None)
    _provider.download_subtitle(subtitle)

    assert len(opened) == 1
    assert subtitle.content == b'from-rar'


def test_download_subtitle_rar_error_fails_only_that_subtitle(_provider, monkeypatch):
    import types
    import rarfile
    import subliminal_patch.providers.subsource as subsource

    class FakeRarFile:
        def __init__(self, stream):
            pass

    def broken(subtitle, archive):
        raise rarfile.BadRarFile('corrupt')

    monkeypatch.setattr(subsource, 'is_rarfile', lambda stream: True)
    monkeypatch.setattr(subsource, 'RarFile', FakeRarFile)
    monkeypatch.setattr(_provider, '_get_subtitles_archive', lambda link: _archive_response(b'Rar!\x1a\x07\x01\x00'))
    monkeypatch.setattr(_provider, 'get_subtitle_from_archive', broken)

    subtitle = types.SimpleNamespace(id=3, content=b'stale')
    _provider.download_subtitle(subtitle)

    assert subtitle.content is None


def test_download_subtitle_rejects_unknown_payload(_provider, monkeypatch):
    import types
    import subliminal_patch.providers.subsource as subsource

    monkeypatch.setattr(subsource, 'is_rarfile', lambda stream: False)
    monkeypatch.setattr(_provider, '_get_subtitles_archive', lambda link: _archive_response(b'<html>nope</html>'))

    subtitle = types.SimpleNamespace(id=4, content=b'stale')
    _provider.download_subtitle(subtitle)

    assert subtitle.content is None
