import json
import importlib
from collections.abc import Iterator
from unittest import mock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from pytest import MonkeyPatch
from sqlalchemy import Integer, create_engine, inspect, select
from sqlalchemy.orm import Session
from subliminal import Episode

from app.database import TableEpisodes, TableShows
from sonarr.series_snapshot import Series, SeriesValues
from sonarr.sync import parser
from sonarr.sync.utils import SERIES_DECODER
from utilities.json_types import JsonValue
from subtitles.refiners import database as refiner

migration = importlib.import_module('migrations.versions.ca7df64674ee_')


def _series_payload(**overrides: JsonValue) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {
        'title': 'Show', 'path': '/tv/show', 'tvdbId': 1, 'id': 1, 'overview': '', 'images': [],
        'alternateTitles': [], 'tags': [], 'sortTitle': 'show', 'year': 2020, 'seriesType': 'standard',
        'monitored': True,
    }
    payload.update(overrides)
    return payload


def _series(**overrides: JsonValue) -> Series:
    record = SERIES_DECODER.complete_from_value(_series_payload(**overrides))
    assert isinstance(record, Series)
    return record


@pytest.fixture
def sonarr_info() -> Iterator[mock.Mock]:
    info = mock.Mock()
    info.is_legacy.return_value = False
    with mock.patch.object(parser, 'get_sonarr_info', info):
        yield info


TMDB_IDS = sorted(
    {0, 1, 603, 2**31 - 1}
    | {2**bit + offset for bit in range(1, 31) for offset in (-1, 0, 1)}
)


def _parse_series(show: Series) -> SeriesValues:
    return parser.seriesParser(show, action='update', tags_dict=[], language_profiles=[],
                               serie_default_profile=None, audio_profiles=[])


@pytest.mark.parametrize('tmdb_id', [None, *TMDB_IDS])
def test_series_parser_preserves_tmdb_id(sonarr_info: mock.Mock, tmdb_id: int | None) -> None:
    parsed = _parse_series(_series(tmdbId=tmdb_id))
    assert parsed['tmdbId'] == (None if tmdb_id is None or tmdb_id == 0 else tmdb_id)


@pytest.mark.parametrize('tmdb_id', TMDB_IDS)
def test_tmdb_id_is_independent_of_sonarr_and_tvdb_ids(sonarr_info: mock.Mock, tmdb_id: int) -> None:
    sonarr_id, tvdb_id = tmdb_id + 1, tmdb_id + 2
    parsed = _parse_series(_series(tmdbId=tmdb_id, id=sonarr_id, tvdbId=tvdb_id))
    assert parsed['tmdbId'] == (None if tmdb_id == 0 else tmdb_id)
    assert parsed['sonarrSeriesId'] == sonarr_id
    assert parsed['tvdbId'] == tvdb_id


@pytest.mark.parametrize('invalid_id', [True, False, '', '0', '603', 0.0, 603.0, [], {}, [603], {'id': 603}])
@pytest.mark.parametrize('encoded', [False, True])
def test_invalid_tmdb_id_preserves_valid_neighboring_records(invalid_id: JsonValue, encoded: bool) -> None:
    payloads: list[JsonValue] = [
        _series_payload(id=1, tmdbId=603),
        _series_payload(id=2, tmdbId=invalid_id),
        _series_payload(id=3, tmdbId=604),
    ]
    decoded = SERIES_DECODER.decode(json.dumps(payloads).encode()) if encoded else SERIES_DECODER.from_value(payloads)
    assert isinstance(decoded, list)
    assert len(decoded) == 3
    first, invalid, last = decoded
    assert isinstance(first, Series) and first.id == 1 and first.tmdbId == 603
    assert invalid is None
    assert isinstance(last, Series) and last.id == 3 and last.tmdbId == 604


def test_series_parser_without_tmdb_id_key(sonarr_info: mock.Mock) -> None:
    parsed = _parse_series(_series())

    assert parsed['tmdbId'] is None


@pytest.fixture
def refiner_session(memory_session: Session, monkeypatch: MonkeyPatch) -> Session:
    monkeypatch.setattr(refiner, 'database', memory_session)
    return memory_session


