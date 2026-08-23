"""add signed telemetry authentication

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-08-23 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "telemetry_agent_credentials" not in tables:
        op.create_table(
            "telemetry_agent_credentials",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("credential_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("agent_id", sa.String(length=128), nullable=False),
            sa.Column("key_id", sa.String(length=128), nullable=False),
            sa.Column("public_key_pem", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.UniqueConstraint("tenant_id", "agent_id", "key_id", name="uq_telemetry_agent_credential"),
        )
        for name, columns in (
            ("ix_telemetry_agent_credentials_credential_id", ["credential_id"]),
            ("ix_telemetry_agent_credentials_tenant_id", ["tenant_id"]),
            ("ix_telemetry_agent_credentials_agent_id", ["agent_id"]),
            ("ix_telemetry_agent_credentials_key_id", ["key_id"]),
            ("ix_telemetry_agent_credentials_status", ["status"]),
        ):
            op.create_index(name, "telemetry_agent_credentials", columns)

    if "telemetry_signature_nonces" not in tables:
        op.create_table(
            "telemetry_signature_nonces",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("nonce_record_id", sa.String(), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("agent_id", sa.String(length=128), nullable=False),
            sa.Column("key_id", sa.String(length=128), nullable=False),
            sa.Column("nonce", sa.String(length=256), nullable=False),
            sa.Column("payload_sha256", sa.String(length=64), nullable=False),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.UniqueConstraint("tenant_id", "agent_id", "key_id", "nonce", name="uq_telemetry_signature_nonce"),
        )
        for name, columns in (
            ("ix_telemetry_signature_nonces_nonce_record_id", ["nonce_record_id"]),
            ("ix_telemetry_signature_nonces_tenant_id", ["tenant_id"]),
            ("ix_telemetry_signature_nonces_agent_id", ["agent_id"]),
            ("ix_telemetry_signature_nonces_key_id", ["key_id"]),
        ):
            op.create_index(name, "telemetry_signature_nonces", columns)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "telemetry_signature_nonces" in tables:
        op.drop_table("telemetry_signature_nonces")
    if "telemetry_agent_credentials" in tables:
        op.drop_table("telemetry_agent_credentials")
