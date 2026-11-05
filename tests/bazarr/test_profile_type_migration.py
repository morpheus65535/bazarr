import importlib

from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

migration = importlib.import_module('migrations.versions.a4c7e1f29b03_')

BASIC_ITEMS = '[{"id": 1, "language": "en", "hi": "False", "forced": "False"}]'


def _create_pre_migration_profiles_table(connection):
    connection.exec_driver_sql(
        'CREATE TABLE table_languages_profiles ('
        'profileId INTEGER PRIMARY KEY, cutoff INTEGER, originalFormat INTEGER, items TEXT NOT NULL, '
        'name TEXT NOT NULL, mustContain TEXT, mustNotContain TEXT, tag TEXT)'
    )


def _run_upgrade(connection):
    with Operations.context(MigrationContext.configure(connection)):
        migration.upgrade()


def test_migration_is_chained_after_previous_head():
    engine = create_engine('sqlite://')
    try:
        with engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
            scripts = ScriptDirectory('migrations')
            assert len(scripts.get_heads()) == 1
            assert scripts.get_revision(migration.revision).down_revision == '9c2f6a8d4b10'
    finally:
        engine.dispose()


def test_migration_backfills_existing_profiles_as_basic(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "profiles.sqlite"}')
    try:
        with engine.begin() as connection:
            _create_pre_migration_profiles_table(connection)
            connection.exec_driver_sql(
                'INSERT INTO table_languages_profiles (profileId, name, items) VALUES (1, ?, ?)',
                ('Existing', BASIC_ITEMS),
            )
            _run_upgrade(connection)
            row = connection.exec_driver_sql(
                'SELECT profileType, items FROM table_languages_profiles WHERE profileId = 1'
            ).one()

        assert row == ('basic', BASIC_ITEMS)
    finally:
        engine.dispose()


def test_migration_keeps_enhanced_profiles_and_is_rerunnable(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "profiles.sqlite"}')
    try:
        with engine.begin() as connection:
            _create_pre_migration_profiles_table(connection)
            connection.exec_driver_sql(
                'INSERT INTO table_languages_profiles (profileId, name, items) VALUES (1, ?, ?)',
                ('Existing', BASIC_ITEMS),
            )
            _run_upgrade(connection)
            connection.exec_driver_sql(
                "UPDATE table_languages_profiles SET profileType = 'enhanced' WHERE profileId = 1"
            )
            # A second run must not fail on the existing column or reset the type.
            _run_upgrade(connection)
            profile_type = connection.exec_driver_sql(
                'SELECT profileType FROM table_languages_profiles WHERE profileId = 1'
            ).scalar_one()

        assert profile_type == 'enhanced'
    finally:
        engine.dispose()
