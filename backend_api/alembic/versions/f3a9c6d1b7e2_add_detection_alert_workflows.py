"""Add governed detection evidence and analyst alert workflows.

Revision ID: f3a9c6d1b7e2
Revises: e1f8d2c3b4a5
Create Date: 2026-08-18 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a9c6d1b7e2"
down_revision: Union[str, Sequence[str], None] = "e1f8d2c3b4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "detection_records" not in tables:
        op.create_table(
            "detection_records",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("detection_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("event_id", sa.String(), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=False),
            sa.Column("rule_version", sa.String(), nullable=False),
            sa.Column("correlation_id", sa.String(), nullable=True),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="detected"),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("mitre_evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("tags", sa.JSON(), nullable=False),
            sa.Column("automatic_enforcement", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("tenant_id", "event_id", "rule_id", name="uq_detection_record_event_rule"),
        )
        op.create_index("ix_detection_records_tenant_id", "detection_records", ["tenant_id"])
        op.create_index("ix_detection_records_event_id", "detection_records", ["event_id"])
        op.create_index("ix_detection_records_rule_id", "detection_records", ["rule_id"])
        op.create_index("ix_detection_records_detected_at", "detection_records", ["detected_at"])
    elif "mitre_evidence" not in {column["name"] for column in inspector.get_columns("detection_records")}:
        op.add_column(
            "detection_records",
            sa.Column("mitre_evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )

    if "analyst_alerts" not in tables:
        op.create_table(
            "analyst_alerts",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("alert_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("detection_ids", sa.JSON(), nullable=False),
            sa.Column("correlation_id", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="new"),
            sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
            sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("suppression_key", sa.String(), nullable=False),
            sa.Column("suppressed_by_alert_id", sa.String(), nullable=True),
            sa.Column("mitre_evidence", sa.JSON(), nullable=False),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("case_id", sa.String(), nullable=True),
            sa.Column("triaged_by", sa.String(), nullable=True),
        )
        op.create_index("ix_analyst_alerts_tenant_id", "analyst_alerts", ["tenant_id"])
        op.create_index("ix_analyst_alerts_status", "analyst_alerts", ["status"])
        op.create_index("ix_analyst_alerts_last_seen", "analyst_alerts", ["last_seen"])
        op.create_index("ix_analyst_alerts_suppression_key", "analyst_alerts", ["suppression_key"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "analyst_alerts" in tables:
        op.drop_table("analyst_alerts")
    if "detection_records" in tables:
        columns = {column["name"] for column in inspector.get_columns("detection_records")}
        if "mitre_evidence" in columns:
            op.drop_column("detection_records", "mitre_evidence")
