import json

import pytest
import requests

from radarr.movie_snapshot import FileState, IncompleteMovie, Movie
from radarr.sync.utils import MOVIE_DECODER
from sonarr.episode_snapshot import Episode
from sonarr.series_snapshot import Series
from sonarr.sync.utils import EPISODE_DECODER, EPISODEFILE_DECODER, SERIES_DECODER
from tests.helpers.arr_fixtures import episode_payload, movie_payload, series_payload
import utilities.arr_decoding as arr_decoding
from utilities.arr_decoding import ArrRecordDecoder
from utilities.json_types import JsonValue


@pytest.mark.parametrize('encoded', [False, True])
@pytest.mark.parametrize(('kind', 'path'), [
    ('movie', ('qualityProfileId',)),
    ('series', ('qualityProfileId',)),
    ('series', ('languageProfileId',)),
    ('episode', ('episodeFileId',)),
    ('movie', ('movieFile', 'quality', 'quality', 'resolution')),
    ('episode', ('episodeFile', 'quality', 'quality', 'resolution')),
])
@pytest.mark.parametrize(('present', 'value', 'valid'), [
    (False, None, True), (True, None, False),
    (True, 0, True), (True, 7, True), (True, False, False), (True, '7', False), (True, 7.0, False),
])
def test_omitted_integer_fields_remain_distinct_from_explicit_null(
    kind: str, path: tuple[str, ...], present: bool, value: JsonValue, valid: bool, encoded: bool,
) -> None:
    payload = {'movie': movie_payload(), 'series': series_payload(), 'episode': episode_payload()}[kind]
    target = payload
    for segment in path[:-1]:
        child = target[segment]
        assert isinstance(child, dict)
        target = child
    if present:
        target[path[-1]] = value
    else:
        _ = target.pop(path[-1], None)
    decoder = {'movie': MOVIE_DECODER, 'series': SERIES_DECODER, 'episode': EPISODE_DECODER}[kind]

    record = decoder.decode(json.dumps(payload)) if encoded else decoder.from_value(payload)

    assert isinstance(record, (Movie, Series, Episode)) is valid


@pytest.mark.parametrize('encoded', [False, True])
def test_year_number_formats_preserve_integer_conversion(encoded: bool) -> None:
    for year in range(1900, 2101):
        for value in (year, float(year), str(year), f'{year}.0', f'{year * 10}e-1'):
            payload = series_payload()
            payload['year'] = value
            record = SERIES_DECODER.decode(json.dumps(payload)) if encoded else SERIES_DECODER.from_value(payload)
            assert isinstance(record, Series)
            assert type(record.year) is int
            assert record.year == year


@pytest.mark.parametrize('kind', ['movie', 'series', 'episode'])
@pytest.mark.parametrize('encoded', [False, True])
@pytest.mark.parametrize('value', [0, 1, 'true', 'false', None])
def test_monitored_flags_remain_strict(kind: str, encoded: bool, value: JsonValue) -> None:
    payload = {'movie': movie_payload(), 'series': series_payload(), 'episode': episode_payload()}[kind]
    payload['monitored'] = value
    decoder = {'movie': MOVIE_DECODER, 'series': SERIES_DECODER, 'episode': EPISODE_DECODER}[kind]

    record = decoder.decode(json.dumps(payload)) if encoded else decoder.from_value(payload)

    assert not isinstance(record, (Movie, Series, Episode))


