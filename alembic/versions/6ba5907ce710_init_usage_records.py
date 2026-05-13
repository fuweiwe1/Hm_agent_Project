"""init_usage_records

Revision ID: 6ba5907ce710
Revises:
Create Date: 2026-05-13 17:06:26.349562
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6ba5907ce710'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'usage_records',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('month', sa.String(), nullable=False),
        sa.Column('feature', sa.String(), nullable=False),
        sa.Column('efficiency', sa.String(), nullable=False),
        sa.Column('consumables', sa.String(), nullable=False),
        sa.Column('comparison', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'month'),
    )


def downgrade() -> None:
    op.drop_table('usage_records')
