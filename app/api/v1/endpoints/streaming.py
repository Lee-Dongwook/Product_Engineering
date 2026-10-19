import asyncio
import json
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.tenant import User, UserRole
from app.services.prediction_service import (
    execute_inventory_prediction,
    PredictionExecutionError,
)

router = APIRouter()

STEP_LABELS = {
    "demand_agent": "수요 예측",
    "supplier_agent": "공급 조건 검토",
    "supervisor": "최종 발주 제안",
}

@router.get("/agent-stream/{product_id}")
async def agent_stream_endpoint(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER)
    ),
):
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def on_step(
        step_id: str,
        step_status: str,
        message: str,
    ) -> None:
        await queue.put({
            "event": "step",
            "data": {
                "step": step_id,
                "status": step_status,
                "message": message,
                "label": STEP_LABELS.get(step_id, step_id),
            },
        })
    
    async def run_prediction() -> None:
        try:
            result = await execute_inventory_prediction(
                db=db,
                product_id=product_id,
                tenant_id=current_user.tenant_id,
                on_step=on_step,
            )
            await queue.put({
                "event": "result",
                "data": result,
            })

        except PredictionExecutionError as exc:
            await queue.put({
                "event": "error",
                "data": {
                    "failed_step_id": exc.failed_step_id,
                    "completed_step_ids": sorted(
                        exc.completed_step_ids
                    ),
                    "message": str(exc),
                },
            })
        except Exception:
            await queue.put({
                "event": "error",
                "data": {
                    "message": "발주 예측 처리에 실패했습니다.",
                },
            })
        
        finally:
            await queue.put(None)
    
    async def event_generator():
        task = asyncio.create_task(run_prediction())

        try:
            while True:
                item = await queue.get()

                if item is None:
                    break

                yield {
                    "event": item["event"],
                    "data": json.dumps(
                        item["data"],
                        ensure_ascii=False,
                    ),
                }
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
    return EventSourceResponse(event_generator())
