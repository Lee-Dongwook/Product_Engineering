from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

router = APIRouter()

class OrderDecisionTrackingSchema(BaseModel):
    event_name: str
    user_id: str
    product_id: int
    purchase_order_id: int
    suggested_qty: int
    final_qty: int
    action: str
    rejection_reason: Optional[str] = None
    decision_time_ms: int
    timestamp: datetime

async def process_event_background(event: OrderDecisionTrackingSchema):
    print(f"[Event Tracker Logged] Action: {event.action}, Product: {event.product_id}, Diff: {event.final_qty - event.suggested_qty}")

@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def receive_tracking_event(
    event: OrderDecisionTrackingSchema,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_event_background, event)
    return {"status": "queued"}
