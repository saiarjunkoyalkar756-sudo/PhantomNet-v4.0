"""Add endpoint inventory and integrity evidence.

Revision ID: d2e5f9a3b7c4
Revises: c7d1e4f8a2b6
Create Date: 2026-08-18 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e5f9a3b7c4"
down_revision: Union[str, Sequence[str], None] = "c7d1e4f8a2b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "endpoint_assets" not in tables:
        op.create_table(
            "endpoint_assets",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("asset_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("agent_id", sa.String(), nullable=False),
            sa.Column("hostname", sa.String(), nullable=False),
            sa.Column("platform", sa.String(), nullable=False),
            sa.Column("os_version", sa.String(), nullable=True),
            sa.Column("ip_addresses", sa.JSON(), nullable=False),
            sa.Column("software", sa.JSON(), nullable=False),
            sa.Column("tags", sa.JSON(), nullable=False),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.UniqueConstraint("tenant_id", "agent_id", name="uq_endpoint_asset_tenant_agent"),
        )
        op.create_index("ix_endpoint_assets_asset_id", "endpoint_assets", ["asset_id"])
        op.create_index("ix_endpoint_assets_tenant_id", "endpoint_assets", ["tenant_id"])
        op.create_index("ix_endpoint_assets_agent_id", "endpoint_assets", ["agent_id"])
        op.create_index("ix_endpoint_assets_hostname", "endpoint_assets", ["hostname"])
        op.create_index("ix_endpoint_assets_last_seen", "endpoint_assets", ["last_seen"])

    if "host_integrity_observations" not in tables:
        op.create_table(
            "host_integrity_observations",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("observation_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("asset_id", sa.String(), nullable=False),
            sa.Column("agent_id", sa.String(), nullable=False),
            sa.Column("source_event_id", sa.String(), nullable=False),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("check_type", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("path", sa.String(), nullable=True),
            sa.Column("observed_hash", sa.String(), nullable=True),
            sa.Column("expected_hash", sa.String(), nullable=True),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("automatic_enforcement", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("tenant_id", "source", "source_event_id", name="uq_integrity_source_event"),
        )
        op.create_index("ix_host_integrity_observations_observation_id", "host_integrity_observations", ["observation_id"])
        op.create_index("ix_host_integrity_observations_tenant_id", "host_integrity_observations", ["tenant_id"])
        op.create_index("ix_host_integrity_observations_asset_id", "host_integrity_observations", ["asset_id"])
        op.create_index("ix_host_integrity_observations_agent_id", "host_integrity_observations", ["agent_id"])
        op.create_index("ix_host_integrity_observations_status", "host_integrity_observations", ["status"])
        op.create_index("ix_host_integrity_observations_severity", "host_integrity_observations", ["severity"])
        op.create_index("ix_host_integrity_observations_observed_at", "host_integrity_observations", ["observed_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "host_integrity_observations" in tables:
        op.drop_table("host_integrity_observations")
    if "endpoint_assets" in tables:
        op.drop_table("endpoint_assets")
