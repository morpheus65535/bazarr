import os
from types import SimpleNamespace

from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select

os.environ.setdefault("SZ_USER_AGENT", "pytest")

from subtitles import wanted_state


class _FakeConnection:
    def __init__(self):
        self.calls = []

    def exec_driver_sql(self, statement, params=None):
        self.calls.append((statement, params))


def test_update_failed_subtitle_attempts_uses_temp_table_for_sqlite(monkeypatch):
    metadata = MetaData()
    table = Table(
        "table_movies",
        metadata,
        Column("radarrId", Integer, primary_key=True),
        Column("failedAttempts", String),
    )
    connection = _FakeConnection()
    bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    monkeypatch.setattr(
        wanted_state,
        "database",
        SimpleNamespace(
            get_bind=lambda: bind,
            connection=lambda: connection,
            execute=lambda *args, **kwargs: None,
        ),
    )

    wanted_state.update_failed_subtitle_attempts(
        table,
        [(index, f"[['en', {float(index)}]]") for index in range(1000)],
        "radarrId",
    )

    assert connection.calls[0][0] == "DROP TABLE IF EXISTS temp_failed_attempt_updates"
    assert connection.calls[1][0].startswith("CREATE TEMP TABLE temp_failed_attempt_updates")
    assert connection.calls[2][0] == "INSERT INTO temp_failed_attempt_updates (media_id, failedAttempts) VALUES (?, ?)"
    assert len(connection.calls[2][1]) == 1000
    assert connection.calls[3][0] == (
        "UPDATE table_movies "
        'SET "failedAttempts" = ('
        "SELECT failedAttempts FROM temp_failed_attempt_updates "
        'WHERE media_id = table_movies."radarrId") '
        'WHERE "radarrId" IN (SELECT media_id FROM temp_failed_attempt_updates)'
    )
    assert connection.calls[-1][0] == "DROP TABLE IF EXISTS temp_failed_attempt_updates"


def test_update_failed_subtitle_attempts_uses_sqlalchemy_update_off_sqlite(monkeypatch):
    metadata = MetaData()
    table = Table(
        "table_movies",
        metadata,
        Column("radarrId", Integer, primary_key=True),
        Column("failedAttempts", String),
    )
    bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    executed = []

    monkeypatch.setattr(
        wanted_state,
        "database",
        SimpleNamespace(
            get_bind=lambda: bind,
            connection=lambda: None,
            execute=lambda statement: executed.append(statement),
        ),
    )

    wanted_state.update_failed_subtitle_attempts(
        table,
        [(17, "[['en', 1.0]]"), (42, "[['fr', 2.0]]")],
        "radarrId",
    )

    assert executed and executed[0].table.name == "table_movies"


def test_serialize_legacy_failed_attempts_preserves_initial_and_latest_order():
    assert wanted_state.serialize_legacy_failed_attempts(
        {"en": (1.0, 3.0), "fr": (2.0, 2.0)}
    ) == "[['en', 1.0], ['en', 3.0], ['fr', 2.0]]"


def test_delete_wanted_search_state_accepts_single_media_id(bind_wanted_state, transactional_session,
                                                           wanted_search_tables):
    del bind_wanted_state
    transactional_session.execute(insert(wanted_search_tables.missing_subtitles), [
        {"media_type": "movie", "media_id": 7, "language": "en"},
        {"media_type": "movie", "media_id": 8, "language": "fr"},
    ])
    transactional_session.execute(insert(wanted_search_tables.failed_subtitle_attempts), [
        {"media_type": "movie", "media_id": 7, "language": "en", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
        {"media_type": "movie", "media_id": 8, "language": "fr", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
    ])

    wanted_state.delete_wanted_search_state("movie", "7")

    missing_rows = transactional_session.execute(
        select(wanted_search_tables.missing_subtitles.c.media_id)
        .order_by(wanted_search_tables.missing_subtitles.c.media_id)
    ).scalars().all()
    failed_rows = transactional_session.execute(
        select(wanted_search_tables.failed_subtitle_attempts.c.media_id)
        .order_by(wanted_search_tables.failed_subtitle_attempts.c.media_id)
    ).scalars().all()
    assert missing_rows == [8]
    assert failed_rows == [8]


def test_delete_wanted_search_state_deduplicates_media_ids(bind_wanted_state, transactional_session,
                                                          wanted_search_tables):
    del bind_wanted_state
    transactional_session.execute(insert(wanted_search_tables.missing_subtitles), [
        {"media_type": "series", "media_id": 17, "language": "en"},
        {"media_type": "series", "media_id": 18, "language": "fr"},
    ])
    transactional_session.execute(insert(wanted_search_tables.failed_subtitle_attempts), [
        {"media_type": "series", "media_id": 17, "language": "en", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
        {"media_type": "series", "media_id": 18, "language": "fr", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
    ])

    wanted_state.delete_wanted_search_state("series", [17, "17", 17])

    missing_rows = transactional_session.execute(
        select(wanted_search_tables.missing_subtitles.c.media_id)
        .order_by(wanted_search_tables.missing_subtitles.c.media_id)
    ).scalars().all()
    failed_rows = transactional_session.execute(
        select(wanted_search_tables.failed_subtitle_attempts.c.media_id)
        .order_by(wanted_search_tables.failed_subtitle_attempts.c.media_id)
    ).scalars().all()
    assert missing_rows == [18]
    assert failed_rows == [18]
