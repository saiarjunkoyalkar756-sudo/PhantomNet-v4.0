"""Add governed case and playbook lifecycle storage.

Revision ID: a4b8d2e6f9c1
Revises: f3a9c6d1b7e2
Create Date: 2026-08-18 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4b8d2e6f9c1"
down_revision: Union[str, Sequence[str], None] = "f3a9c6d1b7e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "investigation_cases" not in tables:
        op.create_table(
            "investigation_cases",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("case_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("alert_ids", sa.JSON(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="new"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("assigned_to", sa.String(), nullable=True),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("timeline", sa.JSON(), nullable=False),
        )
        op.create_index("ix_investigation_cases_tenant_id", "investigation_cases", ["tenant_id"])
        op.create_index("ix_investigation_cases_case_id", "investigation_cases", ["case_id"])
        op.create_index("ix_investigation_cases_status", "investigation_cases", ["status"])
        op.create_index("ix_investigation_cases_updated_at", "investigation_cases", ["updated_at"])

    if "case_playbook_runs" not in tables:
        op.create_table(
            "case_playbook_runs",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("run_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("case_id", sa.String(), nullable=False),
            sa.Column("playbook_id", sa.String(), nullable=False),
            sa.Column("playbook_version", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="requested"),
            sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("requested_by", sa.String(), nullable=False),
            sa.Column("approved_by", sa.String(), nullable=True),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("evidence", sa.JSON(), nullable=False),
        )
        op.create_index("ix_case_playbook_runs_tenant_id", "case_playbook_runs", ["tenant_id"])
        op.create_index("ix_case_playbook_runs_case_id", "case_playbook_runs", ["case_id"])
        op.create_index("ix_case_playbook_runs_run_id", "case_playbook_runs", ["run_id"])
        op.create_index("ix_case_playbook_runs_status", "case_playbook_runs", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "case_playbook_runs" in tables:
        op.drop_table("case_playbook_runs")
    if "investigation_cases" in tables:
        op.drop_table("investigation_cases")
