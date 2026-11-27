"""
Revision e41b7c9d2a60 adds what ca7df64674ee and 3b8e5d1a7f20 create to a database stamped past them.

Run this file with Bazarr's POSTGRES_ENABLED/POSTGRES_URL environment to exercise PostgreSQL.
"""
import importlib

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from flask import Flask
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app import database as db
from tests.bazarr.test_wanted_search_migration import migration_engine, current_head  # noqa: F401


migration = importlib.import_module('migrations.versions.e41b7c9d2a60_')

REPAIRED_INDEXES = {
    'table_episodes': {'ix_episodes_tvdb_id'},
    'table_shows': {'ix_shows_imdb_id'},
    'table_movies': {'ix_movies_imdb_id', 'ix_movies_movie_file_id'},
}


def _index_names(engine, table):
    return {index['name'] for index in inspect(engine).get_indexes(table)}


def _schema(engine):
    return {table: _index_names(engine, table) for table in REPAIRED_INDEXES}, \
        {column['name'] for column in inspect(engine).get_columns('table_shows')}


def _migrate_from(monkeypatch, engine, session, revision):
    monkeypatch.setattr(db, 'engine', engine)
    monkeypatch.setattr(db, 'url', engine.url)
    monkeypatch.setattr(db, 'database', session)
    session.execute(db.text('CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
    session.execute(db.text('DELETE FROM alembic_version'))
    session.execute(db.text(f"INSERT INTO alembic_version VALUES ('{revision}')"))
    session.commit()
    db.migrate_db(Flask(__name__))


def test_repair_is_the_only_head():
    with db.create_engine('sqlite://').connect() as connection, \
            Operations.context(MigrationContext.configure(connection)):
        heads = ScriptDirectory('migrations').get_heads()
    assert heads == [migration.revision]


def test_branch_era_database_gets_the_missing_column_and_indexes(monkeypatch: pytest.MonkeyPatch,
                                                                 migration_engine: Engine) -> None:  # noqa: F811
    engine = migration_engine
    # A branch-era database never ran ca7df64674ee or 3b8e5d1a7f20.
    with engine.begin() as connection:
        connection.exec_driver_sql('ALTER TABLE table_shows DROP COLUMN "tmdbId"')
    assert 'tmdbId' not in _schema(engine)[1]
    assert not _index_names(engine, 'table_movies') & REPAIRED_INDEXES['table_movies']

    with Session(engine) as session:
        _migrate_from(monkeypatch, engine, session, migration.down_revision)

        indexes, columns = _schema(engine)
        assert 'tmdbId' in columns
        for table, names in REPAIRED_INDEXES.items():
            assert names <= indexes[table]
        assert session.execute(db.select(db.TableShows)).all() == []
        assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == \
            current_head(engine)


def test_repair_does_nothing_on_a_complete_database(monkeypatch: pytest.MonkeyPatch,
                                                    migration_engine: Engine) -> None:  # noqa: F811
    engine = migration_engine
    db.metadata.drop_all(engine)
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        db.init_db()
        db.migrate_db(Flask(__name__))
        complete = _schema(engine)

        _migrate_from(monkeypatch, engine, session, migration.down_revision)

        assert _schema(engine) == complete
