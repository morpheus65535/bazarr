import json

import pytest

from radarr.movie_snapshot import Movie
from radarr.sync import utils as radarr
from sonarr.episode_snapshot import Episode, EpisodeFile, complete_episode_snapshot
from sonarr.series_snapshot import Series
from sonarr.sync import episodes as episode_sync
from sonarr.sync import utils as sonarr
from tests.bazarr.test_arr_typed_decoding import make_response
from tests.helpers.arr_fixtures import episode_payload, episode_record, movie_payload, series_payload
from utilities.arr_decoding import InvalidArrRecord


@pytest.mark.parametrize('kind', ['series', 'episodes', 'files', 'movies'])
@pytest.mark.parametrize('many', [False, True])
def test_media_helpers_return_typed_records(kind: str, many: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    if kind == 'series':
        module, payload, record_type = sonarr, series_payload(), Series
        fetch = lambda: sonarr.get_series_from_sonarr_api('key', None if many else 123)
    elif kind == 'episodes':
        module, payload, record_type = sonarr, episode_payload(), Episode
        fetch = lambda: sonarr.get_episodes_from_sonarr_api('key', series_id=7 if many else None,
                                                         episode_id=None if many else 101)
    elif kind == 'files':
        module, payload, record_type = sonarr, episode_payload()['episodeFile'], EpisodeFile
        fetch = lambda: sonarr.get_episodesFiles_from_sonarr_api('key', series_id=7 if many else None,
                                                              episode_file_id=None if many else 11)
    else:
        module, payload, record_type = radarr, movie_payload(), Movie
        fetch = lambda: radarr.get_movies_from_radarr_api('key', None if many else 1)
    monkeypatch.setattr(module, 'url_api_' + ('sonarr' if module is sonarr else 'radarr'),
                        lambda: 'http://example.invalid/api/v3/')
    response = make_response(json.dumps([payload] if many else payload).encode(), compressed=True)
    monkeypatch.setattr(module.requests, 'get', lambda *args, **kwargs: response)
    result = fetch()
    if many or kind == 'series':
        assert isinstance(result, list)
        assert len(result) == 1
        result = result[0]
    assert isinstance(result, record_type)
    assert response.raw.closed


@pytest.mark.parametrize('kind', ['series', 'movies'])
def test_partial_response_preserves_invalid_row_marker(kind: str, monkeypatch: pytest.MonkeyPatch) -> None:
    module, payload, decoder = ((sonarr, series_payload(), sonarr.get_series_from_sonarr_api) if kind == 'series'
                                else (radarr, movie_payload(), radarr.get_movies_from_radarr_api))
    monkeypatch.setattr(module, 'url_api_' + ('sonarr' if kind == 'series' else 'radarr'),
                        lambda: 'http://example.invalid/api/v3/')
    response = make_response(json.dumps([payload, {'id': 99}]).encode())
    monkeypatch.setattr(module.requests, 'get', lambda *args, **kwargs: response)
    result = decoder('key')
    assert isinstance(result, list)
    assert isinstance(result[0], (Series, Movie))
    assert result[1] == InvalidArrRecord({'id': 99})


@pytest.mark.parametrize('encoding', ['latin-1', 'utf-16', 'utf-32', None, 'unknown-codec'])
def test_typed_response_keeps_requests_encoding_fallback(encoding: str | None) -> None:
    payload = series_payload(title='Français')
    body = json.dumps(payload, ensure_ascii=False).encode(encoding if encoding not in (None, 'unknown-codec') else 'utf-8')
    with make_response(body, encoding) as response:
        record = sonarr.SERIES_DECODER.decode_response(response)
    assert isinstance(record, Series)
    assert record.title == 'Français'


def test_invalid_utf8_keeps_requests_replacement() -> None:
    body = json.dumps(series_payload()).encode().replace(b'Series', b'Seri\xffes')
    with make_response(body) as response:
        record = sonarr.SERIES_DECODER.decode_response(response)
    assert isinstance(record, Series)
    assert record.title == 'Seri\ufffdes'


@pytest.mark.parametrize('missing', [True, False])
def test_complete_episode_response_requires_all_file_joins(missing: bool) -> None:
    episode = episode_record(episode_payload())
    file = episode.episodeFile
    assert file is not None
    episode.episodeFile = None
    result = complete_episode_snapshot([episode], [] if missing else [file], separate_files=True)
    assert (result is None) == missing
    if result is not None:
        assert result.episodes[0].episodeFile is file


def test_duplicate_episode_ids_abort_reconciliation() -> None:
    episode = episode_record(episode_payload())
    assert complete_episode_snapshot([episode, episode]) is None


def test_duplicate_episode_file_ids_abort_reconciliation() -> None:
    episode = episode_record(episode_payload())
    assert episode.episodeFile is not None
    assert complete_episode_snapshot([episode], [episode.episodeFile, episode.episodeFile], separate_files=True) is None


def test_wrong_series_response_aborts_before_version_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    episode = episode_record(episode_payload(series_id=7))
    monkeypatch.setattr(episode_sync.get_sonarr_info, 'is_legacy', lambda: pytest.fail('Wrong identity must abort'))
    assert episode_sync._validated_episodes([episode], series_id=8) is None
