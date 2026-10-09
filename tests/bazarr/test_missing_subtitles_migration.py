import importlib

import flask_migrate
import pytest
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.operations import Operations
from flask import Flask
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app import database as db
from subtitles import wanted_state
from tests.bazarr.test_wanted_search_migration import migration_engine


migration = importlib.import_module('migrations.versions.f1d8a9c2b347_')


@pytest.fixture
def missing_upgrade(monkeypatch, migration_engine):
    engine = migration_engine
    with Session(engine) as session:
        monkeypatch.setattr(db, 'engine', engine)
        monkeypatch.setattr(db, 'url', engine.url)
        monkeypatch.setattr(db, 'database', session)
        monkeypatch.setattr(wanted_state, 'database', session)
        session.execute(db.text('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)'))
        session.execute(db.text("INSERT INTO alembic_version VALUES ('e6cbb0f6f9b1')"))
        session.execute(db.insert(db.TableShows).values(sonarrSeriesId=3, title='Series', path='/series'))
        session.execute(db.insert(db.TableMovies).values(
            radarrId=7, path='/movie.mkv', title='Movie', tmdbId='7',
            missing_subtitles="['en']", failedAttempts="[['en', 10], ['en', 20]]",
        ))
        session.execute(db.insert(db.TableEpisodes).values(
            sonarrEpisodeId=17, sonarrSeriesId=3, path='/series/e.mkv', title='Episode', season=1, episode=1,
            missing_subtitles="['en']", failedAttempts="[['en', 10], ['en', 20]]",
        ))
        # These attempts were made after installing the previous PR. Its legacy
        # retry snapshots deliberately contain older times.
        session.execute(db.insert(db.TableFailedSubtitleAttempts), [
            {'media_type': kind, 'media_id': media_id, 'language': 'en',
             'initial_attempt_at': 30, 'latest_attempt_at': 300}
            for kind, media_id in [('movie', 7), ('series', 17)]
        ])
        yield engine, session


@pytest.mark.parametrize('precreated_table', [False, True])
def test_missing_cutover_imports_intervening_writes_and_preserves_retry_history(
    missing_upgrade, precreated_table,
):
    engine, session = missing_upgrade
    if not precreated_table:
        db.TableMissingSubtitles.__table__.drop(engine)
    else:
        session.execute(db.insert(db.TableMissingSubtitles).values(media_type='movie', media_id=7, language='stale'))
    # Simulate an indexer update while the application runs on the retry-only PR.
    for model in (db.TableMovies, db.TableEpisodes):
        session.execute(db.update(model).values(missing_subtitles="['fr:hi:forced', 'fr', 'FR:FORCED:HI']"))
    session.commit()
    if precreated_table:
        db.init_db()
    app = Flask(__name__)
    db.migrate_db(app)
    assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == migration.revision
    assert session.execute(db.select(db.TableMissingSubtitles.media_type, db.TableMissingSubtitles.media_id,
                                    db.TableMissingSubtitles.language).order_by(
        db.TableMissingSubtitles.media_type, db.TableMissingSubtitles.language)).all() == [
        (kind, media_id, language) for kind, media_id in [('movie', 7), ('series', 17)]
        for language in ['fr', 'fr:forced:hi']
    ]
    assert session.execute(db.select(db.TableFailedSubtitleAttempts.initial_attempt_at,
                                    db.TableFailedSubtitleAttempts.latest_attempt_at)).all() == [(30, 300), (30, 300)]
    engine.dispose()
    inspector = inspect(engine)
    assert 'uc_missing_subtitles_language' in {
        item['name'] for item in inspector.get_unique_constraints('table_missing_subtitles')
    }
    assert 'ix_missing_subtitles_media' in {item['name'] for item in inspector.get_indexes('table_missing_subtitles')}

    # The writer cutover belongs to the same release as this migration.
    for kind, media_id, model, id_column in [('movie', 7, db.TableMovies, 'radarrId'),
                                          ('series', 17, db.TableEpisodes, 'sonarrEpisodeId')]:
        wanted_state.store_missing_subtitles(model.__table__, id_column, kind, media_id, "['it']")
        assert wanted_state.get_missing_languages(kind, media_id) == ['it']
        assert session.execute(db.select(model.missing_subtitles)).scalar_one() == "['it']"
    restart_app = Flask(__name__)
    db.migrate_db(restart_app)
    assert session.execute(db.select(db.TableMissingSubtitles.language)).scalars().all() == ['it', 'it']
    assert session.execute(db.select(db.TableFailedSubtitleAttempts.latest_attempt_at)).scalars().all() == [300, 300]

    with restart_app.app_context():
        flask_migrate.downgrade(directory=db.migrations_directory, revision=migration.down_revision)
    engine.dispose()
    assert not inspect(engine).has_table('table_missing_subtitles')
    assert inspect(engine).has_table('table_failed_subtitle_attempts')
    assert session.execute(db.select(db.TableFailedSubtitleAttempts.latest_attempt_at)).scalars().all() == [300, 300]
    for model in (db.TableMovies, db.TableEpisodes):
        assert session.execute(db.select(model.missing_subtitles)).scalar_one() == "['it']"


