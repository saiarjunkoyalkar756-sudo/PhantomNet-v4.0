"""Add tenant-scoped saved threat hunts.

Revision ID: c7d1e4f8a2b6
Revises: a4b8d2e6f9c1
Create Date: 2026-08-18 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d1e4f8a2b6"
down_revision: Union[str, Sequence[str], None] = "a4b8d2e6f9c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "saved_hunts" not in set(inspector.get_table_names()):
        op.create_table(
            "saved_hunts",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("hunt_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("dataset", sa.String(), nullable=False),
            sa.Column("filters", sa.JSON(), nullable=False),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", name="uq_saved_hunt_tenant_name"),
        )
        op.create_index("ix_saved_hunts_hunt_id", "saved_hunts", ["hunt_id"])
        op.create_index("ix_saved_hunts_tenant_id", "saved_hunts", ["tenant_id"])
        op.create_index("ix_saved_hunts_created_at", "saved_hunts", ["created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "saved_hunts" in set(inspector.get_table_names()):
        op.drop_table("saved_hunts")
