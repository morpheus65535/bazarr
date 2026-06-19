import importlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
import flask_migrate

from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy import event
from subtitles import wanted_state
from flask import Flask

from app import database as db


migration = importlib.import_module("migrations.versions.e6cbb0f6f9b1_")


def current_head(engine):
    with engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
        return ScriptDirectory('migrations').get_current_head()


def test_normal_startup_resolves_one_head_after_development():
    engine = create_engine('sqlite://')
    try:
        with engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
            scripts = ScriptDirectory('migrations')
            assert len(scripts.get_heads()) == 1
            revisions = scripts._upgrade_revs('head', '537e9b4d10e3')
            assert revisions[0].revision.revision == migration.revision
    finally:
        engine.dispose()


@pytest.fixture
def migration_engine(tmp_path):
    # Run this file with Bazarr's POSTGRES_ENABLED/POSTGRES_URL environment to
    # exercise PostgreSQL. Every test uses its own schema; SQLite uses a file.
    schema = None
    admin_engine = db.engine
    if db.postgresql:
        schema = 'wanted_migration_' + uuid4().hex
        with admin_engine.connect() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        url = db.url.update_query_dict({'options': f'-csearch_path={schema}'})
    else:
        url = f'sqlite:///{tmp_path / "startup.sqlite"}'
    engine = create_engine(url, isolation_level='AUTOCOMMIT')
    try:
        db.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()
        if schema is not None:
            with admin_engine.connect() as connection:
                connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')


def test_fresh_installation_and_restart(monkeypatch, migration_engine):
    engine = migration_engine
    db.metadata.drop_all(engine)
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        db.init_db()
        db.migrate_db(Flask(__name__))
        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == current_head(engine)
        for model in (db.TableFailedSubtitleAttempts,):
            assert session.execute(db.select(db.func.count()).select_from(model)).scalar_one() == 0
        session.commit()
        db.migrate_db(Flask(__name__))
        assert session.execute(db.select(db.func.count()).select_from(db.System)).scalar_one() == 1


def test_failed_backfill_rolls_back_and_can_be_retried(monkeypatch, migration_engine):
    engine = migration_engine
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        session.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
        session.execute(db.text("INSERT INTO alembic_version VALUES ('537e9b4d10e3')"))
        session.execute(db.insert(db.TableMovies).values(
            radarrId=7, path='/movie.mkv', title='Movie', tmdbId='7',
            missing_subtitles="['en']", failedAttempts="[['en', 10], ['en', 20]]",
        ))
        session.execute(db.insert(db.TableFailedSubtitleAttempts).values(
            media_type='movie', media_id=7, language='stale', initial_attempt_at=1, latest_attempt_at=2,
        ))
        if engine.dialect.name == 'postgresql':
            session.execute(db.text("""CREATE FUNCTION fail_retry_insert() RETURNS trigger AS $$
                BEGIN RAISE EXCEPTION 'injected migration failure'; END; $$ LANGUAGE plpgsql"""))
            session.execute(db.text('CREATE TRIGGER fail_retry_insert BEFORE INSERT ON table_failed_subtitle_attempts '
                                    'FOR EACH ROW EXECUTE FUNCTION fail_retry_insert()'))
            drop_trigger = 'DROP TRIGGER fail_retry_insert ON table_failed_subtitle_attempts'
        else:
            session.execute(db.text("""CREATE TRIGGER fail_retry_insert BEFORE INSERT ON table_failed_subtitle_attempts
                BEGIN SELECT RAISE(ABORT, 'injected migration failure'); END"""))
            drop_trigger = 'DROP TRIGGER fail_retry_insert'
        with pytest.raises(Exception, match='injected migration failure'):
            db.migrate_db(Flask(__name__))
        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == migration.down_revision
        assert session.execute(db.select(db.TableFailedSubtitleAttempts.language)).scalars().all() == ['stale']
        assert session.execute(db.select(db.TableMovies.failedAttempts)).scalar_one() == "[['en', 10], ['en', 20]]"
        session.execute(db.text(drop_trigger))
        db.migrate_db(Flask(__name__))
        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == current_head(engine)
        assert session.execute(db.select(db.TableFailedSubtitleAttempts.language)).scalars().all() == ['en']


