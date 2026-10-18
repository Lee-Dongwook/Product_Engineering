import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from starlette.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.domain import OrderStatus
from app.models.purchase_order import PurchaseOrder
from app.models.tenant import User, UserRole
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

def test_purchase_order_decision_updates_draft():
    order = PurchaseOrder(
        id=50,
        tenant_id=1,
        product_id=101,
        suggested_qty=20,
        status=OrderStatus.DRAFT,
        created_at=datetime(2026, 10, 18),
    )
    result = type("Result", (), {"scalar_one_or_none": lambda self: order})()
    session = AsyncMock()
    session.execute.return_value = result

    async def override_db():
        yield session

    async def override_user():
        return User(id=1, email="admin@companyA.com", hashed_password="test", role=UserRole.ADMIN, tenant_id=1)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    try:
        response = client.patch(
            "/api/v1/orders/50/decision",
            json={"action": "MODIFIED", "final_qty": 25},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert order.status == OrderStatus.APPROVED
    assert order.final_qty == 25
    session.commit.assert_awaited_once()

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
