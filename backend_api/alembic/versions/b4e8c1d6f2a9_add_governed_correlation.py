"""Add governed tenant-scoped correlation rules and evidence.

Revision ID: b4e8c1d6f2a9
Revises: a9d4e7b2c5f8
Create Date: 2026-08-18 21:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4e8c1d6f2a9"
down_revision: Union[str, Sequence[str], None] = "a9d4e7b2c5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "governed_correlation_rules" not in tables:
        op.create_table(
            "governed_correlation_rules",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("rule_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("version", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("event_types", sa.JSON(), nullable=False),
            sa.Column("predicates", sa.JSON(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("mitre_techniques", sa.JSON(), nullable=False),
            sa.Column("mitre_tactics", sa.JSON(), nullable=False),
            sa.Column("correlation_key_fields", sa.JSON(), nullable=False),
            sa.Column("threshold", sa.Integer(), nullable=False),
            sa.Column("window_seconds", sa.Integer(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", name="uq_governed_correlation_rule_tenant_name"),
        )
        for name, columns in (
            ("ix_governed_correlation_rules_rule_id", ["rule_id"]),
            ("ix_governed_correlation_rules_tenant_id", ["tenant_id"]),
            ("ix_governed_correlation_rules_severity", ["severity"]),
            ("ix_governed_correlation_rules_enabled", ["enabled"]),
            ("ix_governed_correlation_rules_created_at", ["created_at"]),
            ("ix_governed_correlation_rules_updated_at", ["updated_at"]),
        ):
            op.create_index(name, "governed_correlation_rules", columns)
    if "correlation_match_evidence" not in tables:
        op.create_table(
            "correlation_match_evidence",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("match_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=False),
            sa.Column("event_id", sa.String(), nullable=False),
            sa.Column("correlation_key", sa.String(length=64), nullable=False),
            sa.Column("matched_predicates", sa.JSON(), nullable=False),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("detection_id", sa.String(), nullable=True),
            sa.UniqueConstraint("tenant_id", "rule_id", "event_id", name="uq_correlation_match_event"),
        )
        for name, columns in (
            ("ix_correlation_match_evidence_match_id", ["match_id"]),
            ("ix_correlation_match_evidence_tenant_id", ["tenant_id"]),
            ("ix_correlation_match_evidence_rule_id", ["rule_id"]),
            ("ix_correlation_match_evidence_event_id", ["event_id"]),
            ("ix_correlation_match_evidence_correlation_key", ["correlation_key"]),
            ("ix_correlation_match_evidence_evaluated_at", ["evaluated_at"]),
            ("ix_correlation_match_evidence_detection_id", ["detection_id"]),
        ):
            op.create_index(name, "correlation_match_evidence", columns)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("correlation_match_evidence", "governed_correlation_rules"):
        if table in tables:
            op.drop_table(table)
