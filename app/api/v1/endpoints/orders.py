from fastapi import APIRouter, Depends
from app.services.agent_workflow import create_scm_agent_workflow

router = APIRouter()
scm_workflow = create_scm_agent_workflow()

@router.post("/run-prediction/{product_id}")
async def run_inventory_prediction(product_id: int):
    initial_state = {
        "product_id": product_id,
        "current_stock": 5,
        "safety_stock": 15,
        "sales_history": [12, 18, 22, 30],
        "lead_time_days": 10,
        "moq": 20,
        "predicted_demand": 0,
        "required_order_timing": "",
        "suggested_qty": 0,
        "reasoning_summary": "",
        "messages": []
    }

    result = await scm_workflow.ainvoke(initial_state)

    return {
        "product_id": product_id,
        "suggested_qty": result.get("suggested_qty"),
        "reasoning_summary": result.get("reasoning_summary"),
        "execution_logs": result.get("messages")
    }
