"""Add response proposal policies and telemetry replication receipts.

Revision ID: c9f2a5e7b3d1
Revises: b4e8c1d6f2a9
Create Date: 2026-08-18 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9f2a5e7b3d1"
down_revision: Union[str, Sequence[str], None] = "b4e8c1d6f2a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "response_automation_policies" not in tables:
        op.create_table(
            "response_automation_policies",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("policy_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("trigger_rule_ids", sa.JSON(), nullable=False),
            sa.Column("minimum_severity", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("target", sa.String(), nullable=False),
            sa.Column("asset_id", sa.String(), nullable=True),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", name="uq_response_automation_policy_tenant_name"),
        )
        for name, columns in (
            ("ix_response_automation_policies_policy_id", ["policy_id"]),
            ("ix_response_automation_policies_tenant_id", ["tenant_id"]),
            ("ix_response_automation_policies_enabled", ["enabled"]),
        ):
            op.create_index(name, "response_automation_policies", columns)
    if "telemetry_replication_targets" not in tables:
        op.create_table(
            "telemetry_replication_targets",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("target_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("target_region", sa.String(), nullable=False),
            sa.Column("stream_name", sa.String(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "target_region", "stream_name", name="uq_telemetry_replication_target"),
        )
        for name, columns in (
            ("ix_telemetry_replication_targets_target_id", ["target_id"]),
            ("ix_telemetry_replication_targets_tenant_id", ["tenant_id"]),
            ("ix_telemetry_replication_targets_target_region", ["target_region"]),
            ("ix_telemetry_replication_targets_enabled", ["enabled"]),
        ):
            op.create_index(name, "telemetry_replication_targets", columns)
    if "telemetry_replication_receipts" not in tables:
        op.create_table(
            "telemetry_replication_receipts",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("receipt_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("target_id", sa.String(), nullable=False),
            sa.Column("event_id", sa.String(), nullable=False),
            sa.Column("source_region", sa.String(), nullable=False),
            sa.Column("target_region", sa.String(), nullable=False),
            sa.Column("payload_hash", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_code", sa.String(), nullable=True),
            sa.UniqueConstraint("tenant_id", "target_id", "event_id", name="uq_telemetry_replication_event"),
        )
        for name, columns in (
            ("ix_telemetry_replication_receipts_receipt_id", ["receipt_id"]),
            ("ix_telemetry_replication_receipts_tenant_id", ["tenant_id"]),
            ("ix_telemetry_replication_receipts_target_id", ["target_id"]),
            ("ix_telemetry_replication_receipts_event_id", ["event_id"]),
            ("ix_telemetry_replication_receipts_payload_hash", ["payload_hash"]),
            ("ix_telemetry_replication_receipts_status", ["status"]),
            ("ix_telemetry_replication_receipts_created_at", ["created_at"]),
        ):
            op.create_index(name, "telemetry_replication_receipts", columns)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("telemetry_replication_receipts", "telemetry_replication_targets", "response_automation_policies"):
        if table in tables:
            op.drop_table(table)
