"""Add governed containment lifecycle tables.

Revision ID: f8c3b6e1d4a2
Revises: e6f2a8c4d9b1
Create Date: 2026-08-18 17:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8c3b6e1d4a2"
down_revision: Union[str, Sequence[str], None] = "e6f2a8c4d9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "containment_requests" not in tables:
        op.create_table(
            "containment_requests",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("request_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("target", sa.String(), nullable=False),
            sa.Column("asset_id", sa.String(), nullable=True),
            sa.Column("playbook_id", sa.String(), nullable=True),
            sa.Column("requested_by", sa.String(), nullable=False),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="requested"),
            sa.Column("idempotency_key", sa.String(), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("automatic_enforcement", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_containment_tenant_idempotency"),
        )
        for name, columns in (("ix_containment_requests_request_id", ["request_id"]), ("ix_containment_requests_tenant_id", ["tenant_id"]), ("ix_containment_requests_target", ["target"]), ("ix_containment_requests_asset_id", ["asset_id"]), ("ix_containment_requests_requested_at", ["requested_at"]), ("ix_containment_requests_status", ["status"])):
            op.create_index(name, "containment_requests", columns)

    if "containment_approvals" not in tables:
        op.create_table(
            "containment_approvals",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("approval_id", sa.String(), nullable=False, unique=True),
            sa.Column("request_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("decided_by", sa.String(), nullable=False),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reason", sa.String(), nullable=False),
        )
        for name, columns in (("ix_containment_approvals_approval_id", ["approval_id"]), ("ix_containment_approvals_request_id", ["request_id"]), ("ix_containment_approvals_tenant_id", ["tenant_id"]), ("ix_containment_approvals_decided_at", ["decided_at"])):
            op.create_index(name, "containment_approvals", columns)

    if "containment_executions" not in tables:
        op.create_table(
            "containment_executions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("execution_id", sa.String(), nullable=False, unique=True),
            sa.Column("request_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("approval_id", sa.String(), nullable=False),
            sa.Column("adapter", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("verification", sa.JSON(), nullable=False),
            sa.Column("rollback_available", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("rolled_back", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("audit_record_hash", sa.String(), nullable=True),
        )
        for name, columns in (("ix_containment_executions_execution_id", ["execution_id"]), ("ix_containment_executions_request_id", ["request_id"]), ("ix_containment_executions_tenant_id", ["tenant_id"]), ("ix_containment_executions_status", ["status"]), ("ix_containment_executions_executed_at", ["executed_at"])):
            op.create_index(name, "containment_executions", columns)

    if "containment_audit_records" not in tables:
        op.create_table(
            "containment_audit_records",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("record_id", sa.String(), nullable=False, unique=True),
            sa.Column("timestamp", sa.String(), nullable=False),
            sa.Column("actor_id", sa.String(), nullable=True),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("previous_hash", sa.String(), nullable=False),
            sa.Column("record_hash", sa.String(), nullable=False, unique=True),
            sa.Column("signature", sa.String(), nullable=True),
            sa.Column("signature_key_id", sa.String(), nullable=True),
        )
        for name, columns in (("ix_containment_audit_records_tenant_id", ["tenant_id"]), ("ix_containment_audit_records_record_id", ["record_id"]), ("ix_containment_audit_records_action", ["action"])):
            op.create_index(name, "containment_audit_records", columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    for table in ("containment_audit_records", "containment_executions", "containment_approvals", "containment_requests"):
        if table in tables:
            op.drop_table(table)
