"""Alter table_languages_profiles.originalFormat type to from bool to int

Revision ID: b183a2ac0dd1
Revises: 30f37e2e15e1
Create Date: 2024-02-16 10:32:39.123456

"""
from alembic import op
import sqlalchemy as sa
from app.database import TableLanguagesProfiles


# revision identifiers, used by Alembic.
revision = 'b183a2ac0dd1'
down_revision = '30f37e2e15e1'
branch_labels = None
depends_on = None

bind = op.get_context().bind


def upgrade():
    op.execute(sa.update(TableLanguagesProfiles)
               .values({TableLanguagesProfiles.originalFormat: 0})
               .where(TableLanguagesProfiles.originalFormat.is_(None)))
    if bind.engine.name == 'postgresql':
        with op.batch_alter_table('table_languages_profiles') as batch_op:
            batch_op.alter_column('originalFormat', type_=sa.Integer())


def downgrade():
    pass
