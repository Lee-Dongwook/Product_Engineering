from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.domain import OrderStatus

class PurchaseOrderBase(BaseModel):
    product_id: int
    suggested_qty: int
    final_qty: Optional[int] = None
    status: OrderStatus = OrderStatus.DRAFT
    reasoning_summary: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    tenant_id: int

class PurchaseOrderUpdate(BaseModel):
    final_qty: Optional[int] = None
    status: Optional[OrderStatus] = None
    reasoning_summary: Optional[str] = None

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    tenant_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
