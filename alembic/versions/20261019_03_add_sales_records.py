
"""add sales records table

Revision ID: 20261019_03
Revises: 20261018_02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20261019_03"
down_revision: Union[str, None] = "20261018_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("sold_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_sales_records_quantity_positive",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_index(
        "ix_sales_records_id",
        "sales_records",
        ["id"],
    )
    op.create_index(
        "ix_sales_records_tenant_id",
        "sales_records",
        ["tenant_id"],
    )
    op.create_index(
        "ix_sales_records_product_id",
        "sales_records",
        ["product_id"],
    )
    op.create_index(
        "ix_sales_records_sold_at",
        "sales_records",
        ["sold_at"],
    )
    op.create_index(
        "ix_sales_records_tenant_product_sold_at",
        "sales_records",
        ["tenant_id", "product_id", "sold_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sales_records_tenant_product_sold_at",
        table_name="sales_records",
    )
    op.drop_index(
        "ix_sales_records_sold_at",
        table_name="sales_records",
    )
    op.drop_index(
        "ix_sales_records_product_id",
        table_name="sales_records",
    )
    op.drop_index(
        "ix_sales_records_tenant_id",
        table_name="sales_records",
    )
    op.drop_index(
        "ix_sales_records_id",
        table_name="sales_records",
    )
    op.drop_table("sales_records")
