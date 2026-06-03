"""normalize missing subtitles state

Revision ID: e6cbb0f6f9b1
Revises: 0124f9e278fb
Create Date: 2026-06-02 00:00:00.000000

"""
from functools import lru_cache
from math import isfinite

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e6cbb0f6f9b1'
down_revision = '0124f9e278fb'
branch_labels = None
depends_on = None

BACKFILL_BATCH_SIZE = 10000

MISSING_SUBTITLES_TABLE = sa.table(
    'table_missing_subtitles',
    sa.column('media_type', sa.Text),
    sa.column('media_id', sa.Integer),
    sa.column('language', sa.Text),
)
FAILED_SUBTITLE_ATTEMPTS_TABLE = sa.table(
    'table_failed_subtitle_attempts',
    sa.column('media_type', sa.Text),
    sa.column('media_id', sa.Integer),
    sa.column('language', sa.Text),
    sa.column('initial_attempt_at', sa.Float),
    sa.column('latest_attempt_at', sa.Float),
)


def table_exists(bind, table_name):
    return sa.inspect(bind).has_table(table_name)


def index_exists(bind, table_name, index_name):
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(i["name"] == index_name for i in indexes)


@lru_cache(maxsize=8192)
def _parse_missing_text_tuple(value):
    if not value:
        return ()
    if not isinstance(value, str):
        return ()

    value = value.strip()
    if value == '[]':
        return ()
    if not value.startswith('[') or not value.endswith(']'):
        return ()

    values = []
    body = value[1:-1].strip()
    if not body:
        return ()

    index = 0
    while index < len(body):
        while index < len(body) and body[index].isspace():
            index += 1

        if body.startswith('None', index):
            values.append(None)
            index += 4
        elif index < len(body) and body[index] in ("'", '"'):
            quote = body[index]
            index += 1
            chars = []
            while index < len(body):
                char = body[index]
                if char == "\\":
                    index += 1
                    if index >= len(body):
                        return ()
                    chars.append(body[index])
                    index += 1
                    continue
                if char == quote:
                    index += 1
                    break
                chars.append(char)
                index += 1
            else:
                return ()
            values.append("".join(chars))
        else:
            return ()

        while index < len(body) and body[index].isspace():
            index += 1
        if index == len(body):
            break
        if body[index] != ',':
            return ()
        index += 1
        if index == len(body):
            return ()

    return tuple(values)


def _parse_missing_text_list(value):
    if not isinstance(value, str):
        return []

    return list(_parse_missing_text_tuple(value))


def _parse_attempts(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []

    value = value.strip()
    if value == '[]':
        return []
    if not value.startswith('[[') or not value.endswith(']]'):
        return []

    attempts = []
    for attempt in value[2:-2].split('], ['):
        try:
            language, timestamp_text = attempt.split(', ', 1)
            if language[0] not in ("'", '"') or language[-1] != language[0]:
                return []
            timestamp = float(timestamp_text) if "." in timestamp_text else int(timestamp_text)
        except (IndexError, TypeError, ValueError):
            return []

        attempts.append([language[1:-1], timestamp])
    return attempts


def _attempt_windows(attempts):
    windows = {}
    for attempt in attempts:
        if not isinstance(attempt, (list, tuple)) or len(attempt) < 2:
            return {}

        language, timestamp = attempt[0], attempt[1]
        if not isinstance(language, str):
            return {}

        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError):
            return {}
        if not isfinite(timestamp):
            return {}

        initial_timestamp, latest_timestamp = windows.get(language, (timestamp, timestamp))
        if timestamp < initial_timestamp:
            initial_timestamp = timestamp
        if timestamp > latest_timestamp:
            latest_timestamp = timestamp
        windows[language] = (initial_timestamp, latest_timestamp)

    return windows


