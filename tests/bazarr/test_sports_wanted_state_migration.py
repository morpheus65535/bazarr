from typing import Iterator
from sqlalchemy.engine import Engine

import importlib

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from flask import Flask
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.orm import Session

from app import database as db
from subtitles import wanted_state
from tests.bazarr.test_wanted_search_migration import migration_engine, current_head  # noqa: F401


migration = importlib.import_module('migrations.versions.d8b3f0c4e215_')


def add_legacy_sports_columns(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql('ALTER TABLE table_sports_events DROP COLUMN missing_subtitles_calculated')
        connection.exec_driver_sql('ALTER TABLE table_sports_events ADD COLUMN "failedAttempts" TEXT')
        connection.exec_driver_sql('ALTER TABLE table_sports_events ADD COLUMN missing_subtitles TEXT')


def legacy_sports_events(engine: Engine) -> Table:
    return Table('table_sports_events', MetaData(), autoload_with=engine)


@pytest.fixture
def sports_upgrade(monkeypatch: pytest.MonkeyPatch,
                   migration_engine: Engine) -> Iterator[tuple[Engine, Session]]:  # noqa: F811
    engine = migration_engine
    add_legacy_sports_columns(engine)
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        monkeypatch.setattr(wanted_state, 'database', session)
        session.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
        session.execute(db.text(f"INSERT INTO alembic_version VALUES ('{migration.down_revision}')"))
        session.execute(db.insert(db.TableSportsLeagues).values(sportarrLeagueId=3, title='UFC', path='/ufc'))
        # Two parts of one card share the Sportarr event id, so the row id keys the shared tables.
        for row_id, part_number in [(17, 1), (18, 2)]:
            session.execute(db.insert(legacy_sports_events(engine)).values(
                id=row_id, sportarrLeagueId=3, sportarrEventId=318, partNumber=part_number,
                path=f'/ufc/part-{part_number}.mkv', title='UFC 318', season=2026, episode=1,
            ))
        session.execute(db.insert(db.TableSportsEventsSubtitles).values(
            sportsEventId=17, sportarrLeagueId=3, language='en', forced=False, hi=False, path='/ufc/part-1.en.srt',
        ))
        session.execute(db.insert(db.TableHistorySports).values(
            action=1, description='Downloaded', sportsEventId=17, sportarrLeagueId=3,
        ))
        # Episode rows written by the earlier migrations must stay as they are.
        session.execute(db.insert(db.TableMissingSubtitles).values(media_type='series', media_id=17, language='pt'))
        session.execute(db.insert(db.TableFailedSubtitleAttempts).values(
            media_type='series', media_id=17, language='pt', initial_attempt_at=1, latest_attempt_at=2,
        ))
        yield engine, session


def _set_legacy_values(session: Session, engine: Engine, row_id: int, missing: str | None,
                       failed: str | None) -> None:
    events = legacy_sports_events(engine)
    session.execute(db.update(events).where(events.c.id == row_id).values(
        missing_subtitles=missing, failedAttempts=failed,
    ))


def _sports_rows(session: Session, model):
    columns = [model.media_id, model.language]
    if model is db.TableFailedSubtitleAttempts:
        columns += [model.initial_attempt_at, model.latest_attempt_at]
    return session.execute(db.select(*columns).where(model.media_type == 'sports')
                           .order_by(model.media_id, model.language)).all()


def test_sports_migration_moves_column_data_to_the_shared_tables(sports_upgrade: tuple[Engine, Session]) -> None:
    engine, session = sports_upgrade
    _set_legacy_values(session, engine, 17, "['en', 'fr:hi:forced', 'FR:FORCED:HI', 'en']",
                       "[['en', 20], ['en', 10], ['fr:hi:forced', 3], ['FR:FORCED:HI', 8]]")
    _set_legacy_values(session, engine, 18, "['de']", "[['de', 5]]")
    session.commit()

    db.migrate_db(Flask(__name__))

    assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == current_head(engine)
    assert _sports_rows(session, db.TableMissingSubtitles) == [(17, 'en'), (17, 'fr:forced:hi'), (18, 'de')]
    assert _sports_rows(session, db.TableFailedSubtitleAttempts) == [
        (17, 'en', 10, 20), (17, 'fr:forced:hi', 3, 8), (18, 'de', 5, 5),
    ]
    assert session.execute(db.select(db.TableMissingSubtitles.language)
                           .where(db.TableMissingSubtitles.media_type == 'series')).scalars().all() == ['pt']
    assert session.execute(db.select(db.TableFailedSubtitleAttempts.latest_attempt_at)
                           .where(db.TableFailedSubtitleAttempts.media_type == 'series')).scalars().all() == [2]
    assert session.execute(db.select(db.TableSportsEvents.id, db.TableSportsEvents.missing_subtitles_calculated)
                           .order_by(db.TableSportsEvents.id)).all() == [(17, True), (18, True)]

    engine.dispose()
    inspector = inspect(engine)
    columns = {column['name'] for column in inspector.get_columns('table_sports_events')}
    assert 'missing_subtitles' not in columns
    assert 'failedAttempts' not in columns
    assert 'missing_subtitles_calculated' in columns
    assert 'uc_sports_event_part' in {
        item['name'] for item in inspector.get_unique_constraints('table_sports_events')
    }
    assert {'ix_sports_events_sportarr_league_id', 'ix_sports_events_path'} <= {
        item['name'] for item in inspector.get_indexes('table_sports_events')
    }
    # Rebuilding the table on SQLite must not cascade into the rows that point at it.
    assert session.execute(db.select(db.func.count()).select_from(db.TableSportsEventsSubtitles)).scalar_one() == 1
    assert session.execute(db.select(db.func.count()).select_from(db.TableHistorySports)).scalar_one() == 1

    # The writer uses the shared table as soon as the migration runs.
    wanted_state.store_missing_subtitles(db.TableSportsEvents.__table__, 'id', 'sports', 17, "['it']")
    assert wanted_state.get_missing_languages('sports', 17) == ['it']
    db.migrate_db(Flask(__name__))
    assert wanted_state.get_missing_languages('sports', 17) == ['it']


@pytest.mark.parametrize('missing, failed, expected_missing, expected_failed', [
    (None, None, [], []), ('', '', [], []), ('[]', '[]', [], []), ('malformed', 'malformed', [], []),
    ("['de', None, 'de']", "[['de', 5]]", ['de'], [('de', 5, 5)]),
])
def test_sports_migration_handles_legacy_values(
    sports_upgrade: tuple[Engine, Session],
    missing: str | None,
    failed: str | None,
    expected_missing: list[str],
    expected_failed: list[tuple[str, float, float]],
) -> None:
    engine, session = sports_upgrade
    _set_legacy_values(session, engine, 17, missing, failed)

    db.migrate_db(Flask(__name__))

    assert wanted_state.get_missing_languages('sports', 17) == expected_missing
    assert [row[1:] for row in _sports_rows(session, db.TableFailedSubtitleAttempts)] == expected_failed
    calculated = session.execute(db.select(db.TableSportsEvents.missing_subtitles_calculated)
                                 .where(db.TableSportsEvents.id == 17)).scalar_one()
    assert calculated is (missing is not None)


def test_sports_migration_replaces_stale_shared_rows(sports_upgrade: tuple[Engine, Session]) -> None:
    engine, session = sports_upgrade
    _set_legacy_values(session, engine, 17, "['en']", "[['en', 10]]")
    session.execute(db.insert(db.TableMissingSubtitles).values(media_type='sports', media_id=17, language='stale'))
    session.execute(db.insert(db.TableFailedSubtitleAttempts).values(
        media_type='sports', media_id=17, language='stale', initial_attempt_at=1, latest_attempt_at=1,
    ))

    db.migrate_db(Flask(__name__))

    assert _sports_rows(session, db.TableMissingSubtitles) == [(17, 'en')]
    assert _sports_rows(session, db.TableFailedSubtitleAttempts) == [(17, 'en', 10, 10)]


def test_failed_sports_backfill_rolls_back_and_can_be_retried(sports_upgrade: tuple[Engine, Session]) -> None:
    engine, session = sports_upgrade
    _set_legacy_values(session, engine, 17, "['en']", "[['en', 10]]")
    if engine.dialect.name == 'postgresql':
        session.execute(db.text("""CREATE FUNCTION fail_sports_insert() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'injected sports migration failure'; END; $$ LANGUAGE plpgsql"""))
        session.execute(db.text('CREATE TRIGGER fail_sports_insert BEFORE INSERT ON table_missing_subtitles '
                                'FOR EACH ROW EXECUTE FUNCTION fail_sports_insert()'))
        drop_trigger = 'DROP TRIGGER fail_sports_insert ON table_missing_subtitles'
    else:
        session.execute(db.text("""CREATE TRIGGER fail_sports_insert BEFORE INSERT ON table_missing_subtitles
            BEGIN SELECT RAISE(ABORT, 'injected sports migration failure'); END"""))
        drop_trigger = 'DROP TRIGGER fail_sports_insert'

    with pytest.raises(Exception, match='injected sports migration failure'):
        db.migrate_db(Flask(__name__))

    assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == migration.down_revision
    assert _sports_rows(session, db.TableFailedSubtitleAttempts) == []
    columns = {column['name'] for column in inspect(engine).get_columns('table_sports_events')}
    assert {'missing_subtitles', 'failedAttempts'} <= columns
    session.execute(db.text(drop_trigger))
    db.migrate_db(Flask(__name__))
    assert _sports_rows(session, db.TableMissingSubtitles) == [(17, 'en')]
    assert _sports_rows(session, db.TableFailedSubtitleAttempts) == [(17, 'en', 10, 10)]


def test_sports_migration_skips_tables_built_from_the_current_model(
    monkeypatch: pytest.MonkeyPatch, migration_engine: Engine,  # noqa: F811
) -> None:
    engine = migration_engine
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        session.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
        session.execute(db.text(f"INSERT INTO alembic_version VALUES ('{migration.down_revision}')"))
        session.execute(db.insert(db.TableSportsLeagues).values(sportarrLeagueId=3, title='UFC', path='/ufc'))
        session.execute(db.insert(db.TableSportsEvents).values(
            id=17, sportarrLeagueId=3, sportarrEventId=318, path='/ufc/card.mkv', title='UFC 318', season=2026,
            episode=1, missing_subtitles_calculated=True,
        ))
        session.commit()

        db.migrate_db(Flask(__name__))

        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == \
            current_head(engine)
        assert session.execute(db.select(db.TableSportsEvents.missing_subtitles_calculated)).scalar_one() is True


def test_sports_revision_follows_the_sports_tables(migration_engine: Engine) -> None:  # noqa: F811
    with migration_engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
        scripts = ScriptDirectory('migrations')
        assert scripts.get_heads() == [current_head(migration_engine)]
        upgrade_path = [step.revision.revision for step in scripts._upgrade_revs('head', '537e9b4d10e3')]
        sports_path = ['e6cbb0f6f9b1', 'f1d8a9c2b347', '9c2f6a8d4b10', 'a3f2c81b9d47', 'c7d1e5a90b32',
                       migration.revision]
        positions = [upgrade_path.index(revision) for revision in sports_path]
        assert positions == sorted(positions)


def test_sports_migration_appends_canonical_rows() -> None:
    rows = []
    migration._append_missing_rows(7, "['en', None, 'fr:hi:forced', 'FR:FORCED:HI', 'en']", rows)
    assert rows == [('sports', 7, 'en'), ('sports', 7, 'fr:forced:hi')]