@pytest.mark.parametrize('precreated_tables', [False, True])
def test_normal_startup_upgrades_development_database(monkeypatch, migration_engine, precreated_tables):
    engine = migration_engine
    if not precreated_tables:
        db.TableFailedSubtitleAttempts.__table__.drop(engine)
    # Force multiple bulk inserts with a small fixture on both database types.
    monkeypatch.setattr(migration, 'BACKFILL_BATCH_SIZE', 2)
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        monkeypatch.setattr(wanted_state, 'database', session)
        session.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
        session.execute(db.text("INSERT INTO alembic_version VALUES ('537e9b4d10e3')"))
        payloads = [
            ("['en', 'en', 'fr:hi:forced', 'FR:FORCED:HI']",
             "[['en', 20], ['en', 10], ['fr:hi:forced', 3], ['FR:FORCED:HI', 8]]"),
            (None, None), ('', ''), ('[]', '[]'), ('malformed', 'malformed'),
            ("['de', None]", "[['de', 5]]"),
        ]
        session.execute(db.insert(db.TableShows).values(sonarrSeriesId=3, title='Series', path='/series'))
        for index, (missing, failed) in enumerate(payloads, start=7):
            session.execute(db.insert(db.TableMovies).values(
                radarrId=index, path=f'/movie-{index}.mkv', title='Movie', tmdbId=str(index),
                missing_subtitles=missing, failedAttempts=failed,
            ))
            session.execute(db.insert(db.TableEpisodes).values(
                sonarrEpisodeId=index, sonarrSeriesId=3, path=f'/series/episode-{index}.mkv',
                title='Episode', season=1, episode=index, missing_subtitles=missing, failedAttempts=failed,
            ))
        if precreated_tables:
            session.execute(db.insert(db.TableFailedSubtitleAttempts).values(
                media_type='movie', media_id=7, language='stale', initial_attempt_at=1, latest_attempt_at=2,
            ))
        db.migrate_db(Flask(__name__))
        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == current_head(engine)
        attempt_rows = session.execute(db.select(
            db.TableFailedSubtitleAttempts.media_type, db.TableFailedSubtitleAttempts.media_id,
            db.TableFailedSubtitleAttempts.language, db.TableFailedSubtitleAttempts.initial_attempt_at,
            db.TableFailedSubtitleAttempts.latest_attempt_at,
        ).order_by(db.TableFailedSubtitleAttempts.media_type, db.TableFailedSubtitleAttempts.media_id,
                   db.TableFailedSubtitleAttempts.language)).all()
        assert attempt_rows == [
            (kind, media_id, language, initial, latest) for kind in ('movie', 'series')
            for media_id, language, initial, latest in [(7, 'en', 10, 20), (7, 'fr:forced:hi', 3, 8), (12, 'de', 5, 5)]
        ]
        # Alembic creates these tables using a separate engine. Reflect them
        # with a fresh pooled connection after that DDL.
        engine.dispose()
        inspector = inspect(engine)
        for table, constraint, index in [
            ('table_failed_subtitle_attempts', 'uc_failed_subtitle_attempts_language', 'ix_failed_subtitle_attempts_media'),
        ]:
            assert constraint in {item['name'] for item in inspector.get_unique_constraints(table)}
            assert index in {item['name'] for item in inspector.get_indexes(table)}
        for kind in ('movie', 'series'):
            wanted_state.record_failed_subtitle_attempts(kind, 7, ['en', 'it'])
        saved_attempts = session.execute(db.select(
            db.TableFailedSubtitleAttempts.media_type, db.TableFailedSubtitleAttempts.media_id,
            db.TableFailedSubtitleAttempts.language, db.TableFailedSubtitleAttempts.initial_attempt_at,
            db.TableFailedSubtitleAttempts.latest_attempt_at,
        ).order_by(db.TableFailedSubtitleAttempts.id)).all()
        assert all(latest > 20 for _, media_id, language, _, latest in saved_attempts
                   if media_id == 7 and language in ('en', 'it'))
        # Startup must not re-import obsolete columns over newer retry history.
        restart_app = Flask(__name__)
        db.migrate_db(restart_app)
        assert session.execute(db.select(
            db.TableFailedSubtitleAttempts.media_type, db.TableFailedSubtitleAttempts.media_id,
            db.TableFailedSubtitleAttempts.language, db.TableFailedSubtitleAttempts.initial_attempt_at,
            db.TableFailedSubtitleAttempts.latest_attempt_at,
        ).order_by(db.TableFailedSubtitleAttempts.id)).all() == saved_attempts
        # Both legacy columns remain unchanged by the retry migration.
        for model, id_column in [(db.TableMovies, db.TableMovies.radarrId),
                                 (db.TableEpisodes, db.TableEpisodes.sonarrEpisodeId)]:
            assert session.execute(db.select(model.missing_subtitles).order_by(id_column)).scalars().all() == [
                missing for missing, _ in payloads
            ]
        # An actual Alembic downgrade must retain the original retry snapshots.
        with restart_app.app_context():
            flask_migrate.downgrade(directory=db.migrations_directory, revision=migration.down_revision)
        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == migration.down_revision
        for model, id_column in [(db.TableMovies, db.TableMovies.radarrId),
                                 (db.TableEpisodes, db.TableEpisodes.sonarrEpisodeId)]:
            assert session.execute(db.select(model.failedAttempts).order_by(id_column)).scalars().all() == [
                failed for _, failed in payloads
            ]
        engine.dispose()
        assert not inspect(engine).has_table('table_failed_subtitle_attempts')
        assert not inspect(engine).has_table('table_missing_subtitles')


