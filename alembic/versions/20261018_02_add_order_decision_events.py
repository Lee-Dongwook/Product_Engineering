"""add order decision events

Revision ID: 20261018_02
Revises: 20261018_01
Create Date: 2026-10-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20261018_02"
down_revision: Union[str, None] = "20261018_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_decision_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=10), nullable=False),
        sa.Column("suggested_qty", sa.Integer(), nullable=False),
        sa.Column("final_qty", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_order_decision_events_id", "order_decision_events", ["id"])
    op.create_index("ix_order_decision_events_tenant_id", "order_decision_events", ["tenant_id"])
    op.create_index("ix_order_decision_events_created_at", "order_decision_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_order_decision_events_created_at", table_name="order_decision_events")
    op.drop_index("ix_order_decision_events_tenant_id", table_name="order_decision_events")
    op.drop_index("ix_order_decision_events_id", table_name="order_decision_events")
    op.drop_table("order_decision_events")
