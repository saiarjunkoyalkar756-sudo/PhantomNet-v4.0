"""Add tenant-scoped read-only integrated evidence records.

Revision ID: e4f5a6b7c8d9
Revises: f1a2b3c4d5e6
Create Date: 2026-08-19 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if "integrated_evidence" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "integrated_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("source_kind", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("payload_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("read_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("automatic_enforcement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint(
            "tenant_id",
            "source_kind",
            "source_name",
            "source_record_id",
            "payload_fingerprint",
            name="uq_integrated_evidence_source_fingerprint",
        ),
    )
    for name, columns in (
        ("ix_integrated_evidence_evidence_id", ["evidence_id"]),
        ("ix_integrated_evidence_tenant_id", ["tenant_id"]),
        ("ix_integrated_evidence_source_kind", ["source_kind"]),
        ("ix_integrated_evidence_source_name", ["source_name"]),
        ("ix_integrated_evidence_source_record_id", ["source_record_id"]),
        ("ix_integrated_evidence_observed_at", ["observed_at"]),
        ("ix_integrated_evidence_collected_at", ["collected_at"]),
        ("ix_integrated_evidence_payload_fingerprint", ["payload_fingerprint"]),
    ):
        op.create_index(name, "integrated_evidence", columns)


def downgrade() -> None:
    bind = op.get_bind()
    if "integrated_evidence" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("integrated_evidence")
