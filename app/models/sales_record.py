from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
)
from app.models.domain import Base

class SalesRecord(Base):
    __tablename__ = "sales_records"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_sales_records_quantity_positive",
        ),
        Index(
            "ix_sales_records_tenant_product_sold_at",
            "tenant_id",
            "product_id",
            "sold_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)
    sold_at = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    
