"""Add bio identity baseline

Revision ID: e1f8d2c3b4a5
Revises: 42c6bdf3e26f
Create Date: 2026-04-14 09:47:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e1f8d2c3b4a5'
down_revision: Union[str, Sequence[str], None] = '42c6bdf3e26f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add bio_baseline JSON column to users table
    op.add_column('users', sa.Column('bio_baseline', sa.JSON(), nullable=True))
    # Add tenant_id if missing (hardening)
    # op.add_column('users', sa.Column('tenant_id', sa.String(), nullable=True)) 

def downgrade() -> None:
    op.drop_column('users', 'bio_baseline')