def _add_episode(session: Session, tmdb_id: int | None) -> None:
    session.add(TableShows(sonarrSeriesId=1, path='/tv/show', title='Show', alternativeTitles='[]',
                           tmdbId=tmdb_id))
    session.flush()
    session.add(TableEpisodes(sonarrEpisodeId=1, sonarrSeriesId=1, path='/tv/show/s01e01.mkv', season=1,
                              episode=1, title='Pilot', format='WEB-DL', resolution='1080p'))
    session.commit()


def _guessed_episode() -> Episode:
    return Episode('/tv/show/s01e01.mkv', 'Show', 1, 1, source='WEB-DL', resolution='1080p')


def test_refine_from_db_sets_series_tmdb_id(refiner_session: Session) -> None:
    _add_episode(refiner_session, tmdb_id=603)
    video = refiner.refine_from_db('/tv/show/s01e01.mkv', _guessed_episode())

    assert video.series_tmdb_id == 603


def test_refine_from_db_keeps_existing_series_tmdb_id(refiner_session: Session) -> None:
    _add_episode(refiner_session, tmdb_id=603)
    video = _guessed_episode()
    video.series_tmdb_id = 999
    video = refiner.refine_from_db('/tv/show/s01e01.mkv', video)

    assert video.series_tmdb_id == 999


def test_refine_from_db_leaves_series_tmdb_id_empty_when_unknown(refiner_session: Session) -> None:
    _add_episode(refiner_session, tmdb_id=None)
    video = refiner.refine_from_db('/tv/show/s01e01.mkv', _guessed_episode())

    assert video.series_tmdb_id is None


@pytest.mark.parametrize('tmdb_id', [None, *TMDB_IDS])
def test_tmdb_id_survives_parsing_storage_and_refinement(
    sonarr_info: mock.Mock, refiner_session: Session, tmdb_id: int | None,
) -> None:
    values = _parse_series(_series(tmdbId=tmdb_id))
    refiner_session.add(TableShows(**values))
    refiner_session.flush()
    refiner_session.add(TableEpisodes(sonarrEpisodeId=1, sonarrSeriesId=1, path='/tv/show/s01e01.mkv',
                                      season=1, episode=1, title='Pilot', format='WEB-DL', resolution='1080p'))
    refiner_session.commit()

    expected = None if tmdb_id is None or tmdb_id == 0 else tmdb_id
    stored = refiner_session.execute(select(TableShows.tmdbId).where(TableShows.sonarrSeriesId == 1)).scalar_one()
    assert stored == expected
    video = refiner.refine_from_db('/tv/show/s01e01.mkv', _guessed_episode())
    assert video.series_tmdb_id == expected


@pytest.mark.parametrize('stored_id', [None, 0, 603])
@pytest.mark.parametrize('existing_id', [None, *TMDB_IDS])
def test_tmdb_refinement_preserves_existing_id_or_uses_database_fallback(
    refiner_session: Session, stored_id: int | None, existing_id: int | None,
) -> None:
    _add_episode(refiner_session, tmdb_id=stored_id)
    video = _guessed_episode()
    video.series_tmdb_id = existing_id
    result = refiner.refine_from_db('/tv/show/s01e01.mkv', video)
    assert result.series_tmdb_id == (stored_id if stored_id and not existing_id else existing_id)


def test_migration_adds_tmdb_id_column_and_is_rerunnable() -> None:
    engine = create_engine('sqlite://')
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql('CREATE TABLE table_shows (sonarrSeriesId INTEGER PRIMARY KEY, title TEXT)')
            for _ in range(2):
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()

        columns = {column['name']: column for column in inspect(engine).get_columns('table_shows')}
        assert isinstance(columns['tmdbId']['type'], Integer)
        assert columns['tmdbId']['nullable'] is True
    finally:
        engine.dispose()


def test_migration_is_chained_after_previous_head() -> None:
    engine = create_engine('sqlite://')
    try:
        with engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
            scripts = ScriptDirectory('migrations')
            assert scripts.get_heads() == [migration.revision]
            assert scripts.get_revision(migration.revision).down_revision == 'a4c7e1f29b03'
    finally:
        engine.dispose()
