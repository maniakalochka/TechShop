from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4d2e1f_remove_quantity_outbox"
down_revision: str | Sequence[str] | None = "b3ee21ed042f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "quantity_non_negative",
        "products",
        type_="check",
    )

    op.drop_column("products", "quantity")

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
    op.drop_table("outbox_messages")

    op.add_column(
        "products",
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_check_constraint(
        "quantity_non_negative",
        "products",
        "quantity >= 0",
    )
