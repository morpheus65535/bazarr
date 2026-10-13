import os

from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

os.environ.setdefault("SZ_USER_AGENT", "pytest")

from subtitles import wanted_state
from subtitles.serialization import missing_subtitle_to_language_tuple


def test_delete_wanted_search_state_accepts_single_media_id(bind_wanted_state, transactional_session,
                                                           wanted_search_tables):
    del bind_wanted_state
    transactional_session.execute(insert(wanted_search_tables.failed_subtitle_attempts), [
        {"media_type": "movie", "media_id": 7, "language": "en", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
        {"media_type": "movie", "media_id": 8, "language": "fr", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
    ])

    wanted_state.delete_wanted_search_state("movie", "7")

    failed_rows = transactional_session.execute(
        select(wanted_search_tables.failed_subtitle_attempts.c.media_id)
        .order_by(wanted_search_tables.failed_subtitle_attempts.c.media_id)
    ).scalars().all()
    assert failed_rows == [8]


def test_delete_wanted_search_state_deduplicates_media_ids(bind_wanted_state, transactional_session,
                                                          wanted_search_tables):
    del bind_wanted_state
    transactional_session.execute(insert(wanted_search_tables.failed_subtitle_attempts), [
        {"media_type": "series", "media_id": 17, "language": "en", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
        {"media_type": "series", "media_id": 18, "language": "fr", "initial_attempt_at": 1.0, "latest_attempt_at": 2.0},
    ])

    wanted_state.delete_wanted_search_state("series", [17, "17", 17])

    failed_rows = transactional_session.execute(
        select(wanted_search_tables.failed_subtitle_attempts.c.media_id)
        .order_by(wanted_search_tables.failed_subtitle_attempts.c.media_id)
    ).scalars().all()
    assert failed_rows == [18]


def test_transactional_fixture_rolls_back_session_commit(transactional_engine, transactional_connection):
    transactional_connection.exec_driver_sql("CREATE TABLE transaction_probe (value INTEGER)")
    session = Session(bind=transactional_connection, join_transaction_mode="create_savepoint")
    session.execute(text("INSERT INTO transaction_probe VALUES (1)"))
    session.commit()
    assert transactional_connection.in_transaction()
    session.close()

    transactional_connection.rollback()
    transactional_connection.close()

    with transactional_engine.connect() as connection:
        table_count = connection.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE name = 'transaction_probe'")
        ).scalar_one()
    assert table_count == 0


def test_missing_subtitle_to_language_tuple_preserves_combined_flags():
    assert missing_subtitle_to_language_tuple("en:hi:forced") == ("en", "True", "True")
