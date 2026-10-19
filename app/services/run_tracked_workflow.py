from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase_order import PurchaseOrder
from app.services import summarize_step_output
from app.services.workflow_execution_service import (
    WorkflowExecutionService,
)
from app.services.agent_workflow import create_scm_agent_workflow

async def create_purchase_order(
    result: dict[str, Any],
    db: AsyncSession,
):
    purchase_order = PurchaseOrder(
        product_id=result["product_id"],
        quantity=result["suggested_qty"],
        status="DRAFT",
        reasoning_summary=result["reasoning_summary"],
    )

    db.add(purchase_order)
    await db.flush()

    return purchase_order

async def run_tracked_workflow(
    product_id: int,
    initial_state: dict[str, Any],
    execution_service: WorkflowExecutionService,
    publish_sse,
):
    execution = await execution_service.start(product_id)
    execution_id = execution.execution_id

    async def on_step(
        step_id: str,
        status: str,
        message: str,
    ) -> None:
        await execution_service.update_step(
            execution_id=execution_id,
            step_id=step_id,
            status=status.upper(),
            message=message,
        )

        await publish_sse(
            product_id=product_id,
            event={
                "execution_id": execution_id,
                "step_id": step_id,
                "status": status,
                "message": message,
            },
        )

    async def on_step_result(
        step_id: str,
        result: dict[str, Any],
    ) -> None:
        output = summarize_step_output(step_id, result)

        await execution_service.update_step(
            execution_id=execution_id,
            step_id=step_id,
            status="COMPLETED",
            output=output,
        )

    try:
        graph = create_scm_agent_workflow(on_step=on_step)
        result = await graph.ainovke(initial_state)

        purchase_order = await create_purchase_order(result)

        await execution_service.complete(
            execution_id=execution_id,
            purchase_order_id=purchase_order.id,
        )

        return {
            "execution_id": execution_id,
            "result": result,
            "purchase_order_id": purchase_order.id,
        }
    except Exception as exc:
        await execution_service.fail(
            execution_id=execution_id,
            error_message=str(exc),
        )
        raise
