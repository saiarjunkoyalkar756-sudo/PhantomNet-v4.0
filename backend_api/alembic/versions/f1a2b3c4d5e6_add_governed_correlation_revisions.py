"""Add immutable governed correlation rule revisions and suppression controls.

Revision ID: f1a2b3c4d5e6
Revises: d4e7f1a9c2b5
Create Date: 2026-08-19 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d4e7f1a9c2b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "governed_correlation_rules" in tables:
        columns = {column["name"] for column in inspector.get_columns("governed_correlation_rules")}
        if "suppression_window_seconds" not in columns:
            op.add_column(
                "governed_correlation_rules",
                sa.Column("suppression_window_seconds", sa.Integer(), nullable=False, server_default="900"),
            )
            # SQLite does not support ALTER COLUMN DROP DEFAULT. Retaining the backfill default
            # there preserves the required value; production PostgreSQL removes it as intended.
            if bind.dialect.name != "sqlite":
                op.alter_column("governed_correlation_rules", "suppression_window_seconds", server_default=None)
    if "governed_correlation_rule_revisions" not in tables:
        op.create_table(
            "governed_correlation_rule_revisions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("revision_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=False),
            sa.Column("version", sa.String(), nullable=False),
            sa.Column("definition_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("definition", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "tenant_id",
                "rule_id",
                "version",
                name="uq_governed_correlation_rule_revision_version",
            ),
        )
        for name, columns in (
            ("ix_governed_correlation_rule_revisions_revision_id", ["revision_id"]),
            ("ix_governed_correlation_rule_revisions_tenant_id", ["tenant_id"]),
            ("ix_governed_correlation_rule_revisions_rule_id", ["rule_id"]),
            ("ix_governed_correlation_rule_revisions_definition_fingerprint", ["definition_fingerprint"]),
            ("ix_governed_correlation_rule_revisions_created_at", ["created_at"]),
        ):
            op.create_index(name, "governed_correlation_rule_revisions", columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "governed_correlation_rule_revisions" in tables:
        op.drop_table("governed_correlation_rule_revisions")
    if "governed_correlation_rules" in tables:
        columns = {column["name"] for column in inspector.get_columns("governed_correlation_rules")}
        if "suppression_window_seconds" in columns:
            op.drop_column("governed_correlation_rules", "suppression_window_seconds")
