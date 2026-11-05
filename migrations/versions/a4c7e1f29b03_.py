"""Add profile type to languages profiles.

Revision ID: a4c7e1f29b03
Revises: 9c2f6a8d4b10
"""

from alembic import op
import sqlalchemy as sa

revision = 'a4c7e1f29b03'
down_revision = '9c2f6a8d4b10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column['name'] for column in sa.inspect(bind).get_columns('table_languages_profiles')}
    if 'profileType' not in columns:
        op.add_column('table_languages_profiles', sa.Column(
            'profileType', sa.Text(), nullable=False, server_default=sa.text("'basic'"),
        ))

    # Existing profiles are basic profiles. Their items are left untouched.
    profiles = sa.table('table_languages_profiles', sa.column('profileType', sa.Text()))
    bind.execute(profiles.update()
                 .where(sa.or_(profiles.c.profileType.is_(None), profiles.c.profileType == ''))
                 .values(profileType='basic'))


def downgrade() -> None:
    pass
