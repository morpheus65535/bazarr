"""normalize failed subtitle retry state

Revision ID: e6cbb0f6f9b1
Revises: 537e9b4d10e3
Create Date: 2026-06-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

from subtitles.adaptive_searching import get_attempt_windows

revision = 'e6cbb0f6f9b1'
down_revision = '537e9b4d10e3'
branch_labels = None
depends_on = None

BACKFILL_BATCH_SIZE = 10000

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

def _attempt_window_items(value):
    return tuple(
        (language, attempt_window[0], attempt_window[1])
        for language, attempt_window in get_attempt_windows(value).items()
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

def _insert_failed_attempts_cursor(write_cursor, rows):
    write_cursor.executemany(
        'INSERT INTO table_failed_subtitle_attempts '
        '(media_type, media_id, language, initial_attempt_at, latest_attempt_at) VALUES (?, ?, ?, ?, ?)',
        rows,
    )

def _append_attempt_rows(media_type, media_id, failed_attempts, attempt_rows):
    if not isinstance(failed_attempts, str):
        return

    for language, initial_attempt_at, latest_attempt_at in _attempt_window_items(failed_attempts):
        attempt_rows.append((media_type, media_id, language, initial_attempt_at, latest_attempt_at))


def _backfill_media_state(bind, media_type, id_column, table_name):
    query = (
        f'SELECT "{id_column}" AS media_id, "failedAttempts" FROM {table_name} '
        'WHERE "failedAttempts" IS NOT NULL AND "failedAttempts" != \'[]\''
    )
    rows = bind.exec_driver_sql(query)
    buffered_rows = []
    for media_id, value in rows:
        _append_attempt_rows(media_type, media_id, value, buffered_rows)
        if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
            _insert_failed_attempts(bind, buffered_rows)
            buffered_rows = []
    if buffered_rows:
        _insert_failed_attempts(bind, buffered_rows)


def _backfill_media_state_sqlite(bind, media_type, id_column, table_name):
    query = (
        f'SELECT "{id_column}" AS media_id, "failedAttempts" FROM {table_name} '
        'WHERE "failedAttempts" IS NOT NULL AND "failedAttempts" != \'[]\''
    )
    driver_connection = _get_driver_connection(bind)
    read_cursor = driver_connection.cursor()
    write_cursor = driver_connection.cursor()
    read_cursor.execute(query)
    rows = read_cursor
    buffered_rows = []
    for media_id, value in rows:
        _append_attempt_rows(media_type, media_id, value, buffered_rows)
        if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
            _insert_failed_attempts_cursor(write_cursor, buffered_rows)
            buffered_rows = []
    if buffered_rows:
        _insert_failed_attempts_cursor(write_cursor, buffered_rows)


def upgrade():
    bind = op.get_context().bind
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
    backfill = _backfill_media_state_sqlite if bind.dialect.name == 'sqlite' else _backfill_media_state
    for media_type, id_column, table_name in [('series', 'sonarrEpisodeId', 'table_episodes'),
                                             ('movie', 'radarrId', 'table_movies')]:
        bind.execute(sa.delete(FAILED_SUBTITLE_ATTEMPTS_TABLE).where(FAILED_SUBTITLE_ATTEMPTS_TABLE.c.media_type == media_type))
        backfill(bind, media_type, id_column, table_name)
    if not index_exists(bind, 'table_failed_subtitle_attempts', 'ix_failed_subtitle_attempts_media'):
        op.create_index('ix_failed_subtitle_attempts_media', 'table_failed_subtitle_attempts', ['media_type', 'media_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    if table_exists(bind, 'table_failed_subtitle_attempts'):
        if index_exists(bind, 'table_failed_subtitle_attempts', 'ix_failed_subtitle_attempts_media'):
            op.drop_index('ix_failed_subtitle_attempts_media', table_name='table_failed_subtitle_attempts')
        op.drop_table('table_failed_subtitle_attempts')
