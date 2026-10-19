from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_workflow import(
    WorkflowNodeError,
    create_scm_agent_workflow,
)

from app.services.inventory_service import InventoryService

StepCallback = Callable[[str, str, str], Awaitable[None]]

def build_workflow_steps(
    workflow_result: dict,
    initial_state: dict,
    completed_step_ids: set[str] | None = None,
    failed_step_id: str | None = None,
    error_message: str | None = None,
) -> list[dict]:
    completed_step_ids = completed_step_ids or set()

    message_by_agent = {
        "demand_agent": "예상 수요량을 산출했습니다.",
        "supplier_agent": "공급 조건을 검토했습니다.",
        "supervisor": "최종 발주 수량을 산출했습니다.",
    }

    for message in workflow_result.get("messages", []):
        if message.startswith("Demand Agent:"):
            message_by_agent["demand_agent"] = message.split(":", 1)[1].strip()
        elif message.startswith("Supplier Agent:"):
            message_by_agent["supplier_agent"] = message.split(":", 1)[1].strip()
        elif message.startswith("Supervisor Agent:"):
            message_by_agent["supervisor"] = message.split(":", 1)[1].strip()

    predicted_demand = workflow_result.get("predicted_demand", 0)
    suggested_qty = workflow_result.get("suggested_qty", 0)

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
            "input_summary": f"공급 리드타임 {initial_state['lead_time_days']}일",
            "output_summary": workflow_result.get("required_order_timing", ""),
        },
        {
            "id": "supervisor",
            "message": message_by_agent["supervisor"],
            "input_summary": (
                f"현재 재고 {initial_state['current_stock']}개 · "
                f"안전재고 {initial_state['safety_stock']}개 · "
                f"예상 수요 {predicted_demand}개 · "
                f"MOQ {initial_state['moq']}개"
            ),
            "output_summary": f"최종 발주 제안 수량 {suggested_qty}개",
        },
    ]

    for step in steps:
        if step["id"] in completed_step_ids:
            step["status"] = "completed"
        elif step["id"] == failed_step_id:
            step["status"] = "error"
            step["message"] = error_message or "단계 실행에 실패했습니다."
        else:
            step["status"] = "pending"

    return steps

class PredictionExecutionError(Exception):
    def __init__(
        self,
        failed_step_id: str,
        completed_step_ids: set[str],
    ):
        self.failed_step_id = failed_step_id
        self.completed_step_ids = completed_step_ids
        super().__init__("발주 예측 처리 중 단계 실행에 실패했습니다.")

async def execute_inventory_prediction(
    db: AsyncSession,
    product_id: int,
    tenant_id: int,
    on_step: StepCallback | None = None,
) -> dict[str, Any]:
    product = await InventoryService.get_product_with_inventory(
        db=db,
        product_id=product_id,
        tenant_id=tenant_id,
    )

    initial_state = {
        "product_id": product.id,
        "current_stock": product.current_stock,
        "safety_stock": product.safety_stock,
        "sales_history": [12, 18, 22, 30],
        "lead_time_days": getattr(product, "lead_time_days", 7),
        "moq": getattr(product, "moq", 1),
        "predicted_demand": 0,
        "required_order_timing": "",
        "suggested_qty": 0,
        "reasoning_summary": "",
        "messages": [],
    }

    workflow = create_scm_agent_workflow(on_step=on_step)
    workflow_result = dict(initial_state)
    completed_step_ids: set[str] = set()

    try:
        async for update in workflow.astream(
            initial_state,
            stream_mode="updates",
        ):
            for node_id, node_output in update.items():
                completed_step_ids.add(node_id)

                for key, value in node_output.items():
                    if key == "messages":
                        workflow_result[key] = [
                            *workflow_result.get(key, []),
                            *value,
                        ]
                    else:
                        workflow_result[key] = value
    except WorkflowNodeError as exc:
        raise PredictionExecutionError(
            failed_step_id=exc.node_id,
            completed_step_ids=completed_step_ids,
        ) from exc
    
    suggested_qty = workflow_result.get("suggested_qty", 0)
    reasoning_summary = workflow_result.get("reasoning_summary", "")
    predicted_demand = workflow_result.get("predicted_demand", 0)
    net_required = workflow_result.get("net_required", 0)

    draft_order = await InventoryService.create_purchase_order_draft(
        db=db,
        product_id=product_id,
        suggested_qty=suggested_qty,
        reasoning=reasoning_summary,
        tenant_id=tenant_id,
    )

    return {
        "purchase_order_id": draft_order.id,
        "product_id": product_id,
        "suggested_qty": draft_order.suggested_qty,
        "reasoning_summary": draft_order.reasoning_summary,
        "execution_logs": workflow_result.get("messages", []),
        "workflow_steps": build_workflow_steps(
            workflow_result,
            initial_state,
            completed_step_ids=completed_step_ids,
        ),
        "decision_basis": {
            "inputs": {
                "current_stock": initial_state["current_stock"],
                "safety_stock": initial_state["safety_stock"],
                "sales_history": initial_state["sales_history"],
                "lead_time_days": initial_state["lead_time_days"],
                "moq": initial_state["moq"],
            },
            "demand": {
                "average_sales": workflow_result.get("average_sales", 0),
                "forecast_multiplier": workflow_result.get(
                    "forecast_multiplier", 1.2
                ),
                "predicted_demand": predicted_demand,
            },
            "quantity_calculation": {
                "net_required": net_required,
                "suggested_qty": draft_order.suggested_qty,
                "moq_rounding_applied": (
                    net_required > 0
                    and draft_order.suggested_qty != net_required
                ),
            },
            "supply": {
                "required_order_timing": workflow_result.get(
                    "required_order_timing", ""
                ),
            },
        },
    }
