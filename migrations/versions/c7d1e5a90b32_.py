"""empty message

Revision ID: c7d1e5a90b32
Revises: a3f2c81b9d47
Create Date: 2026-08-13 00:41:12.503118

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d1e5a90b32'
down_revision = 'a3f2c81b9d47'
branch_labels = None
depends_on = None


bind = op.get_context().bind
insp = sa.inspect(bind)
tables = insp.get_table_names()


def upgrade():
    if 'table_blacklist_sports' not in tables:
        op.create_table(
            'table_blacklist_sports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('language', sa.Text(), nullable=True),
            sa.Column('provider', sa.Text(), nullable=True),
            sa.Column('sports_event_id', sa.Integer(), nullable=True),
            sa.Column('sportarr_league_id', sa.Integer(), nullable=True),
            sa.Column('subs_id', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['sports_event_id'], ['table_sports_events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sportarr_league_id'], ['table_sports_leagues.sportarrLeagueId'],
                                    ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'table_history_sports' not in tables:
        op.create_table(
            'table_history_sports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('action', sa.Integer(), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('language', sa.Text(), nullable=True),
            sa.Column('provider', sa.Text(), nullable=True),
            sa.Column('score', sa.Integer(), nullable=True),
            sa.Column('score_out_of', sa.Integer(), nullable=True),
            sa.Column('sportsEventId', sa.Integer(), nullable=True),
            sa.Column('sportarrLeagueId', sa.Integer(), nullable=True),
            sa.Column('subs_id', sa.Text(), nullable=True),
            sa.Column('subtitles_path', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('video_path', sa.Text(), nullable=True),
            sa.Column('matched', sa.Text(), nullable=True),
            sa.Column('not_matched', sa.Text(), nullable=True),
            sa.Column('upgradedFromId', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['sportsEventId'], ['table_sports_events.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sportarrLeagueId'], ['table_sports_leagues.sportarrLeagueId'],
                                    ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['upgradedFromId'], ['table_history_sports.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    pass
