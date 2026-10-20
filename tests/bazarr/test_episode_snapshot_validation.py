import json
import pytest

from sonarr.sync.utils import EPISODE_DECODER, EPISODEFILE_DECODER
from utilities.json_types import JsonValue


@pytest.mark.parametrize('field', ['id', 'seriesId', 'seasonNumber', 'episodeNumber',
                                   'absoluteEpisodeNumber', 'tvdbId', 'episodeFileId'])
@pytest.mark.parametrize('invalid', [True, False, '1', 1.0, [], {}])
def test_episode_integer_fields_reject_non_integer_values(field: str, invalid: JsonValue) -> None:
    value: dict[str, JsonValue] = {'id': 1, 'seriesId': 2, 'title': 'Episode', 'hasFile': False,
                                  'monitored': True, 'seasonNumber': 0, 'episodeNumber': 0}
    value[field] = invalid
    assert EPISODE_DECODER.decode_complete(json.dumps(value)) is None


@pytest.mark.parametrize('field', ['id', 'size', 'resolution'])
@pytest.mark.parametrize('invalid', [True, False, '1', 1.0, None, [], {}])
def test_episode_file_integer_fields_reject_non_integer_values(field: str, invalid: JsonValue) -> None:
    definition: dict[str, JsonValue] = {'name': 'HDTV', 'resolution': 1080}
    value: dict[str, JsonValue] = {'id': 1, 'path': '/show/episode.mkv', 'size': 0,
                                  'quality': {'quality': definition}}
    if field == 'resolution':
        definition[field] = invalid
    else:
        value[field] = invalid
    assert EPISODEFILE_DECODER.decode_complete(json.dumps(value)) is None


def test_episode_integer_checks_preserve_zero_and_optional_null_values() -> None:
    value: dict[str, JsonValue] = {'id': 1, 'seriesId': 2, 'title': 'Episode', 'hasFile': False,
                                  'monitored': True, 'seasonNumber': 0, 'episodeNumber': 0,
                                  'absoluteEpisodeNumber': None, 'tvdbId': None}
    assert EPISODE_DECODER.decode_complete(json.dumps(value)) is not None
    assert EPISODEFILE_DECODER.decode_complete(json.dumps({'id': 1, 'path': '/show/episode.mkv', 'size': 0,
                            'quality': {'quality': {'name': 'HDTV', 'resolution': 0}}})) is not None
