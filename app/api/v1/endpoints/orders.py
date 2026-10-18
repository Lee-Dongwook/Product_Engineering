from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.services.inventory_service import InventoryService
from app.services.agent_workflow import create_scm_agent_workflow
from app.api.deps import get_current_user, require_roles
from app.models.tenant import User, UserRole
from app.models.product import Product
from app.core.exceptions import ProductNotFoundError
from app.models.domain import OrderStatus
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import PurchaseOrderDecision, PurchaseOrderResponse

router = APIRouter()
scm_workflow = create_scm_agent_workflow()

@router.post("/run-prediction/{product_id}")
async def run_inventory_prediction(
    product_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    product = await InventoryService.get_product_with_inventory(
        db=db, 
        product_id=product_id, 
        tenant_id=current_user.tenant_id
    )

    lead_time = getattr(product, "lead_time_days", 7)
    moq = getattr(product, "moq", 1)

    initial_state = {
        "product_id": product.id,
        "current_stock": product.current_stock,
        "safety_stock": product.safety_stock,
        "sales_history": [12, 18, 22, 30],
        "lead_time_days": lead_time,
        "moq": moq,
        "predicted_demand": 0,
        "required_order_timing": "",
        "suggested_qty": 0,
        "reasoning_summary": "",
        "messages": []
    }

    workflow_result = await scm_workflow.ainvoke(initial_state)
    suggested_qty = workflow_result.get("suggested_qty", 0)
    reasoning_summary = workflow_result.get("reasoning_summary", "")

    draft_order = await InventoryService.create_purchase_order_draft(
        db=db,
        product_id=product_id,
        suggested_qty=suggested_qty,
        reasoning=reasoning_summary,
        tenant_id=current_user.tenant_id
    )

    return {
        "purchase_order_id": draft_order.id,
        "product_id": product_id,
        "suggested_qty": draft_order.suggested_qty,
        "reasoning_summary": draft_order.reasoning_summary,
        "execution_logs": workflow_result.get("messages", [])
    }


@router.patch("/{purchase_order_id}/decision", response_model=PurchaseOrderResponse)
async def decide_purchase_order(
    purchase_order_id: int,
    decision: PurchaseOrderDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
):
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == current_user.tenant_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Purchase order is already decided")

    order.final_qty = 0 if decision.action == "REJECTED" else decision.final_qty
    order.status = OrderStatus.REJECTED if decision.action == "REJECTED" else OrderStatus.APPROVED
    await db.commit()
    await db.refresh(order)
    return order

