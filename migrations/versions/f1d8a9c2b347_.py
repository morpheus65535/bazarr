"""normalize missing subtitle languages

Revision ID: f1d8a9c2b347
Revises: e6cbb0f6f9b1
Create Date: 2026-06-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

from subtitles.language_utils import parse_language_token
from utilities.text_list import parse_text_list_or_default

revision = 'f1d8a9c2b347'
down_revision = 'e6cbb0f6f9b1'
branch_labels = None
depends_on = None

BACKFILL_BATCH_SIZE = 10000

MISSING_SUBTITLES_TABLE = sa.table(
    'table_missing_subtitles',
    sa.column('media_type', sa.Text),
    sa.column('media_id', sa.Integer),
    sa.column('language', sa.Text),
)

def table_exists(bind, table_name):
    return sa.inspect(bind).has_table(table_name)

def index_exists(bind, table_name, index_name):
    indexes = sa.inspect(bind).get_indexes(table_name)
    return any(i["name"] == index_name for i in indexes)

def _parse_missing_text_list(value):
    languages = []
    for language in parse_text_list_or_default(value):
        if language is None:
            continue
        parsed_language = parse_language_token(language)
        languages.append(parsed_language[0] if parsed_language is not None else language)
    return languages

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

def _get_driver_connection(bind):
    connection = bind.connection
    return getattr(connection, 'driver_connection', connection)

def _insert_missing_subtitles_cursor(write_cursor, rows):
    write_cursor.executemany(
        'INSERT INTO table_missing_subtitles (media_type, media_id, language) VALUES (?, ?, ?)',
        rows,
    )

def _append_missing_rows(media_type, media_id, missing_subtitles, missing_rows):
    seen_languages = set()
    for language in _parse_missing_text_list(missing_subtitles):
        if language is None or language in seen_languages:
            continue
        seen_languages.add(language)
        missing_rows.append((media_type, media_id, language))


def _backfill_media_state(bind, media_type, id_column, table_name):
    query = (
        f'SELECT "{id_column}" AS media_id, missing_subtitles FROM {table_name} '
        "WHERE missing_subtitles IS NOT NULL AND missing_subtitles != '[]'"
    )
    rows = bind.exec_driver_sql(query)
    buffered_rows = []
    for media_id, value in rows:
        _append_missing_rows(media_type, media_id, value, buffered_rows)
        if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
            _insert_missing_subtitles(bind, buffered_rows)
            buffered_rows = []
    if buffered_rows:
        _insert_missing_subtitles(bind, buffered_rows)


def _backfill_media_state_sqlite(bind, media_type, id_column, table_name):
    query = (
        f'SELECT "{id_column}" AS media_id, missing_subtitles FROM {table_name} '
        "WHERE missing_subtitles IS NOT NULL AND missing_subtitles != '[]'"
    )
    driver_connection = _get_driver_connection(bind)
    read_cursor = driver_connection.cursor()
    write_cursor = driver_connection.cursor()
    read_cursor.execute(query)
    rows = read_cursor
    buffered_rows = []
    for media_id, value in rows:
        _append_missing_rows(media_type, media_id, value, buffered_rows)
        if len(buffered_rows) >= BACKFILL_BATCH_SIZE:
            _insert_missing_subtitles_cursor(write_cursor, buffered_rows)
            buffered_rows = []
    if buffered_rows:
        _insert_missing_subtitles_cursor(write_cursor, buffered_rows)


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
    backfill = _backfill_media_state_sqlite if bind.dialect.name == 'sqlite' else _backfill_media_state
    for media_type, id_column, table_name in [('series', 'sonarrEpisodeId', 'table_episodes'),
                                             ('movie', 'radarrId', 'table_movies')]:
        bind.execute(sa.delete(MISSING_SUBTITLES_TABLE).where(MISSING_SUBTITLES_TABLE.c.media_type == media_type))
        backfill(bind, media_type, id_column, table_name)
    if not index_exists(bind, 'table_missing_subtitles', 'ix_missing_subtitles_media'):
        op.create_index('ix_missing_subtitles_media', 'table_missing_subtitles', ['media_type', 'media_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    if table_exists(bind, 'table_missing_subtitles'):
        if index_exists(bind, 'table_missing_subtitles', 'ix_missing_subtitles_media'):
            op.drop_index('ix_missing_subtitles_media', table_name='table_missing_subtitles')
        op.drop_table('table_missing_subtitles')
