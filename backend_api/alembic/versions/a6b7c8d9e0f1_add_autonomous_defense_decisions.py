"""Add tenant-scoped autonomous defense policies and immutable decisions.

Revision ID: a6b7c8d9e0f1
Revises: e4f5a6b7c8d9
Create Date: 2026-08-21 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "autonomous_defense_policies" not in existing:
        op.create_table(
            "autonomous_defense_policies",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("policy_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("trigger_rule_ids", sa.JSON(), nullable=False),
            sa.Column("minimum_severity", sa.String(), nullable=False),
            sa.Column("decision_mode", sa.String(), nullable=False),
            sa.Column("minimum_confidence", sa.Float(), nullable=False),
            sa.Column("minimum_evidence_count", sa.Integer(), nullable=False),
            sa.Column("required_evidence_kinds", sa.JSON(), nullable=False),
            sa.Column("cooldown_seconds", sa.Integer(), nullable=False),
            sa.Column("max_decisions_per_hour", sa.Integer(), nullable=False),
            sa.Column("containment_action", sa.String(), nullable=True),
            sa.Column("target", sa.String(), nullable=True),
            sa.Column("asset_id", sa.String(), nullable=True),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", name="uq_autonomous_defense_policy_tenant_name"),
        )
        for name, columns in (
            ("ix_autonomous_defense_policies_policy_id", ["policy_id"]),
            ("ix_autonomous_defense_policies_tenant_id", ["tenant_id"]),
            ("ix_autonomous_defense_policies_enabled", ["enabled"]),
            ("ix_autonomous_defense_policies_decision_mode", ["decision_mode"]),
        ):
            op.create_index(name, "autonomous_defense_policies", columns)

    if "autonomous_defense_decisions" not in existing:
        op.create_table(
            "autonomous_defense_decisions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("decision_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("policy_id", sa.String(), nullable=False),
            sa.Column("detection_id", sa.String(), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("decision_mode", sa.String(), nullable=False),
            sa.Column("outcome", sa.String(), nullable=False),
            sa.Column("evidence_ids", sa.JSON(), nullable=False),
            sa.Column("evidence_kinds", sa.JSON(), nullable=False),
            sa.Column("reasons", sa.JSON(), nullable=False),
            sa.Column("containment_request_id", sa.String(), nullable=True),
            sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("decision_hash", sa.String(length=64), nullable=False),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["policy_id"], ["autonomous_defense_policies.policy_id"]),
            sa.UniqueConstraint(
                "tenant_id",
                "policy_id",
                "detection_id",
                "decision_hash",
                name="uq_autonomous_defense_decision",
            ),
        )
        for name, columns in (
            ("ix_autonomous_defense_decisions_decision_id", ["decision_id"]),
            ("ix_autonomous_defense_decisions_tenant_id", ["tenant_id"]),
            ("ix_autonomous_defense_decisions_policy_id", ["policy_id"]),
            ("ix_autonomous_defense_decisions_detection_id", ["detection_id"]),
            ("ix_autonomous_defense_decisions_rule_id", ["rule_id"]),
            ("ix_autonomous_defense_decisions_severity", ["severity"]),
            ("ix_autonomous_defense_decisions_decision_mode", ["decision_mode"]),
            ("ix_autonomous_defense_decisions_outcome", ["outcome"]),
            ("ix_autonomous_defense_decisions_containment_request_id", ["containment_request_id"]),
            ("ix_autonomous_defense_decisions_decision_hash", ["decision_hash"]),
            ("ix_autonomous_defense_decisions_decided_at", ["decided_at"]),
        ):
            op.create_index(name, "autonomous_defense_decisions", columns)


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    if "autonomous_defense_decisions" in existing:
        op.drop_table("autonomous_defense_decisions")
    if "autonomous_defense_policies" in existing:
        op.drop_table("autonomous_defense_policies")
