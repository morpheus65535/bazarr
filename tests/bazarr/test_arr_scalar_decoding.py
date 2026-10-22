import json
import pytest

from radarr.movie_snapshot import IncompleteMovie, Movie
from radarr.sync.utils import MOVIE_DECODER
from sonarr.series_snapshot import Series
from sonarr.sync.utils import SERIES_DECODER
from tests.helpers.arr_fixtures import movie_payload, series_payload
from utilities.json_types import JsonValue


@pytest.mark.parametrize('kind', ['movie', 'series'])
@pytest.mark.parametrize('encoded', [False, True])
@pytest.mark.parametrize(('value', 'expected'), [
    (2024, 2024),
    ('2024', 2024),
    (2024.0, 2024),
    (None, None),
])
def test_year_scalars_are_normalized_during_decoding(
    kind: str, encoded: bool, value: JsonValue, expected: int | None,
) -> None:
    payload = movie_payload() if kind == 'movie' else series_payload()
    payload['year'] = value
    decoder = MOVIE_DECODER if kind == 'movie' else SERIES_DECODER
    record = decoder.decode(json.dumps(payload).encode()) if encoded else decoder.from_value(payload)

    assert isinstance(record, (Movie, Series))
    assert record.year == expected
    assert record.year is None or type(record.year) is int


@pytest.mark.parametrize('kind', ['movie', 'series'])
@pytest.mark.parametrize('encoded', [False, True])
@pytest.mark.parametrize('value', [True, False, 2024.5, 'Unknown', ' 2024 ', '0024'])
def test_invalid_year_scalars_do_not_produce_complete_records(
    kind: str, encoded: bool, value: JsonValue,
) -> None:
    payload = movie_payload() if kind == 'movie' else series_payload()
    payload['year'] = value
    decoder = MOVIE_DECODER if kind == 'movie' else SERIES_DECODER
    record = decoder.decode(json.dumps(payload).encode()) if encoded else decoder.from_value(payload)

    if kind == 'movie':
        assert isinstance(record, IncompleteMovie)
    else:
        assert record is None


@pytest.mark.parametrize('encoded', [False, True])
@pytest.mark.parametrize(('value', 'expected'), [
    (4096.9, 4096),
    ('4096', 4096),
    (-1, -1),
    (0, 0),
])
def test_radarr_file_sizes_are_normalized_during_decoding(
    encoded: bool, value: JsonValue, expected: int,
) -> None:
    payload = movie_payload()
    movie_file = payload['movieFile']
    assert isinstance(movie_file, dict)
    movie_file['size'] = value
    record = MOVIE_DECODER.decode(json.dumps(payload).encode()) if encoded else MOVIE_DECODER.from_value(payload)

    assert isinstance(record, Movie)
    assert record.movieFile is not None
    assert type(record.movieFile.size) is int
    assert record.movieFile.size == expected