@pytest.mark.parametrize('value, expected', [
    (None, []), ('', []), ('[]', []), ('malformed', []),
    ("['de', None, 'de']", ['de']), ("['en', 'fr:hi', 'en']", ['en', 'fr:hi']),
])
def test_missing_migration_handles_legacy_values(missing_upgrade, value, expected):
    _, session = missing_upgrade
    for model in (db.TableMovies, db.TableEpisodes):
        session.execute(db.update(model).values(missing_subtitles=value))
    db.migrate_db(Flask(__name__))
    for kind, media_id in [('movie', 7), ('series', 17)]:
        assert wanted_state.get_missing_languages(kind, media_id) == expected


def test_failed_missing_backfill_rolls_back_and_can_be_retried(missing_upgrade):
    engine, session = missing_upgrade
    session.execute(db.insert(db.TableMissingSubtitles).values(media_type='movie', media_id=7, language='stale'))
    if engine.dialect.name == 'postgresql':
        session.execute(db.text("""CREATE FUNCTION fail_missing_insert() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'injected missing migration failure'; END; $$ LANGUAGE plpgsql"""))
        session.execute(db.text('CREATE TRIGGER fail_missing_insert BEFORE INSERT ON table_missing_subtitles '
                                'FOR EACH ROW EXECUTE FUNCTION fail_missing_insert()'))
        drop_trigger = 'DROP TRIGGER fail_missing_insert ON table_missing_subtitles'
    else:
        session.execute(db.text("""CREATE TRIGGER fail_missing_insert BEFORE INSERT ON table_missing_subtitles
            BEGIN SELECT RAISE(ABORT, 'injected missing migration failure'); END"""))
        drop_trigger = 'DROP TRIGGER fail_missing_insert'
    with pytest.raises(Exception, match='injected missing migration failure'):
        db.migrate_db(Flask(__name__))
    assert session.execute(db.text('SELECT version_num FROM alembic_version')).scalar_one() == migration.down_revision
    assert session.execute(db.select(db.TableMissingSubtitles.language)).scalars().all() == ['stale']
    assert session.execute(db.select(db.TableFailedSubtitleAttempts.latest_attempt_at)).scalars().all() == [300, 300]
    session.execute(db.text(drop_trigger))
    db.migrate_db(Flask(__name__))
    assert session.execute(db.select(db.TableMissingSubtitles.language)).scalars().all() == ['en', 'en']


def test_missing_revision_follows_retry_cutover(migration_engine):
    with migration_engine.connect() as connection, Operations.context(MigrationContext.configure(connection)):
        scripts = ScriptDirectory('migrations')
        assert scripts.get_heads() == [migration.revision]
        assert [step.revision.revision for step in scripts._upgrade_revs('head', '537e9b4d10e3')] == [
            'e6cbb0f6f9b1', migration.revision,
        ]


def test_missing_migration_appends_canonical_rows():
    rows = []
    migration._append_missing_rows('movie', 7, "['en', None, 'fr:hi:forced', 'FR:FORCED:HI', 'en']", rows)
    assert rows == [('movie', 7, 'en'), ('movie', 7, 'fr:forced:hi')]
