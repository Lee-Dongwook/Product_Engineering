
from starlette.testclient import TestClient

from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.tenant import User, UserRole
from app.services.prediction_service import PredictionExecutionError
import app.api.v1.endpoints.orders as orders_endpoint


client = TestClient(app)


def test_run_prediction_returns_workflow_failure_details(monkeypatch):
    async def fail_prediction(**kwargs):
        raise PredictionExecutionError(
            failed_step_id="supplier_agent",
            completed_step_ids={"demand_agent"},
        )

    monkeypatch.setattr(
        orders_endpoint,
        "execute_inventory_prediction",
        fail_prediction,
    )

    async def override_db():
        yield None

    async def override_user():
        return User(
            id=1,
            email="admin@companyA.com",
            hashed_password="test",
            role=UserRole.ADMIN,
            tenant_id=1,
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user

    try:
        response = client.post(
            "/api/v1/orders/run-prediction/101"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500

    detail = response.json()["detail"]

    assert detail["failed_step_id"] == "supplier_agent"
    assert detail["completed_step_ids"] == ["demand_agent"]
    assert detail["message"] == (
        "발주 예측 처리 중 단계 실행에 실패했습니다."
    )
