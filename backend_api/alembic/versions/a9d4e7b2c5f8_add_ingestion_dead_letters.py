"""Add durable canonical-ingestion dead-letter evidence.

Revision ID: a9d4e7b2c5f8
Revises: f8c3b6e1d4a2
Create Date: 2026-08-18 19:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9d4e7b2c5f8"
down_revision: Union[str, Sequence[str], None] = "f8c3b6e1d4a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ingestion_dead_letters" in set(inspector.get_table_names()):
        return
    op.create_table(
        "ingestion_dead_letters",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dead_letter_id", sa.String(), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=True),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("partition", sa.Integer(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=False),
        sa.Column("message_hash", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(), nullable=False),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replayed_by", sa.String(), nullable=True),
        sa.UniqueConstraint("topic", "partition", "offset", name="uq_ingestion_dead_letter_delivery"),
    )
    for name, columns in (
        ("ix_ingestion_dead_letters_dead_letter_id", ["dead_letter_id"]),
        ("ix_ingestion_dead_letters_tenant_id", ["tenant_id"]),
        ("ix_ingestion_dead_letters_event_id", ["event_id"]),
        ("ix_ingestion_dead_letters_message_hash", ["message_hash"]),
        ("ix_ingestion_dead_letters_error_code", ["error_code"]),
        ("ix_ingestion_dead_letters_status", ["status"]),
        ("ix_ingestion_dead_letters_first_failed_at", ["first_failed_at"]),
        ("ix_ingestion_dead_letters_last_failed_at", ["last_failed_at"]),
    ):
        op.create_index(name, "ingestion_dead_letters", columns)


def downgrade() -> None:
    bind = op.get_bind()
    if "ingestion_dead_letters" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("ingestion_dead_letters")
