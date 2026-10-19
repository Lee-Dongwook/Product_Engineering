import inspect
from typing import Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.summarize_step_output import summarize_step_output
from app.services.workflow_execution_service import (
    WorkflowExecutionService,
)
from app.services.agent_workflow import create_scm_agent_workflow
from app.services.inventory_service import InventoryService

async def create_purchase_order(
    result: dict[str, Any],
    db: AsyncSession,
    tenant_id: int,
    product_id: int | None = None,
):
    pid = result.get("product_id") or product_id
    return await InventoryService.create_purchase_order_draft(
        db=db,
        product_id=pid,
        suggested_qty=result.get("suggested_qty", 0),
        reasoning=result.get("reasoning_summary", ""),
        tenant_id=tenant_id,
    )

async def run_tracked_workflow(
    product_id: int,
    initial_state: dict[str, Any],
    execution_service: WorkflowExecutionService,
    publish_sse: Callable[..., Any] | None = None,
    db: AsyncSession | None = None,
    tenant_id: int = 1,
):
    execution = await execution_service.start(product_id)
    execution_id = execution.execution_id

    state = dict(initial_state)
    state.setdefault("product_id", product_id)

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

        if publish_sse:
            try:
                res = publish_sse(
                    product_id=product_id,
                    event={
                        "execution_id": execution_id,
                        "step_id": step_id,
                        "status": status,
                        "message": message,
                    },
                )
            except TypeError:
                res = publish_sse(
                    {
                        "execution_id": execution_id,
                        "step_id": step_id,
                        "status": status,
                        "message": message,
                    }
                )
            if inspect.isawaitable(res):
                await res

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
        graph = create_scm_agent_workflow(
            on_step=on_step,
            on_step_result=on_step_result,
        )
        result = await graph.ainvoke(state)

        purchase_order = await create_purchase_order(
            result=result,
            db=db,
            tenant_id=tenant_id,
            product_id=product_id,
        )

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