def test_concurrent_retry_writers_and_atomic_cleanup(monkeypatch, migration_engine):
    engine = migration_engine
    sessions = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(wanted_state, 'database', sessions)
    with Session(engine) as session:
        session.execute(db.insert(db.TableMovies).values(
            radarrId=7, path='/movie.mkv', title='Movie', tmdbId='7', failedAttempts='legacy snapshot',
        ))
    barrier = Barrier(2)

    def record(languages):
        try:
            barrier.wait(timeout=10)
            wanted_state.record_failed_subtitle_attempts('movie', 7, languages)
        finally:
            sessions.remove()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(record, ['en', 'fr']), executor.submit(record, ['en', 'de'])]
            for future in futures:
                future.result(timeout=20)
        rows = sessions.execute(db.select(db.TableFailedSubtitleAttempts)).scalars().all()
        assert {row.language for row in rows} == {'en', 'fr', 'de'}
        assert len(rows) == 3
        assert all(row.initial_attempt_at <= row.latest_attempt_at for row in rows)
        assert sessions.execute(db.select(db.TableMovies.failedAttempts)).scalar_one() == 'legacy snapshot'

        def reject_cleanup(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith('DELETE FROM table_failed_subtitle_attempts'):
                raise RuntimeError('cleanup failed')

        event.listen(engine, 'before_cursor_execute', reject_cleanup)
        try:
            with pytest.raises(RuntimeError, match='cleanup failed'):
                wanted_state.delete_media_and_wanted_search_state('movie', db.TableMovies, 'radarrId', 7)
        finally:
            event.remove(engine, 'before_cursor_execute', reject_cleanup)
        assert sessions.execute(db.select(db.TableMovies.radarrId)).scalar_one() == 7
        assert sessions.execute(db.select(db.func.count()).select_from(db.TableFailedSubtitleAttempts)).scalar_one() == 3
        wanted_state.delete_media_and_wanted_search_state('movie', db.TableMovies, 'radarrId', 7)
        wanted_state.record_failed_subtitle_attempts('movie', 7, ['en'])
        assert sessions.execute(db.select(db.TableMovies.radarrId)).all() == []
        assert sessions.execute(db.select(db.TableFailedSubtitleAttempts.id)).all() == []
    finally:
        sessions.remove()


@pytest.mark.parametrize('delete_parent', [False, True])
def test_episode_retry_write_racing_deletion_leaves_no_orphans(monkeypatch, migration_engine, delete_parent):
    engine = migration_engine
    sessions = scoped_session(sessionmaker(bind=engine))
    monkeypatch.setattr(wanted_state, 'database', sessions)
    with Session(engine) as session:
        session.execute(db.insert(db.TableShows).values(sonarrSeriesId=3, title='Series', path='/series'))
        session.execute(db.insert(db.TableEpisodes).values(
            sonarrEpisodeId=17, sonarrSeriesId=3, path='/series/e.mkv', title='Episode', season=1, episode=1,
        ))
    barrier = Barrier(2)

    def write():
        try:
            barrier.wait(timeout=10)
            wanted_state.record_failed_subtitle_attempts('series', 17, ['en', 'fr'])
        finally:
            sessions.remove()

    def remove():
        try:
            barrier.wait(timeout=10)
            if delete_parent:
                wanted_state.delete_series_and_wanted_search_state(3)
            else:
                wanted_state.delete_media_and_wanted_search_state('series', db.TableEpisodes, 'sonarrEpisodeId', 17)
        finally:
            sessions.remove()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(write), executor.submit(remove)]
            for future in futures:
                future.result(timeout=20)
        assert sessions.execute(db.select(db.TableEpisodes.sonarrEpisodeId)).all() == []
        assert sessions.execute(db.select(db.TableFailedSubtitleAttempts.id)).all() == []
    finally:
        sessions.remove()


def test_migration_appends_attempt_rows_using_shared_attempt_parser():
    rows = []

    migration._append_attempt_rows("series", 17, "[['en', 1], ['en', 3], ['fr', 2]]", rows)

    assert rows == [
        ("series", 17, "en", 1.0, 3.0),
        ("series", 17, "fr", 2.0, 2.0),
    ]


def test_downgrade_handles_existing_tables_without_indexes():
    engine = create_engine("sqlite://")
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE table_failed_subtitle_attempts (id INTEGER PRIMARY KEY)"
            )
            with Operations.context(MigrationContext.configure(connection)):
                migration.downgrade()

            inspector = inspect(connection)
            assert not inspector.has_table("table_failed_subtitle_attempts")
            assert not inspector.has_table("table_missing_subtitles")
    finally:
        engine.dispose()
