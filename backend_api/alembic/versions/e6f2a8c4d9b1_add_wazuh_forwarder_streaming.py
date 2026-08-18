"""Add Wazuh forwarder registration and batch replay protection.

Revision ID: e6f2a8c4d9b1
Revises: d2e5f9a3b7c4
Create Date: 2026-08-18 16:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6f2a8c4d9b1"
down_revision: Union[str, Sequence[str], None] = "d2e5f9a3b7c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "wazuh_forwarders" not in tables:
        op.create_table(
            "wazuh_forwarders",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("forwarder_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("token_digest", sa.String(), nullable=False),
            sa.Column("token_prefix", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="active"),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_sequence", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("tenant_id", "name", name="uq_wazuh_forwarder_tenant_name"),
        )
        op.create_index("ix_wazuh_forwarders_forwarder_id", "wazuh_forwarders", ["forwarder_id"])
        op.create_index("ix_wazuh_forwarders_tenant_id", "wazuh_forwarders", ["tenant_id"])
        op.create_index("ix_wazuh_forwarders_status", "wazuh_forwarders", ["status"])

    if "wazuh_forwarder_batches" not in tables:
        op.create_table(
            "wazuh_forwarder_batches",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("forwarder_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("batch_id", sa.String(), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("alert_count", sa.Integer(), nullable=False),
            sa.UniqueConstraint("forwarder_id", "sequence", name="uq_wazuh_forwarder_sequence"),
            sa.UniqueConstraint("forwarder_id", "batch_id", name="uq_wazuh_forwarder_batch"),
        )
        op.create_index("ix_wazuh_forwarder_batches_forwarder_id", "wazuh_forwarder_batches", ["forwarder_id"])
        op.create_index("ix_wazuh_forwarder_batches_tenant_id", "wazuh_forwarder_batches", ["tenant_id"])
        op.create_index("ix_wazuh_forwarder_batches_received_at", "wazuh_forwarder_batches", ["received_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "wazuh_forwarder_batches" in tables:
        op.drop_table("wazuh_forwarder_batches")
    if "wazuh_forwarders" in tables:
        op.drop_table("wazuh_forwarders")
