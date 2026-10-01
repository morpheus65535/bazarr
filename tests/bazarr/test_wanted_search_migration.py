import importlib

from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from flask import Flask

from app import database as db


migration = importlib.import_module("migrations.versions.e6cbb0f6f9b1_")


def test_normal_startup_resolves_one_head_after_development():
    engine = create_engine('sqlite://')
    try:
        with engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
            scripts = ScriptDirectory('migrations')
            assert scripts.get_heads() == [migration.revision]
            revisions = scripts._upgrade_revs('head', '537e9b4d10e3')
            assert [step.revision.revision for step in revisions] == [migration.revision]
    finally:
        engine.dispose()


def test_normal_startup_upgrades_development_database(monkeypatch, tmp_path):
    url = f'sqlite:///{tmp_path / "startup.sqlite"}'
    engine = create_engine(url, isolation_level='AUTOCOMMIT')
    db.metadata.create_all(engine)
    db.TableMissingSubtitles.__table__.drop(engine)
    db.TableFailedSubtitleAttempts.__table__.drop(engine)
    try:
        with Session(engine) as session:
            monkeypatch.setattr(db, 'engine', engine)
            monkeypatch.setattr(db, 'url', url)
            monkeypatch.setattr(db, 'database', session)
            session.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
            session.execute(db.text("INSERT INTO alembic_version VALUES ('537e9b4d10e3')"))
            session.execute(db.insert(db.TableMovies).values(
                radarrId=7, path='/movie.mkv', title='Movie', tmdbId='7',
                missing_subtitles="['en', 'en', 'fr:hi']", failedAttempts="[['en', 10], ['en', 20]]",
            ))
            db.migrate_db(Flask(__name__))
            assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == migration.revision
            assert session.execute(db.select(db.TableMissingSubtitles.language).order_by(db.TableMissingSubtitles.id)).scalars().all() == ['en', 'fr:hi']
            attempt = session.execute(db.select(db.TableFailedSubtitleAttempts)).scalar_one()
            assert (attempt.language, attempt.initial_attempt_at, attempt.latest_attempt_at) == ('en', 10, 20)
            # Another startup must leave the data and version intact.
            db.migrate_db(Flask(__name__))
            assert session.execute(db.select(db.func.count()).select_from(db.TableMissingSubtitles)).scalar_one() == 2
    finally:
        engine.dispose()


def test_migration_appends_missing_rows_using_shared_text_parser():
    rows = []

    migration._append_missing_rows("movie", 7, "['en', None, 'fr:hi', 'en']", rows)

    assert rows == [("movie", 7, "en"), ("movie", 7, "fr:hi")]


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
