"""normalize sports missing subtitles and failed attempts

Revision ID: d8b3f0c4e215
Revises: c7d1e5a90b32
Create Date: 2026-11-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from typing import cast

from subtitles.adaptive_searching import get_attempt_windows
from subtitles.language_utils import parse_language_token
from utilities.text_list import parse_text_list_or_default

revision = 'd8b3f0c4e215'
down_revision = 'c7d1e5a90b32'
branch_labels = None
depends_on = None

BACKFILL_BATCH_SIZE = 10000

MEDIA_TYPE = 'sports'
ID_COLUMN = 'id'
TABLE_NAME = 'table_sports_events'

FAILED_SUBTITLE_ATTEMPTS_TABLE = sa.table(
    'table_failed_subtitle_attempts',
    sa.column('media_type', sa.Text),
    sa.column('media_id', sa.Integer),
    sa.column('language', sa.Text),
    sa.column('initial_attempt_at', sa.Float),
    sa.column('latest_attempt_at', sa.Float),
)

MISSING_SUBTITLES_TABLE = sa.table(
    'table_missing_subtitles',
    sa.column('media_type', sa.Text),
    sa.column('media_id', sa.Integer),
    sa.column('language', sa.Text),
)


def table_exists(bind, table_name):
    return sa.inspect(bind).has_table(table_name)


def column_names(bind, table_name):
    return {column['name'] for column in sa.inspect(bind).get_columns(table_name)}


def _get_driver_connection(bind):
    connection = bind.connection
    return getattr(connection, 'driver_connection', connection)


def _append_attempt_rows(media_id, failed_attempts, rows):
    if not isinstance(failed_attempts, str):
        return

    for language, attempt_window in get_attempt_windows(failed_attempts).items():
        rows.append((MEDIA_TYPE, media_id, language, attempt_window[0], attempt_window[1]))


def _parse_missing_text_list(value):
    languages = []
    for language in parse_text_list_or_default(value):
        if language is None:
            continue
        parsed_language = parse_language_token(language)
        languages.append(parsed_language[0] if parsed_language is not None else language)
    return languages


def _append_missing_rows(media_id, missing_subtitles, rows):
    seen_languages = set()
    for language in _parse_missing_text_list(missing_subtitles):
        if language is None or language in seen_languages:
            continue
        seen_languages.add(language)
        rows.append((MEDIA_TYPE, media_id, language))


def _insert_failed_attempts(bind, rows):
    if not rows:
        return

    bind.execute(
        sa.insert(FAILED_SUBTITLE_ATTEMPTS_TABLE),
        [
            {
                'media_type': media_type,
                'media_id': media_id,
                'language': language,
                'initial_attempt_at': initial_attempt_at,
                'latest_attempt_at': latest_attempt_at,
            }
            for media_type, media_id, language, initial_attempt_at, latest_attempt_at in rows
        ],
    )


def _insert_missing_subtitles(bind, rows):
    if not rows:
        return

    bind.execute(
        sa.insert(MISSING_SUBTITLES_TABLE),
        [
            {'media_type': media_type, 'media_id': media_id, 'language': language}
            for media_type, media_id, language in rows
        ],
    )


def _insert_failed_attempts_cursor(write_cursor, rows):
    write_cursor.executemany(
        'INSERT INTO table_failed_subtitle_attempts '
        '(media_type, media_id, language, initial_attempt_at, latest_attempt_at) VALUES (?, ?, ?, ?, ?)',
        rows,
    )


def _insert_missing_subtitles_cursor(write_cursor, rows):
    write_cursor.executemany(
        'INSERT INTO table_missing_subtitles (media_type, media_id, language) VALUES (?, ?, ?)',
        rows,
    )


def _failed_attempts_query():
    return (
        f'SELECT "{ID_COLUMN}" AS media_id, "failedAttempts" FROM {TABLE_NAME} '
        'WHERE "failedAttempts" IS NOT NULL AND "failedAttempts" != \'[]\''
    )


def _missing_subtitles_query():
    return (
        f'SELECT "{ID_COLUMN}" AS media_id, missing_subtitles FROM {TABLE_NAME} '
        "WHERE missing_subtitles IS NOT NULL AND missing_subtitles != '[]'"
    )


def _backfill(bind, query, append_rows, insert_rows):
    rows = bind.exec_driver_sql(query)
    buffered_rows = []
    for media_id, value in rows:
        append_rows(media_id, value, buffered_rows)
        if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
            insert_rows(bind, buffered_rows)
            buffered_rows = []
    if buffered_rows:
        insert_rows(bind, buffered_rows)


def _backfill_sqlite(bind, query, append_rows, insert_rows_cursor):
    driver_connection = _get_driver_connection(bind)
    read_cursor = driver_connection.cursor()
    write_cursor = driver_connection.cursor()
    read_cursor.execute(query)
    buffered_rows = []
    for media_id, value in read_cursor:
        append_rows(media_id, value, buffered_rows)
        if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
            insert_rows_cursor(write_cursor, buffered_rows)
            buffered_rows = []
    if buffered_rows:
        insert_rows_cursor(write_cursor, buffered_rows)


def upgrade() -> None:
    bind = op.get_bind()
    if not table_exists(bind, TABLE_NAME):
        return
    is_sqlite = bind.dialect.name == 'sqlite'

    columns = column_names(bind, TABLE_NAME)
    if 'missing_subtitles_calculated' not in columns:
        op.add_column(TABLE_NAME, sa.Column(
            'missing_subtitles_calculated', sa.Boolean(), nullable=False, server_default=sa.false(),
        ))

    if 'failedAttempts' in columns:
        bind.execute(sa.delete(FAILED_SUBTITLE_ATTEMPTS_TABLE)
                     .where(FAILED_SUBTITLE_ATTEMPTS_TABLE.c.media_type == MEDIA_TYPE))
        if is_sqlite:
            _backfill_sqlite(bind, _failed_attempts_query(), _append_attempt_rows, _insert_failed_attempts_cursor)
        else:
            _backfill(bind, _failed_attempts_query(), _append_attempt_rows, _insert_failed_attempts)

    if 'missing_subtitles' in columns:
        bind.execute(sa.delete(MISSING_SUBTITLES_TABLE)
                     .where(MISSING_SUBTITLES_TABLE.c.media_type == MEDIA_TYPE))
        if is_sqlite:
            _backfill_sqlite(bind, _missing_subtitles_query(), _append_missing_rows, _insert_missing_subtitles_cursor)
        else:
            _backfill(bind, _missing_subtitles_query(), _append_missing_rows, _insert_missing_subtitles)

        events = sa.table(TABLE_NAME, sa.column('missing_subtitles', sa.Text()),
                          sa.column('missing_subtitles_calculated', sa.Boolean()))
        bind.execute(events.update().values(
            missing_subtitles_calculated=events.c.missing_subtitles.is_not(None),
        ))

    dropped_columns = [column for column in ('failedAttempts', 'missing_subtitles') if column in columns]
    if dropped_columns:
        with op.batch_alter_table(TABLE_NAME) as batch_op:
            for index in sa.inspect(bind).get_indexes(TABLE_NAME):
                if set(dropped_columns) & set(index['column_names'] or []):
                    # SQLite and PostgreSQL give every reflected index a name.
                    batch_op.drop_index(cast(str, index['name']))
            for column in dropped_columns:
                batch_op.drop_column(column)


def downgrade() -> None:
    pass
