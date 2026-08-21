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
    # Legacy deployments provisioned tenancy and IAM tables outside Alembic. Clean self-hosted
    # deployment must bootstrap these prerequisites before applying the additive identity field.
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if 'tenants' not in existing:
        op.create_table(
            'tenants',
            sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        )
        existing.add('tenants')
    if 'users' not in existing:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('tenant_id', sa.String(length=36), nullable=False),
            sa.Column('username', sa.String(), nullable=True, unique=True),
            sa.Column('hashed_password', sa.String(), nullable=True),
            sa.Column('role', sa.String(), nullable=True),
            sa.Column('twofa_enforced', sa.Boolean(), nullable=True),
            sa.Column('totp_secret', sa.String(), nullable=True),
            sa.Column('webauthn_enabled', sa.Boolean(), nullable=True),
            sa.Column('trust_score', sa.Float(), nullable=True),
        )
    # Add bio_baseline JSON column to users table.
    op.add_column('users', sa.Column('bio_baseline', sa.JSON(), nullable=True))
    # Add tenant_id if missing (hardening)
    # op.add_column('users', sa.Column('tenant_id', sa.String(), nullable=True)) 

def downgrade() -> None:
    op.drop_column('users', 'bio_baseline')
