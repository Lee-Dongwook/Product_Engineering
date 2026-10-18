from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.inventory_service import InventoryService
from app.services.agent_workflow import create_scm_agent_workflow

router = APIRouter()
scm_workflow = create_scm_agent_workflow()

@router.post("/run-prediction/{product_id}")
async def run_inventory_prediction(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await InventoryService.get_product_with_inventory(db, product_id)
    initial_state = {
        "product_id": product.id,
        "current_stock": product.current_stock,
        "safety_stock": product.safety_stock,
        "sales_history": [12, 18, 22, 30],
        "lead_time_days": product.lead_time_days,
        "moq": product.moq,
        "predicted_demand": 0,
        "required_order_timing": "",
        "suggested_qty": 0,
        "reasoning_summary": "",
        "messages": []
    }

    result = await scm_workflow.ainvoke(initial_state)
    draft_order = await InventoryService.create_purchase_order_draft(
        db=db,
        product_id=product_id,
        suggested_qty=result.get("suggested_qty"),
        reasoning=result.get("reasoning_summary")
    )

    return {
        "product_id": product_id,
        "suggested_qty": draft_order.id,
        "reasoning_summary": draft_order.reasoning,
        "execution_logs": result.get("messages")
    }
