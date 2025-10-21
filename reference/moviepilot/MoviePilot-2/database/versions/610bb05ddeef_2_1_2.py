"""2.1.2

Revision ID: 610bb05ddeef
Revises: 279a949d81b6
Create Date: 2025-02-24 07:52:00.042837

"""
import contextlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '610bb05ddeef'
down_revision = '279a949d81b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('workflow')
    if not any(c['name'] == 'flows' for c in columns):
        op.add_column('workflow', sa.Column('flows', sa.JSON(), nullable=True))


def downgrade() -> None:
    pass
