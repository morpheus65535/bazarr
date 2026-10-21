import importlib
from unittest import mock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from pytest import MonkeyPatch
from sqlalchemy import Integer, create_engine, inspect
from sqlalchemy.orm import Session
from subliminal import Episode

from app.database import TableEpisodes, TableShows
from sonarr.sync import parser
from subtitles.refiners import database as refiner

migration = importlib.import_module('migrations.versions.ca7df64674ee_')


def _series_payload(**overrides: object) -> dict:
    payload = {
        'title': 'Show', 'path': '/tv/show', 'tvdbId': 1, 'id': 1, 'overview': '', 'images': [],
        'alternateTitles': [], 'tags': [], 'sortTitle': 'show', 'year': 2020, 'seriesType': 'standard',
        'monitored': True,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def sonarr_info() -> mock.Mock:
    info = mock.Mock()
    info.is_legacy.return_value = False
    with mock.patch.object(parser, 'get_sonarr_info', info):
        yield info


@pytest.mark.parametrize('payload_tmdb_id, expected', [
    (603, 603),
    ('603', 603),
    (0, None),
    (None, None),
])
def test_series_parser_reads_tmdb_id(sonarr_info: mock.Mock, payload_tmdb_id: object, expected: int | None) -> None:
    parsed = parser.seriesParser(_series_payload(tmdbId=payload_tmdb_id), action='update', tags_dict=[],
                                 language_profiles=[], serie_default_profile=None, audio_profiles=[])

    assert parsed['tmdbId'] == expected


def test_series_parser_without_tmdb_id_key(sonarr_info: mock.Mock) -> None:
    parsed = parser.seriesParser(_series_payload(), action='update', tags_dict=[],
                                 language_profiles=[], serie_default_profile=None, audio_profiles=[])

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
