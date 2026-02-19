"""Add multi-instance Radarr support

Revision ID: a3f8b2c1d9e7
Revises: df76a4410347
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import warnings
from sqlalchemy import exc as sa_exc

# revision identifiers, used by Alembic.
revision = 'a3f8b2c1d9e7'
down_revision = 'df76a4410347'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)
tables = insp.get_table_names()

should_recreate = 'always' if bind.engine.name == 'sqlite' else 'auto'


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def table_exists(table_name):
    return table_name in tables


def upgrade():
    warnings.filterwarnings("ignore", category=sa_exc.SAWarning)

    # 1. Create the radarr instances table if it doesn't exist
    if not table_exists('table_radarr_instances'):
        op.create_table(
            'table_radarr_instances',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False),
            sa.Column('ip', sa.Text(), nullable=False),
            sa.Column('port', sa.Integer(), nullable=False),
            sa.Column('base_url', sa.Text(), nullable=False),
            sa.Column('ssl', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('apikey', sa.Text(), nullable=False, server_default=''),
            sa.Column('http_timeout', sa.Integer(), nullable=False, server_default='60'),
            sa.Column('enabled', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('full_update', sa.Text(), nullable=False, server_default='Daily'),
            sa.Column('full_update_day', sa.Integer(), nullable=False, server_default='6'),
            sa.Column('full_update_hour', sa.Integer(), nullable=False, server_default='4'),
            sa.Column('movies_sync', sa.Integer(), nullable=False, server_default='60'),
            sa.Column('movies_sync_on_live', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('only_monitored', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('excluded_tags', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('sync_only_monitored_movies', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('defer_search_signalr', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('use_ffprobe_cache', sa.Integer(), nullable=False, server_default='1'),
            sa.PrimaryKeyConstraint('id', name='pk_table_radarr_instances'),
        )

    # 2. Populate the primary instance from the app's settings
    # We read from config.yaml via a direct import to avoid circular dependency issues.
    # This populates instance id=1 from the existing settings.radarr.* config.
    try:
        from app.config import settings
        primary = {
            'id': 1,
            'name': 'Radarr',
            'ip': str(settings.radarr.ip),
            'port': int(settings.radarr.port),
            'base_url': str(settings.radarr.base_url),
            'ssl': 1 if settings.radarr.ssl else 0,
            'apikey': str(settings.radarr.apikey),
            'http_timeout': int(settings.radarr.http_timeout),
            'enabled': 1,
            'full_update': str(settings.radarr.full_update),
            'full_update_day': int(settings.radarr.full_update_day),
            'full_update_hour': int(settings.radarr.full_update_hour),
            'movies_sync': int(settings.radarr.movies_sync),
            'movies_sync_on_live': 1 if settings.radarr.movies_sync_on_live else 0,
            'only_monitored': 1 if settings.radarr.only_monitored else 0,
            'excluded_tags': str(settings.radarr.excluded_tags),
            'sync_only_monitored_movies': 1 if settings.radarr.sync_only_monitored_movies else 0,
            'defer_search_signalr': 1 if settings.radarr.defer_search_signalr else 0,
            'use_ffprobe_cache': 1 if settings.radarr.use_ffprobe_cache else 0,
        }
        instances_table = sa.table(
            'table_radarr_instances',
            sa.column('id'), sa.column('name'), sa.column('ip'), sa.column('port'),
            sa.column('base_url'), sa.column('ssl'), sa.column('apikey'),
            sa.column('http_timeout'), sa.column('enabled'), sa.column('full_update'),
            sa.column('full_update_day'), sa.column('full_update_hour'),
            sa.column('movies_sync'), sa.column('movies_sync_on_live'),
            sa.column('only_monitored'), sa.column('excluded_tags'),
            sa.column('sync_only_monitored_movies'), sa.column('defer_search_signalr'),
            sa.column('use_ffprobe_cache'),
        )
        # Only insert if no row with id=1 exists
        conn = op.get_bind()
        existing = conn.execute(sa.text("SELECT id FROM table_radarr_instances WHERE id=1")).fetchone()
        if not existing:
            conn.execute(instances_table.insert().values(**primary))
    except Exception as e:
        import logging
        logging.warning(f"Could not populate primary Radarr instance from settings: {e}")
        # Insert a placeholder row so the FK constraint is satisfied
        conn = op.get_bind()
        existing = conn.execute(sa.text("SELECT id FROM table_radarr_instances WHERE id=1")).fetchone()
        if not existing:
            conn.execute(sa.text(
                "INSERT INTO table_radarr_instances "
                "(id, name, ip, port, base_url, ssl, apikey, http_timeout, enabled, "
                " full_update, full_update_day, full_update_hour, movies_sync, "
                " movies_sync_on_live, only_monitored, excluded_tags, "
                " sync_only_monitored_movies, defer_search_signalr, use_ffprobe_cache) "
                "VALUES (1, 'Radarr', '127.0.0.1', 7878, '/', 0, '', 60, 1, "
                "        'Daily', 6, 4, 60, 1, 0, '[]', 0, 0, 1)"
            ))

    # 3. Add radarr_instance_id to table_movies and recreate with composite PK
    if not column_exists('table_movies', 'radarr_instance_id'):
        # First add the column as nullable
        with op.batch_alter_table('table_movies') as batch_op:
            batch_op.add_column(sa.Column('radarr_instance_id', sa.Integer(), nullable=True,
                                          server_default='1'))

        # Set all existing rows to instance 1
        op.get_bind().execute(sa.text("UPDATE table_movies SET radarr_instance_id = 1"))

    # Recreate table_movies with composite PK and updated constraints
    with op.batch_alter_table('table_movies', recreate=should_recreate) as batch_op:
        # Drop old single-column PK and recreate as composite
        batch_op.create_primary_key('pk_table_movies', ['radarrId', 'radarr_instance_id'])
        # Add FK to radarr_instances
        batch_op.create_foreign_key(
            'fk_movies_radarr_instance_id',
            'table_radarr_instances',
            ['radarr_instance_id'],
            ['id'],
            ondelete='CASCADE'
        )
        # Make radarr_instance_id non-nullable now that all rows have a value
        batch_op.alter_column('radarr_instance_id', nullable=False)
        # Drop the old global tmdbId unique constraint and recreate per-instance
        try:
            batch_op.drop_constraint('unique_table_movies_tmdbId', type_='unique')
        except Exception:
            pass
        batch_op.create_unique_constraint(
            'unique_table_movies_tmdbId_instance',
            ['tmdbId', 'radarr_instance_id']
        )

    # 4. Add radarr_instance_id to table_history_movie
    if not column_exists('table_history_movie', 'radarr_instance_id'):
        with op.batch_alter_table('table_history_movie') as batch_op:
            batch_op.add_column(sa.Column('radarr_instance_id', sa.Integer(), nullable=True,
                                          server_default='1'))
        op.get_bind().execute(sa.text("UPDATE table_history_movie SET radarr_instance_id = 1"))

    # Recreate table_history_movie with updated composite FK
    with op.batch_alter_table('table_history_movie', recreate=should_recreate) as batch_op:
        # Drop old single-column FK and recreate as composite
        try:
            batch_op.drop_constraint('fk_radarrId_history_movie', type_='foreignkey')
        except Exception:
            pass
        batch_op.alter_column('radarr_instance_id', nullable=False)
        batch_op.create_foreign_key(
            'fk_radarrId_history_movie',
            'table_movies',
            ['radarrId', 'radarr_instance_id'],
            ['radarrId', 'radarr_instance_id'],
            ondelete='CASCADE'
        )

    # 5. Add radarr_instance_id to table_blacklist_movie
    if not column_exists('table_blacklist_movie', 'radarr_instance_id'):
        with op.batch_alter_table('table_blacklist_movie') as batch_op:
            batch_op.add_column(sa.Column('radarr_instance_id', sa.Integer(), nullable=True,
                                          server_default='1'))
        op.get_bind().execute(sa.text("UPDATE table_blacklist_movie SET radarr_instance_id = 1"))

    # Recreate table_blacklist_movie with updated composite FK
    with op.batch_alter_table('table_blacklist_movie', recreate=should_recreate) as batch_op:
        try:
            batch_op.drop_constraint('fk_radarrId_blacklist_movie', type_='foreignkey')
        except Exception:
            pass
        batch_op.alter_column('radarr_instance_id', nullable=False)
        batch_op.create_foreign_key(
            'fk_radarrId_blacklist_movie',
            'table_movies',
            ['radarr_id', 'radarr_instance_id'],
            ['radarrId', 'radarr_instance_id'],
            ondelete='CASCADE'
        )

    warnings.filterwarnings("default", category=sa_exc.SAWarning)


def downgrade():
    pass
