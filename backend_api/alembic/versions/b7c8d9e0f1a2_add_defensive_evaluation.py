"""Add governed defensive dataset and advisory evaluation records.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-08-21 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_indexes(table: str, specs: tuple[tuple[str, list[str]], ...]) -> None:
    for name, columns in specs:
        op.create_index(name, table, columns)


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "defensive_dataset_sources" not in existing:
        op.create_table(
            "defensive_dataset_sources",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("source_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("source_type", sa.String(), nullable=False),
            sa.Column("source_uri", sa.String(), nullable=True),
            sa.Column("source_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("license_reference", sa.String(), nullable=True),
            sa.Column("operator_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("license_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("sanitization_attested", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("approved_by", sa.String(), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", "source_fingerprint", name="uq_defensive_dataset_source"),
        )
        _create_indexes(
            "defensive_dataset_sources",
            (
                ("ix_defensive_dataset_sources_source_id", ["source_id"]),
                ("ix_defensive_dataset_sources_tenant_id", ["tenant_id"]),
                ("ix_defensive_dataset_sources_source_type", ["source_type"]),
                ("ix_defensive_dataset_sources_source_fingerprint", ["source_fingerprint"]),
            ),
        )

    if "defensive_dataset_versions" not in existing:
        op.create_table(
            "defensive_dataset_versions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("dataset_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("source_id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("version", sa.String(), nullable=False),
            sa.Column("dataset_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("intended_use", sa.String(), nullable=False),
            sa.Column("sample_count", sa.Integer(), nullable=False),
            sa.Column("attack_sample_count", sa.Integer(), nullable=False),
            sa.Column("benign_sample_count", sa.Integer(), nullable=False),
            sa.Column("training_split_count", sa.Integer(), nullable=False),
            sa.Column("validation_split_count", sa.Integer(), nullable=False),
            sa.Column("test_split_count", sa.Integer(), nullable=False),
            sa.Column("sanitization_attested", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["source_id"], ["defensive_dataset_sources.source_id"]),
            sa.UniqueConstraint("tenant_id", "name", "version", name="uq_defensive_dataset_version"),
        )
        _create_indexes(
            "defensive_dataset_versions",
            (
                ("ix_defensive_dataset_versions_dataset_id", ["dataset_id"]),
                ("ix_defensive_dataset_versions_tenant_id", ["tenant_id"]),
                ("ix_defensive_dataset_versions_source_id", ["source_id"]),
                ("ix_defensive_dataset_versions_dataset_fingerprint", ["dataset_fingerprint"]),
                ("ix_defensive_dataset_versions_intended_use", ["intended_use"]),
            ),
        )

    if "defensive_dataset_samples" not in existing:
        op.create_table(
            "defensive_dataset_samples",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("sample_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("dataset_id", sa.String(), nullable=False),
            sa.Column("split", sa.String(), nullable=False),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("attack_family", sa.String(), nullable=True),
            sa.Column("mitre_techniques", sa.JSON(), nullable=False),
            sa.Column("feature_payload", sa.JSON(), nullable=False),
            sa.Column("source_record_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["dataset_id"], ["defensive_dataset_versions.dataset_id"]),
            sa.UniqueConstraint("dataset_id", "split", "source_record_fingerprint", name="uq_defensive_dataset_sample"),
        )
        _create_indexes(
            "defensive_dataset_samples",
            (
                ("ix_defensive_dataset_samples_sample_id", ["sample_id"]),
                ("ix_defensive_dataset_samples_tenant_id", ["tenant_id"]),
                ("ix_defensive_dataset_samples_dataset_id", ["dataset_id"]),
                ("ix_defensive_dataset_samples_split", ["split"]),
                ("ix_defensive_dataset_samples_label", ["label"]),
                ("ix_defensive_dataset_samples_source_record_fingerprint", ["source_record_fingerprint"]),
            ),
        )

    if "defensive_evaluation_policies" not in existing:
        op.create_table(
            "defensive_evaluation_policies",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("policy_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("minimum_precision", sa.Float(), nullable=False),
            sa.Column("minimum_recall", sa.Float(), nullable=False),
            sa.Column("maximum_false_positive_rate", sa.Float(), nullable=False),
            sa.Column("minimum_attack_samples", sa.Integer(), nullable=False),
            sa.Column("minimum_benign_samples", sa.Integer(), nullable=False),
            sa.Column("require_test_split", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "name", name="uq_defensive_evaluation_policy_tenant_name"),
        )
        _create_indexes(
            "defensive_evaluation_policies",
            (
                ("ix_defensive_evaluation_policies_policy_id", ["policy_id"]),
                ("ix_defensive_evaluation_policies_tenant_id", ["tenant_id"]),
                ("ix_defensive_evaluation_policies_enabled", ["enabled"]),
            ),
        )

    if "defensive_model_evaluations" not in existing:
        op.create_table(
            "defensive_model_evaluations",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("evaluation_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("policy_id", sa.String(), nullable=False),
            sa.Column("dataset_id", sa.String(), nullable=False),
            sa.Column("dataset_version", sa.String(), nullable=False),
            sa.Column("dataset_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("model_id", sa.String(), nullable=False),
            sa.Column("model_version", sa.String(), nullable=False),
            sa.Column("evaluated_split", sa.String(), nullable=False),
            sa.Column("true_positive", sa.Integer(), nullable=False),
            sa.Column("false_positive", sa.Integer(), nullable=False),
            sa.Column("true_negative", sa.Integer(), nullable=False),
            sa.Column("false_negative", sa.Integer(), nullable=False),
            sa.Column("precision", sa.Float(), nullable=False),
            sa.Column("recall", sa.Float(), nullable=False),
            sa.Column("false_positive_rate", sa.Float(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("rejection_reasons", sa.JSON(), nullable=False),
            sa.Column("evaluation_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("advisory_only", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("automatic_enforcement", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["policy_id"], ["defensive_evaluation_policies.policy_id"]),
            sa.ForeignKeyConstraint(["dataset_id"], ["defensive_dataset_versions.dataset_id"]),
            sa.UniqueConstraint(
                "tenant_id", "policy_id", "dataset_id", "model_id", "model_version", "evaluation_fingerprint",
                name="uq_defensive_model_evaluation",
            ),
        )
        _create_indexes(
            "defensive_model_evaluations",
            (
                ("ix_defensive_model_evaluations_evaluation_id", ["evaluation_id"]),
                ("ix_defensive_model_evaluations_tenant_id", ["tenant_id"]),
                ("ix_defensive_model_evaluations_policy_id", ["policy_id"]),
                ("ix_defensive_model_evaluations_dataset_id", ["dataset_id"]),
                ("ix_defensive_model_evaluations_dataset_fingerprint", ["dataset_fingerprint"]),
                ("ix_defensive_model_evaluations_model_id", ["model_id"]),
                ("ix_defensive_model_evaluations_evaluated_split", ["evaluated_split"]),
                ("ix_defensive_model_evaluations_status", ["status"]),
                ("ix_defensive_model_evaluations_evaluation_fingerprint", ["evaluation_fingerprint"]),
                ("ix_defensive_model_evaluations_evaluated_at", ["evaluated_at"]),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    for table in (
        "defensive_model_evaluations",
        "defensive_evaluation_policies",
        "defensive_dataset_samples",
        "defensive_dataset_versions",
        "defensive_dataset_sources",
    ):
        if table in existing:
            op.drop_table(table)
