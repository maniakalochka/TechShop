from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_inventory_schema"
down_revision: str | Sequence[str] | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_balances",
        sa.Column("product_id", sa.UUID(), primary_key=True),
        sa.Column("available_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "available_quantity >= 0", name="ck_stock_balances_available_non_negative"
        ),
        sa.CheckConstraint(
            "reserved_quantity >= 0", name="ck_stock_balances_reserved_non_negative"
        ),
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("available_after", sa.Integer(), nullable=False),
        sa.Column("reserved_after", sa.Integer(), nullable=False),
        sa.Column("reference_key", sa.String(255), nullable=False, unique=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_table(
        "request_deduplications",
        sa.Column("idempotency_key", sa.String(255), primary_key=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "reservations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("order_id", sa.UUID(), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "reservation_items",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("reservation_id", sa.UUID(), sa.ForeignKey("reservations.id"), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "inbox_messages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("consumer_name", sa.String(128), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("consumer_name", "event_id", name="uq_inbox_consumer_event"),
    )
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("routing_key", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "outbox_messages",
        "inbox_messages",
        "reservation_items",
        "reservations",
        "request_deduplications",
        "stock_movements",
        "stock_balances",
    ):
        op.drop_table(table)
