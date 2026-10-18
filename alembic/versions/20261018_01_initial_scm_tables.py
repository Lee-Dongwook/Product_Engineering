"""create initial SCM tables

Revision ID: 20261018_01
Revises:
Create Date: 2026-10-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20261018_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])
    op.create_index("ix_tenants_name", "tenants", ["name"])

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("moq", sa.Integer()),
    )
    op.create_index("ix_suppliers_id", "suppliers", ["id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "MANAGER", "VIEWER", name="userrole"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50)),
        sa.Column("current_stock", sa.Integer(), nullable=False),
        sa.Column("safety_stock", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=False),
        sa.Column("supplier_id", sa.Integer()),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.UniqueConstraint("sku"),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_category", "products", ["category"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("suggested_qty", sa.Integer(), nullable=False),
        sa.Column("final_qty", sa.Integer()),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "APPROVED", "REJECTED", "ORDERED", name="orderstatus"),
        ),
        sa.Column("reasoning_summary", sa.String(length=500)),
        sa.Column("created_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("ix_purchase_orders_id", "purchase_orders", ["id"])
    op.create_index("ix_purchase_orders_tenant_id", "purchase_orders", ["tenant_id"])

    op.create_table(
        "inventory_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("change_qty", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_inventory_logs_id", "inventory_logs", ["id"])
    op.create_index("ix_inventory_logs_created_at", "inventory_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_inventory_logs_created_at", table_name="inventory_logs")
    op.drop_index("ix_inventory_logs_id", table_name="inventory_logs")
    op.drop_table("inventory_logs")
    op.drop_index("ix_purchase_orders_tenant_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_suppliers_id", table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_index("ix_tenants_name", table_name="tenants")
    op.drop_index("ix_tenants_id", table_name="tenants")
    op.drop_table("tenants")
    sa.Enum(name="orderstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
