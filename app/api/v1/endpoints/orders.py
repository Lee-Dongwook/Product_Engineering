from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.services.inventory_service import InventoryService
from app.api.deps import get_current_user, require_roles
from app.models.tenant import User, UserRole
from app.models.product import Product
from app.core.exceptions import ProductNotFoundError
from app.models.domain import OrderStatus
from app.models.purchase_order import PurchaseOrder
from app.models.order_decision_event import OrderDecisionEvent
from app.schemas.purchase_order import (
    DecisionMetricsResponse,
    PurchaseOrderDecision,
    PurchaseOrderResponse,
    PurchaseOrderProposalResponse,
)
from app.services.prediction_service import (
    build_workflow_steps,
    execute_inventory_prediction,
    PredictionExecutionError,
)

router = APIRouter()

@router.post("/run-prediction/{product_id}", response_model=PurchaseOrderProposalResponse)
async def run_inventory_prediction(
    product_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))
):
    try:
        return await execute_inventory_prediction(
            db=db,
            product_id=product_id,
            tenant_id=current_user.tenant_id,
        )
    except PredictionExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "failed_step_id": exc.failed_step_id,
                "completed_step_ids": sorted(exc.completed_step_ids),
                "message": str(exc),
            },
        ) from exc

@router.get("/decision-metrics", response_model=DecisionMetricsResponse)
async def get_decision_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OrderDecisionEvent.action, func.count(OrderDecisionEvent.id))
        .where(OrderDecisionEvent.tenant_id == current_user.tenant_id)
        .group_by(OrderDecisionEvent.action)
    )
    counts = dict(result.all())
    approved_count = counts.get("APPROVED", 0)
    modified_count = counts.get("MODIFIED", 0)
    rejected_count = counts.get("REJECTED", 0)
    return {
        "total_decisions": approved_count + modified_count + rejected_count,
        "approved_count": approved_count,
        "modified_count": modified_count,
        "rejected_count": rejected_count,
    }


@router.patch("/{purchase_order_id}/decision", response_model=PurchaseOrderResponse)
async def decide_purchase_order(
    purchase_order_id: int,
    decision: PurchaseOrderDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
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
    db.add(
        OrderDecisionEvent(
            tenant_id=order.tenant_id,
            purchase_order_id=order.id,
            product_id=order.product_id,
            action=decision.action,
            suggested_qty=order.suggested_qty,
            final_qty=order.final_qty,
        )
    )
    await db.commit()
    await db.refresh(order)
    return order

