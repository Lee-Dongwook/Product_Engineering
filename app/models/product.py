from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.models.domain import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), index=True)
    current_stock = Column(Integer, default=0, nullable=False)
    safety_stock = Column(Integer, default=10, nullable=False)  
    unit_cost = Column(Float, nullable=False)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier = relationship("Supplier", back_populates="products")
    inventory_logs = relationship("InventoryLog", back_populates="product")
    tenant = relationship("Tenant", back_populates="products")

