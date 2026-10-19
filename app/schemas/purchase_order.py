from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.domain import OrderStatus

class DecisionBasisInputs(BaseModel):
    current_stock: int
    safety_stock: int
    sales_history: List[int]
    lead_time_days: int
    moq: int

class DecisionBasisDemand(BaseModel):
    average_sales: float
    forecast_multiplier: float
    predicted_demand: int

class DecisionBasisQuantity(BaseModel):
    net_required: int
    suggested_qty: int
    moq_rounding_applied: bool


class DecisionBasisSupply(BaseModel):
    required_order_timing: str


class DecisionBasis(BaseModel):
    inputs: DecisionBasisInputs
    demand: DecisionBasisDemand
    quantity_calculation: DecisionBasisQuantity
    supply: DecisionBasisSupply

class PurchaseOrderProposalResponse(BaseModel):
    purchase_order_id: int
    product_id: int
    suggested_qty: int
    reasoning_summary: str
    execution_logs: List[str]
    workflow_steps: List[dict]
    decision_basis: DecisionBasis

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

class PurchaseOrderDecision(BaseModel):
    action: Literal["APPROVED", "MODIFIED", "REJECTED"]
    final_qty: int = Field(ge=0)

class DecisionMetricsResponse(BaseModel):
    total_decisions: int
    approved_count: int
    modified_count: int
    rejected_count: int

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    tenant_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
