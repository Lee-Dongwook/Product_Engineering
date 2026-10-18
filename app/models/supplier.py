from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.domain import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lead_time_days = Column(Integer, nullable=False, default=7) 
    moq = Column(Integer, default=1)                            
    products = relationship("Product", back_populates="supplier")
