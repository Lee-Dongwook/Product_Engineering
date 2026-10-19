from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.workflow_execution import WorkflowExecution

class WorkflowExecutionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def start(self, product_id: int) -> WorkflowExecution:
        execution = WorkflowExecution(
            execution_id=str(uuid4()),
            product_id=product_id,
            status="RUNNING",
            steps=[],
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def update_step(
        self,
        execution_id: str,
        step_id: str,
        status: str,
        message: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> None:
        execution = await self._get(execution_id)
        steps = [dict(s) for s in (execution.steps or [])]
        step = next((item for item in steps if item["id"] == step_id), None)
        if step is None:
            step = {"id": step_id}
            steps.append(step)

        step["status"] = status
        if message is not None:
            step["message"] = message
        if output is not None:
            step["output"] = output

        execution.steps = steps
        flag_modified(execution, "steps")
        await self.db.commit()

    async def complete(self, execution_id: str, purchase_order_id: int) -> None:
        execution = await self._get(execution_id)
        execution.status = "COMPLETED"
        execution.purchase_order_id = purchase_order_id
        execution.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def fail(self, execution_id: str, error_message: str) -> None:
        execution = await self._get(execution_id)
        execution.status = "FAILED"
        execution.error_message = error_message
        execution.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def get_by_execution_id(self, execution_id: str) -> WorkflowExecution | None:
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == execution_id
            )
        )
        return result.scalars().first()

    async def _get(self, execution_id: str) -> WorkflowExecution:
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == execution_id
            )
        )
        return result.scalar_one()