@pytest.mark.parametrize('token', ['NaN', 'Infinity', '-Infinity'])
@pytest.mark.parametrize('as_bytes', [False, True])
@pytest.mark.parametrize('complete', [False, True])
def test_nonstandard_numbers_use_the_requests_json_fallback(
    token: str, as_bytes: bool, complete: bool, monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps(series_payload())[:-1] + ', "unused": ' + token + '}'
    wire = body.encode() if as_bytes else body
    seen: list[str | bytes] = []

    def reject_nonstandard(data: str | bytes) -> JsonValue:
        seen.append(data)
        raise requests.JSONDecodeError('Nonstandard number', body, body.index(token))

    monkeypatch.setattr(arr_decoding, '_CHECK_NONSTANDARD_NUMBERS', True)
    monkeypatch.setattr(ArrRecordDecoder, '_json_value', staticmethod(reject_nonstandard))
    with pytest.raises(requests.JSONDecodeError, match='Nonstandard number'):
        if complete:
            _ = SERIES_DECODER.decode_complete(wire)
        else:
            _ = SERIES_DECODER.decode(wire)
    assert seen == [wire]


@pytest.mark.parametrize('title', ['Avengers: Infinity War', 'Infinity', 'NaN', 'NaN values'])
def test_number_names_in_strings_keep_direct_json_decoding(title: str, monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_fallback(_data: bytes | str) -> JsonValue:
        pytest.fail('A title containing a number name should use direct decoding')

    monkeypatch.setattr(arr_decoding, '_CHECK_NONSTANDARD_NUMBERS', True)
    monkeypatch.setattr(ArrRecordDecoder, '_json_value', staticmethod(unexpected_fallback))
    record = SERIES_DECODER.decode(json.dumps(series_payload(title=title)))
    assert isinstance(record, Series)
    assert record.title == title


@pytest.mark.parametrize('token', ['NaN', 'Infinity', '-Infinity'])
@pytest.mark.parametrize('as_bytes', [False, True])
@pytest.mark.parametrize('complete', [False, True])
def test_accepting_json_backends_need_neither_a_scan_nor_a_dictionary_fallback(
    token: str, as_bytes: bool, complete: bool, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_scan(_data: bytes | str) -> bool:
        pytest.fail('This JSON backend accepts nonstandard numbers')

    def unexpected_fallback(_data: bytes | str) -> JsonValue:
        pytest.fail('Valid records should decode directly')

    monkeypatch.setattr(arr_decoding, '_CHECK_NONSTANDARD_NUMBERS', False)
    monkeypatch.setattr(ArrRecordDecoder, '_may_have_nonstandard_number', staticmethod(unexpected_scan))
    monkeypatch.setattr(ArrRecordDecoder, '_json_value', staticmethod(unexpected_fallback))
    title = 'To Infinity, and Beyond'
    body = json.dumps(series_payload(title=title))[:-1] + ', "unused": ' + token + '}'
    wire = body.encode() if as_bytes else body
    record = SERIES_DECODER.decode_complete(wire) if complete else SERIES_DECODER.decode(wire)
    assert isinstance(record, Series)
    assert record.title == title


@pytest.mark.parametrize('kind', ['movie', 'series', 'episode', 'file'])
@pytest.mark.parametrize('invalid_index', [0, 1, 2])
def test_invalid_complete_catalogues_do_not_decode_json_again(
    kind: str, invalid_index: int, monkeypatch: pytest.MonkeyPatch,
) -> None:
    file = episode_payload()['episodeFile']
    payload = {'movie': movie_payload(), 'series': series_payload(), 'episode': episode_payload(), 'file': file}[kind]
    rows = [payload, payload, payload]
    rows[invalid_index] = {}
    decoder = {'movie': MOVIE_DECODER, 'series': SERIES_DECODER,
               'episode': EPISODE_DECODER, 'file': EPISODEFILE_DECODER}[kind]

    def unexpected_fallback(_data: bytes | str) -> JsonValue:
        pytest.fail('The JSON is valid; the record validation failure should return None')

    monkeypatch.setattr(ArrRecordDecoder, '_json_value', staticmethod(unexpected_fallback))
    assert decoder.decode_complete(json.dumps(rows)) is None


@pytest.mark.parametrize('value', [False, 0, 'error', [], [None], {}])
@pytest.mark.parametrize('encoded', [False, True])
def test_invalid_movie_rows_keep_their_positions(value: JsonValue, encoded: bool) -> None:
    payloads: list[JsonValue] = [movie_payload(), value, movie_payload()]
    result = MOVIE_DECODER.decode(json.dumps(payloads)) if encoded else MOVIE_DECODER.from_value(payloads)
    assert isinstance(result, list)
    assert isinstance(result[0], Movie)
    assert result[1] == IncompleteMovie()
    assert isinstance(result[2], Movie)
    assert MOVIE_DECODER.decode('null') is None
    assert MOVIE_DECODER.decode('[null]') == [IncompleteMovie()]


@pytest.mark.parametrize('path', ['', ' \t\n', '\u2003', '\x1c', '\u200b', ' /movie.mkv '])
@pytest.mark.parametrize('encoded', [False, True])
def test_recovered_file_paths_keep_whitespace_validation(path: str, encoded: bool) -> None:
    payload: JsonValue = {'id': 7, 'hasFile': True, 'movieFile': {'id': 10, 'path': path, 'size': '4096'}}
    result = MOVIE_DECODER.decode(json.dumps(payload)) if encoded else MOVIE_DECODER.from_value(payload)
    expected_file = FileState(10, path, 4096) if path.strip() else None
    assert result == IncompleteMovie(7, True, expected_file)
