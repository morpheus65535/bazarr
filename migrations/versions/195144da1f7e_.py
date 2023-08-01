"""empty message

Revision ID: 195144da1f7e
Revises: 95cd4cf40d7a
Create Date: 2023-07-27 13:14:08.825037

"""
from alembic import op
import sqlalchemy as sa

from app.database import TableHistory, TableHistoryMovie, TableBlacklist, TableBlacklistMovie, select


# revision identifiers, used by Alembic.
revision = '195144da1f7e'
down_revision = '95cd4cf40d7a'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)
tables = insp.get_table_names()
sqlite = bind.engine.name == 'sqlite'


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    if column_exists('table_episodes', 'rowid'):
        if sqlite:
            table_history_data = [{
                "id": x.id,
                "action": x.action,
                "description": x.description,
                "language": x.language,
                "provider": x.provider,
                "score": x.score,
                "sonarrEpisodeId": x.sonarrEpisodeId,
                "sonarrSeriesId": x.sonarrSeriesId,
                "subs_id": x.subs_id,
                "subtitles_path": x.subtitles_path,
                "timestamp": x.timestamp,
                "video_path": x.video_path,
                "matched": x.matched,
                "not_matched": x.not_matched,
            } for x in bind.execute(select(TableHistory)).all()]

            table_blacklist_data = [{
                "id": x.id,
                "language": x.language,
                "provider": x.provider,
                "sonarr_episode_id": x.sonarr_episode_id,
                "sonarr_series_id": x.sonarr_series_id,
                "subs_id": x.subs_id,
                "timestamp": x.timestamp,
            } for x in bind.execute(select(TableBlacklist)).all()]
        with op.batch_alter_table('table_episodes') as batch_op:
            batch_op.drop_column(column_name='rowid')
        if sqlite:
            op.bulk_insert(TableHistory.__table__, rows=table_history_data)
            op.bulk_insert(TableBlacklist.__table__, rows=table_blacklist_data)

    if column_exists('table_movies', 'rowid'):
        if sqlite:
            table_history_movie_data = [{
                "id": x.id,
                "action": x.action,
                "description": x.description,
                "language": x.language,
                "provider": x.provider,
                "radarrId": x.radarrId,
                "score": x.score,
                "subs_id": x.subs_id,
                "subtitles_path": x.subtitles_path,
                "timestamp": x.timestamp,
                "video_path": x.video_path,
                "matched": x.matched,
                "not_matched": x.not_matched,
            } for x in bind.execute(select(TableHistoryMovie)).all()]

            table_blacklist_movie_data = [{
                "id": x.id,
                "language": x.language,
                "provider": x.provider,
                "radarr_id": x.radarr_id,
                "subs_id": x.subs_id,
                "timestamp": x.timestamp,
            } for x in bind.execute(select(TableBlacklistMovie)).all()]
        with op.batch_alter_table('table_movies') as batch_op:
            batch_op.drop_column(column_name='rowid')
        if sqlite:
            op.bulk_insert(TableHistoryMovie.__table__, rows=table_history_movie_data)
            op.bulk_insert(TableBlacklistMovie.__table__, rows=table_blacklist_movie_data)

    if 'table_custom_score_profile_conditions' in tables:
        op.drop_table('table_custom_score_profile_conditions')

    if 'table_custom_score_profiles' in tables:
        op.drop_table('table_custom_score_profiles')


def downgrade():
    pass
