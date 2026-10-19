from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.services.inventory_service import InventoryService
from app.services.agent_workflow import (
    create_scm_agent_workflow,
    WorkflowNodeError,
)
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
    execute_inventory_prediction,
    PredictionExecutionError,
)

router = APIRouter()
scm_workflow = create_scm_agent_workflow()

def build_workflow_steps(
    workflow_result: dict,
    initial_state: dict,
    completed_step_ids: set[str] | None = None,
    failed_step_id: str | None = None,
    error_message: str | None = None,
) -> list[dict]:
    completed_step_ids = completed_step_ids or set()
    
    messages = workflow_result.get("messages", [])
    message_by_agent = {
        "demand_agent": "예상 수요량을 산출했습니다.",
        "supplier_agent": "공급 조건을 검토했습니다.",
        "supervisor": "최종 발주 수량을 산출했습니다.",
    }

    for message in messages:
        if message.startswith("Demand Agent:"):
            message_by_agent["demand_agent"] = message.split(":", 1)[1].strip()
        elif message.startswith("Supplier Agent:"):
            message_by_agent["supplier_agent"] = message.split(":", 1)[1].strip()
        elif message.startswith("Supervisor Agent:"):
            message_by_agent["supervisor"] = message.split(":", 1)[1].strip()

    predicted_demand = workflow_result.get("predicted_demand", 0)
    timing = workflow_result.get("required_order_timing", "")
    suggested_qty = workflow_result.get("suggested_qty", 0)

    current_stock = initial_state.get("current_stock", 0)
    safety_stock = initial_state.get("safety_stock", 0)
    lead_time = initial_state.get("lead_time_days", 7)
    moq = initial_state.get("moq", 1)

    steps = [
        {
            "id": "demand_agent",
            "message": message_by_agent["demand_agent"],
            "input_summary": (
                f"판매 이력 {len(initial_state.get('sales_history', []))}개 항목"
            ),
            "output_summary": f"예상 월간 수요량 {predicted_demand}개",
        },
        {
            "id": "supplier_agent",
            "message": message_by_agent["supplier_agent"],
            "input_summary": f"공급 리드타임 {lead_time}일",
            "output_summary": timing,
        },
        {
            "id": "supervisor",
            "message": message_by_agent["supervisor"],
            "input_summary": (
                f"현재 재고 {current_stock}개 · "
                f"안전재고 {safety_stock}개 · "
                f"예상 수요 {predicted_demand}개 · "
                f"MOQ {moq}개"
            ),
            "output_summary": f"최종 발주 제안 수량 {suggested_qty}개",
        },
    ]

    for step in steps:
        step_id = step["id"]

        if step_id in completed_step_ids:
            step["status"] = "completed"
        elif step_id == failed_step_id:
            step["status"] = "error"
            step["message"] = error_message or "단계 실행에 실패했습니다."
        else:
            step["status"] = "pending"
        
    
    return steps

@router.post("/run-prediction/{product_id}", response_model=PurchaseOrderProposalResponse)
async def run_inventory_prediction(
    product_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
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

