from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

"""Add product and category models.

Revision ID: b3ee21ed042f
Revises:
Create Date: 2026-08-17 17:18:38.679249
"""


# revision identifiers, used by Alembic.
revision: str = "b3ee21ed042f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
    )
    op.create_index(op.f("ix_categories_created_date"), "categories", ["created_date"])
    op.create_index(op.f("ix_categories_updated_date"), "categories", ["updated_date"])
    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_date", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price > 0", name=op.f("ck_products_price_positive")),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_products_quantity_non_negative")),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_products_category_id_categories")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        sa.UniqueConstraint("name", name=op.f("uq_products_name")),
    )
    op.create_index(op.f("ix_products_created_date"), "products", ["created_date"])
    op.create_index(op.f("ix_products_updated_date"), "products", ["updated_date"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_products_updated_date"), table_name="products")
    op.drop_index(op.f("ix_products_created_date"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_categories_updated_date"), table_name="categories")
    op.drop_index(op.f("ix_categories_created_date"), table_name="categories")
    op.drop_table("categories")
