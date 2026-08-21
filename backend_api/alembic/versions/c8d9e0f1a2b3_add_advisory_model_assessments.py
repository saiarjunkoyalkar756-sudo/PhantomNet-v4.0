"""Add immutable advisory model assessment records.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-08-21 11:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if "advisory_model_assessments" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "advisory_model_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("assessment_id", sa.String(), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("detection_id", sa.String(), nullable=False),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("evaluation_id", sa.String(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("recommended_mode", sa.String(), nullable=False),
        sa.Column("assessment_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("advisory_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("automatic_enforcement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["evaluation_id"], ["defensive_model_evaluations.evaluation_id"]),
        sa.UniqueConstraint(
            "tenant_id", "detection_id", "model_id", "model_version", "assessment_fingerprint",
            name="uq_advisory_model_assessment",
        ),
    )
    for name, columns in (
        ("ix_advisory_model_assessments_assessment_id", ["assessment_id"]),
        ("ix_advisory_model_assessments_tenant_id", ["tenant_id"]),
        ("ix_advisory_model_assessments_detection_id", ["detection_id"]),
        ("ix_advisory_model_assessments_model_id", ["model_id"]),
        ("ix_advisory_model_assessments_evaluation_id", ["evaluation_id"]),
        ("ix_advisory_model_assessments_classification", ["classification"]),
        ("ix_advisory_model_assessments_recommended_mode", ["recommended_mode"]),
        ("ix_advisory_model_assessments_assessment_fingerprint", ["assessment_fingerprint"]),
        ("ix_advisory_model_assessments_assessed_at", ["assessed_at"]),
    ):
        op.create_index(name, "advisory_model_assessments", columns)


def downgrade() -> None:
    bind = op.get_bind()
    if "advisory_model_assessments" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("advisory_model_assessments")
