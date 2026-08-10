"""initial schema: inventory_items, suppliers, recipes, stock_movements

Revision ID: 0001
Revises:
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from restaurant_database.guid import GUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", GUID(), primary_key=True, comment="Identificador único universal (UUIDv7)"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", GUID(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "suppliers",
        *_base_columns(),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("contact_email", sa.String(length=150), nullable=True),
    )
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"])

    op.create_table(
        "inventory_items",
        *_base_columns(),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "unit", sa.Enum("KG", "G", "L", "ML", "UN", name="inventoryunit"), nullable=False
        ),
        sa.Column("current_quantity", sa.Float(), nullable=False),
        sa.Column("minimum_quantity", sa.Float(), nullable=False),
        sa.Column("supplier_id", GUID(), nullable=True),
    )
    op.create_index("ix_inventory_items_tenant_id", "inventory_items", ["tenant_id"])

    op.create_table(
        "recipes",
        *_base_columns(),
        sa.Column("product_id", GUID(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
    )
    op.create_index("ix_recipes_tenant_id", "recipes", ["tenant_id"])
    op.create_index("ix_recipes_product_id", "recipes", ["product_id"], unique=True)

    op.create_table(
        "stock_movements",
        *_base_columns(),
        sa.Column("inventory_item_id", GUID(), nullable=False),
        sa.Column(
            "movement_type",
            sa.Enum(
                "ENTRY",
                "LOSS",
                "RETURN",
                "COUNT_ADJUSTMENT",
                "SALE_DEDUCTION",
                name="stockmovementtype",
            ),
            nullable=False,
        ),
        sa.Column("quantity_delta", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("order_id", GUID(), nullable=True),
    )
    op.create_index("ix_stock_movements_tenant_id", "stock_movements", ["tenant_id"])
    op.create_index(
        "ix_stock_movements_inventory_item_id", "stock_movements", ["inventory_item_id"]
    )


def downgrade() -> None:
    op.drop_table("stock_movements")
    op.drop_table("recipes")
    op.drop_table("inventory_items")
    op.drop_table("suppliers")
    sa.Enum(name="stockmovementtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="inventoryunit").drop(op.get_bind(), checkfirst=True)
