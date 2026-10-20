import json
import gzip
from io import BytesIO
from urllib3.response import HTTPResponse

import msgspec
import pytest
import requests

from radarr.movie_snapshot import Movie, MovieFile
from sonarr.episode_snapshot import Episode, EpisodeFile
from sonarr.series_snapshot import Series
from sonarr.sync.utils import EPISODE_DECODER, EPISODEFILE_DECODER, SERIES_DECODER
from radarr.sync.utils import MOVIE_DECODER
from tests.helpers.arr_fixtures import episode_payload, movie_payload, series_payload
from utilities.arr_decoding import InvalidArrRecord
from utilities.json_types import JsonValue


def make_response(body: bytes, encoding: str | None = 'utf-8', *, compressed: bool = False) -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response.encoding = encoding
    headers = {'Content-Encoding': 'gzip'} if compressed else {}
    response.raw = HTTPResponse(body=BytesIO(gzip.compress(body) if compressed else body),
                                headers=headers, preload_content=False, decode_content=False)
    return response


@pytest.mark.parametrize('kind', ['episode', 'movie', 'series'])
@pytest.mark.parametrize('many', [False, True])
@pytest.mark.parametrize('compressed', [False, True])
def test_json_decodes_directly_into_records(kind: str, many: bool, compressed: bool) -> None:
    if kind == 'episode':
        payload, decoder, record_type = episode_payload(), EPISODE_DECODER, Episode
    elif kind == 'movie':
        payload, decoder, record_type = movie_payload(), MOVIE_DECODER, Movie
    else:
        payload, decoder, record_type = series_payload(), SERIES_DECODER, Series
    payload['unused'] = {'large': ['ignored metadata'] * 100}
    body = json.dumps([payload] if many else payload).encode()
    with make_response(body, compressed=compressed) as response:
        result = decoder.decode_response(response)
    record = result[0] if isinstance(result, list) else result
    assert isinstance(record, record_type)
    assert record.id == payload['id']
    assert not hasattr(record, '__dict__')
    assert not hasattr(record, 'unused')
    if isinstance(record, Episode):
        assert isinstance(record.episodeFile, EpisodeFile)
    if isinstance(record, Movie):
        assert isinstance(record.movieFile, MovieFile)


@pytest.mark.parametrize('kind', ['episode', 'movie', 'series'])
def test_empty_catalogue_and_failed_fetch_remain_distinct(kind: str) -> None:
    decoder = {'episode': EPISODE_DECODER, 'movie': MOVIE_DECODER, 'series': SERIES_DECODER}[kind]
    assert decoder.decode(b'[]') == []
    assert decoder.decode(b'null') is None
    assert decoder.decode_complete(b'{"error":"unavailable"}') is None


@pytest.mark.parametrize('kind', ['movie', 'series'])
def test_partial_catalogue_preserves_valid_records_and_invalid_row_positions(kind: str) -> None:
    payload, decoder, record_type = ((movie_payload(), MOVIE_DECODER, Movie) if kind == 'movie'
                                      else (series_payload(), SERIES_DECODER, Series))
    payload['unused'] = {'nested': ['unneeded metadata'] * 10}
    result = decoder.decode(json.dumps([payload, {'id': 12}, payload]))
    assert isinstance(result, list)
    assert isinstance(result[0], record_type)
    assert result[1] == InvalidArrRecord({'id': 12})
    assert isinstance(result[2], record_type)
    assert not hasattr(result[0], 'unused')


@pytest.mark.parametrize('payload', [[episode_payload(), {'id': 12}], [None], {}, {'error': 'unavailable'}])
def test_episode_decoder_rejects_incomplete_catalogues(payload: JsonValue) -> None:
    assert EPISODE_DECODER.decode_complete(json.dumps(payload)) is None


@pytest.mark.parametrize('body', [b'', b'{', b'[{},', b'[{"id":1},invalid]', b'[] trailing'])
def test_invalid_json_keeps_requests_error_details(body: bytes) -> None:
    with make_response(body) as baseline:
        with pytest.raises(requests.JSONDecodeError) as original:
            baseline.json()
    with make_response(body) as response:
        with pytest.raises(requests.JSONDecodeError) as actual:
            EPISODE_DECODER.decode_complete_response(response)
    assert (actual.value.msg, actual.value.doc, actual.value.pos) == (
        original.value.msg, original.value.doc, original.value.pos)


@pytest.mark.parametrize('encoding', ['utf-8', 'latin-1', 'utf-16', None])
def test_typed_records_preserve_encoding_behavior(encoding: str | None) -> None:
    payload = series_payload(title='Français')
    body = json.dumps(payload, ensure_ascii=False).encode(encoding or 'utf-32')
    with make_response(body, encoding) as response:
        record = SERIES_DECODER.decode_response(response)
    assert isinstance(record, Series)
    assert record.title == 'Français'


def test_invalid_utf8_is_replaced_as_in_requests() -> None:
    body = json.dumps(series_payload()).encode().replace(b'Series', b'\xffSeries')
    with make_response(body) as response:
        record = SERIES_DECODER.decode_response(response)
    assert isinstance(record, Series)
    assert record.title == '\ufffdSeries'


@pytest.mark.parametrize('overview', [None, True, 7, 1.25, 'Overview', ['a', None], {'x': True}])
def test_movie_overview_keeps_its_existing_display_conversion(overview: JsonValue) -> None:
    payload = movie_payload()
    payload['overview'] = overview
    result = MOVIE_DECODER.decode(json.dumps(payload))
    assert isinstance(result, Movie)
    assert result.overview == str(overview)


def test_nonstandard_numbers_and_large_integers_preserve_requests_semantics() -> None:
    payload = movie_payload(movie_id=2**100)
    payload['unused'] = float('nan')
    result = MOVIE_DECODER.decode(json.dumps(payload))
    assert isinstance(result, Movie)
    assert result.id == 2**100


@pytest.mark.parametrize('invalid', [True, False, '1', 1.0, None])
def test_episode_id_validation_is_applied_during_json_decoding(invalid: JsonValue) -> None:
    payload = episode_payload()
    payload['id'] = invalid
    assert EPISODE_DECODER.decode_complete(json.dumps([payload])) is None


def test_episode_file_constraints_apply_during_json_decoding() -> None:
    payload = episode_payload()['episodeFile']
    assert isinstance(payload, dict)
    payload['path'] = '  '
    assert EPISODEFILE_DECODER.decode_complete(json.dumps(payload)) is None
