from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum

from app.models.domain import Base, OrderStatus


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    suggested_qty = Column(Integer, nullable=False)     
    final_qty = Column(Integer, nullable=True)          
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    reasoning_summary = Column(String(500))            
    created_at = Column(DateTime, default=datetime.utcnow)
