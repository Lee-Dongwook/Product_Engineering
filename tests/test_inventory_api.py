import pytest
from starlette.testclient import TestClient
from app.main import app
from app.services.agent_workflow import create_scm_agent_workflow

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "scm-backend"}

def test_tracking_event():
    payload = {
        "event_name": "order_decision_submitted",
        "user_id": "user_001",
        "product_id": 101,
        "purchase_order_id": 50,
        "suggested_qty": 20,
        "final_qty": 20,
        "action": "APPROVED",
        "decision_time_ms": 120,
        "timestamp": "2026-10-18T12:00:00Z"
    }
    response = client.post("/api/v1/tracking/events", json=payload)
    assert response.status_code == 202
    assert response.json() == {"status": "queued"}

@pytest.mark.asyncio
async def test_scm_agent_workflow():
    workflow = create_scm_agent_workflow()
    initial_state = {
        "product_id": 1,
        "current_stock": 5,
        "safety_stock": 10,
        "sales_history": [10, 15, 20, 25],
        "lead_time_days": 7,
        "moq": 10,
        "predicted_demand": 0,
        "required_order_timing": "",
        "suggested_qty": 0,
        "reasoning_summary": "",
        "messages": []
    }
    result = await workflow.ainvoke(initial_state)
    assert result["suggested_qty"] > 0
    assert "Supervisor Agent" in result["messages"][-1]
    assert "Demand Agent" in result["messages"][0]
