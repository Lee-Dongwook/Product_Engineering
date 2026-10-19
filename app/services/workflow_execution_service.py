from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

