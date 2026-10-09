# coding=utf-8
import datetime

import pytest
from babelfish import Language
from requests import Response

from subliminal_patch.converters.subsource import SubsourceConverter
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