@lru_cache(maxsize=32768)
def _attempt_window_items(value):
    return tuple(
        (language, attempt_window[0], attempt_window[1])
        for language, attempt_window in _attempt_windows(_parse_attempts(value)).items()
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


def _get_driver_connection(bind):
    connection = bind.connection
    return getattr(connection, 'driver_connection', connection)


def _insert_missing_subtitles_cursor(write_cursor, rows):
    write_cursor.executemany(
        'INSERT INTO table_missing_subtitles (media_type, media_id, language) VALUES (?, ?, ?)',
        rows,
    )


def _insert_failed_attempts_cursor(write_cursor, rows):
    write_cursor.executemany(
        'INSERT INTO table_failed_subtitle_attempts '
        '(media_type, media_id, language, initial_attempt_at, latest_attempt_at) VALUES (?, ?, ?, ?, ?)',
        rows,
    )


def _append_missing_rows(media_type, media_id, missing_subtitles, missing_rows):
    seen_languages = set()
    for language in _parse_missing_text_list(missing_subtitles):
        if language is None or language in seen_languages:
            continue
        seen_languages.add(language)
        missing_rows.append((media_type, media_id, language))


def _append_attempt_rows(media_type, media_id, failed_attempts, attempt_rows):
    if not isinstance(failed_attempts, str):
        return

    for language, initial_attempt_at, latest_attempt_at in _attempt_window_items(failed_attempts):
        attempt_rows.append((media_type, media_id, language, initial_attempt_at, latest_attempt_at))


def _backfill_media_state(bind, media_type, id_column, table_name):
    rows = bind.exec_driver_sql(
        f'SELECT "{id_column}" AS media_id, missing_subtitles, "failedAttempts" '
        f'FROM {table_name} '
        "WHERE (missing_subtitles IS NOT NULL AND missing_subtitles != '[]') "
        'OR ("failedAttempts" IS NOT NULL AND "failedAttempts" != \'[]\')'
    )

    missing_rows = []
    attempt_rows = []
    for media_id, missing_subtitles, failed_attempts in rows:
        _append_missing_rows(media_type, media_id, missing_subtitles, missing_rows)
        _append_attempt_rows(media_type, media_id, failed_attempts, attempt_rows)

        if len(missing_rows) >= BACKFILL_BATCH_SIZE:
            _insert_missing_subtitles(bind, missing_rows)
            missing_rows = []
        if len(attempt_rows) >= BACKFILL_BATCH_SIZE:
            _insert_failed_attempts(bind, attempt_rows)
            attempt_rows = []

    if missing_rows:
        _insert_missing_subtitles(bind, missing_rows)
    if attempt_rows:
        _insert_failed_attempts(bind, attempt_rows)


def _backfill_media_state_sqlite(bind, media_type, id_column, table_name):
    driver_connection = _get_driver_connection(bind)
    read_cursor = driver_connection.cursor()
    write_cursor = driver_connection.cursor()
    read_cursor.execute(
        f'SELECT "{id_column}" AS media_id, missing_subtitles, "failedAttempts" '
        f'FROM {table_name} '
        "WHERE (missing_subtitles IS NOT NULL AND missing_subtitles != '[]') "
        'OR ("failedAttempts" IS NOT NULL AND "failedAttempts" != \'[]\')'
    )

    missing_rows = []
    attempt_rows = []
    for media_id, missing_subtitles, failed_attempts in read_cursor:
        _append_missing_rows(media_type, media_id, missing_subtitles, missing_rows)
        _append_attempt_rows(media_type, media_id, failed_attempts, attempt_rows)

        if len(missing_rows) >= BACKFILL_BATCH_SIZE:
            _insert_missing_subtitles_cursor(write_cursor, missing_rows)
            missing_rows = []
        if len(attempt_rows) >= BACKFILL_BATCH_SIZE:
            _insert_failed_attempts_cursor(write_cursor, attempt_rows)
            attempt_rows = []

    if missing_rows:
        _insert_missing_subtitles_cursor(write_cursor, missing_rows)
    if attempt_rows:
        _insert_failed_attempts_cursor(write_cursor, attempt_rows)


def _clear_backfilled_media_state(bind, media_type):
    bind.execute(
        sa.delete(MISSING_SUBTITLES_TABLE)
        .where(MISSING_SUBTITLES_TABLE.c.media_type == media_type)
    )
    bind.execute(
        sa.delete(FAILED_SUBTITLE_ATTEMPTS_TABLE)
        .where(FAILED_SUBTITLE_ATTEMPTS_TABLE.c.media_type == media_type)
    )


def _create_wanted_state_indexes(bind):
    if not index_exists(bind, 'table_missing_subtitles', 'ix_missing_subtitles_media'):
        op.create_index(
            'ix_missing_subtitles_media',
            'table_missing_subtitles',
            ['media_type', 'media_id'],
            unique=False,
        )
    if not index_exists(bind, 'table_failed_subtitle_attempts', 'ix_failed_subtitle_attempts_media'):
        op.create_index(
            'ix_failed_subtitle_attempts_media',
            'table_failed_subtitle_attempts',
            ['media_type', 'media_id'],
            unique=False,
        )


def upgrade():
    bind = op.get_context().bind

    if not table_exists(bind, 'table_missing_subtitles'):
        op.create_table(
            'table_missing_subtitles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('media_type', sa.Text(), nullable=False),
            sa.Column('media_id', sa.Integer(), nullable=False),
            sa.Column('language', sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('media_type', 'media_id', 'language', name='uc_missing_subtitles_language'),
        )
    if not table_exists(bind, 'table_failed_subtitle_attempts'):
        op.create_table(
            'table_failed_subtitle_attempts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('media_type', sa.Text(), nullable=False),
            sa.Column('media_id', sa.Integer(), nullable=False),
            sa.Column('language', sa.Text(), nullable=False),
            sa.Column('initial_attempt_at', sa.Float(), nullable=False),
            sa.Column('latest_attempt_at', sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('media_type', 'media_id', 'language', name='uc_failed_subtitle_attempts_language'),
        )
    backfill_media_state = _backfill_media_state_sqlite if bind.dialect.name == 'sqlite' else _backfill_media_state
    _clear_backfilled_media_state(bind, 'series')
    backfill_media_state(bind, 'series', 'sonarrEpisodeId', 'table_episodes')
    _clear_backfilled_media_state(bind, 'movie')
    backfill_media_state(bind, 'movie', 'radarrId', 'table_movies')
    _create_wanted_state_indexes(bind)


def downgrade():
    op.drop_index('ix_failed_subtitle_attempts_media', table_name='table_failed_subtitle_attempts')
    op.drop_table('table_failed_subtitle_attempts')
    op.drop_index('ix_missing_subtitles_media', table_name='table_missing_subtitles')
    op.drop_table('table_missing_subtitles')
