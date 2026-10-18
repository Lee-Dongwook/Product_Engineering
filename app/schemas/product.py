from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProductBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    current_stock: int = 0
    safety_stock: int = 10
    unit_cost: float
    supplier_id: Optional[int] = None

class ProductCreate(ProductBase):
    tenant_id: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    current_stock: Optional[int] = None
    safety_stock: Optional[int] = None
    unit_cost: Optional[float] = None
    supplier_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)
