"""Add signed Wazuh Active Response endpoint receipts.

Revision ID: d4e7f1a9c2b5
Revises: c9f2a5e7b3d1
Create Date: 2026-08-19 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e7f1a9c2b5"
down_revision: Union[str, Sequence[str], None] = "c9f2a5e7b3d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if "wazuh_response_receipts" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "wazuh_response_receipts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("receipt_id", sa.String(), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("approval_id", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("wazuh_agent_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("network_state", sa.String(), nullable=False),
        sa.Column("command_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("nonce", sa.String(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature", sa.String(length=64), nullable=False),
        sa.Column("signature_key_id", sa.String(), nullable=False),
        sa.UniqueConstraint("tenant_id", "nonce", name="uq_wazuh_response_receipt_tenant_nonce"),
    )
    for name, columns in (
        ("ix_wazuh_response_receipts_receipt_id", ["receipt_id"]),
        ("ix_wazuh_response_receipts_tenant_id", ["tenant_id"]),
        ("ix_wazuh_response_receipts_request_id", ["request_id"]),
        ("ix_wazuh_response_receipts_approval_id", ["approval_id"]),
        ("ix_wazuh_response_receipts_asset_id", ["asset_id"]),
        ("ix_wazuh_response_receipts_wazuh_agent_id", ["wazuh_agent_id"]),
        ("ix_wazuh_response_receipts_action", ["action"]),
        ("ix_wazuh_response_receipts_network_state", ["network_state"]),
        ("ix_wazuh_response_receipts_command_fingerprint", ["command_fingerprint"]),
        ("ix_wazuh_response_receipts_observed_at", ["observed_at"]),
        ("ix_wazuh_response_receipts_received_at", ["received_at"]),
    ):
        op.create_index(name, "wazuh_response_receipts", columns)


def downgrade() -> None:
    bind = op.get_bind()
    if "wazuh_response_receipts" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("wazuh_response_receipts")
