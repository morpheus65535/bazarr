"""empty message

Revision ID: a3f2c81b9d47
Revises: 0124f9e278fb
Create Date: 2026-08-12 14:22:08.417293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f2c81b9d47'
down_revision = '0124f9e278fb'
branch_labels = None
depends_on = None


bind = op.get_context().bind
insp = sa.inspect(bind)
tables = insp.get_table_names()


def upgrade():
    if 'table_sports_leagues' not in tables:
        op.create_table(
            'table_sports_leagues',
            sa.Column('sportarrLeagueId', sa.Integer(), nullable=False),
            sa.Column('audio_language', sa.Text(), nullable=True),
            sa.Column('created_at_timestamp', sa.DateTime(), nullable=True),
            sa.Column('externalId', sa.Text(), nullable=True),
            sa.Column('fanart', sa.Text(), nullable=True),
            sa.Column('monitored', sa.Text(), nullable=True),
            sa.Column('overview', sa.Text(), nullable=True),
            sa.Column('path', sa.Text(), nullable=False),
            sa.Column('poster', sa.Text(), nullable=True),
            sa.Column('profileId', sa.Integer(), nullable=True),
            sa.Column('sortTitle', sa.Text(), nullable=True),
            sa.Column('sport', sa.Text(), nullable=True),
            sa.Column('tags', sa.Text(), nullable=True),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['profileId'], ['table_languages_profiles.profileId'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('sportarrLeagueId'),
            sa.UniqueConstraint('path'),
        )

    if 'table_sports_events' not in tables:
        op.create_table(
            'table_sports_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('audio_codec', sa.Text(), nullable=True),
            sa.Column('audio_language', sa.Text(), nullable=True),
            sa.Column('broadcastDate', sa.Text(), nullable=True),
            sa.Column('created_at_timestamp', sa.DateTime(), nullable=True),
            sa.Column('episode', sa.Integer(), nullable=False),
            sa.Column('externalId', sa.Text(), nullable=True),
            sa.Column('failedAttempts', sa.Text(), nullable=True),
            sa.Column('ffprobe_cache', sa.LargeBinary(), nullable=True),
            sa.Column('file_id', sa.Integer(), nullable=True),
            sa.Column('file_size', sa.BigInteger(), nullable=True),
            sa.Column('format', sa.Text(), nullable=True),
            sa.Column('missing_subtitles', sa.Text(), nullable=True),
            sa.Column('monitored', sa.Text(), nullable=True),
            sa.Column('partName', sa.Text(), nullable=True),
            sa.Column('partNumber', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('path', sa.Text(), nullable=False),
            sa.Column('resolution', sa.Text(), nullable=True),
            sa.Column('sceneName', sa.Text(), nullable=True),
            sa.Column('season', sa.Integer(), nullable=False),
            sa.Column('sportarrEventId', sa.Integer(), nullable=False),
            sa.Column('sportarrLeagueId', sa.Integer(), nullable=True),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True),
            sa.Column('video_codec', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['sportarrLeagueId'], ['table_sports_leagues.sportarrLeagueId'],
                                    ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sportarrEventId', 'partNumber', name='uc_sports_event_part'),
        )

    if 'table_sports_events_subtitles' not in tables:
        op.create_table(
            'table_sports_events_subtitles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('language', sa.Text(), nullable=False),
            sa.Column('hi', sa.Boolean(), nullable=False),
            sa.Column('forced', sa.Boolean(), nullable=False),
            sa.Column('path', sa.Text(), nullable=True),
            sa.Column('size', sa.BigInteger(), nullable=True),
            sa.Column('embedded_track_id', sa.Integer(), nullable=True),
            sa.Column('sportsEventId', sa.Integer(), nullable=False),
            sa.Column('sportarrLeagueId', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['sportsEventId'], ['table_sports_events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sportarrLeagueId'], ['table_sports_leagues.sportarrLeagueId'],
                                    ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('path', 'sportarrLeagueId', 'sportsEventId', 'language', 'forced', 'hi',
                                name='uc_external_sports_events_subtitles'),
            sa.UniqueConstraint('embedded_track_id', 'sportarrLeagueId', 'sportsEventId', 'language', 'forced', 'hi',
                                name='uc_embedded_sports_events_subtitles'),
        )

    if 'table_sports_leagues_rootfolder' not in tables:
        op.create_table(
            'table_sports_leagues_rootfolder',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('accessible', sa.Integer(), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('path', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    pass
