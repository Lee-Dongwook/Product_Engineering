
import json

from starlette.testclient import TestClient

from app.api.deps import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.tenant import User, UserRole
from app.services.prediction_service import PredictionExecutionError
import app.api.v1.endpoints.streaming as streaming_endpoint


client = TestClient(app)


def _override_dependencies():
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


def _parse_sse_events(body: str) -> list[dict]:
    events = []

    for block in body.strip().split("\n\n"):
        event_name = None
        data_lines = []

        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())

        if event_name and data_lines:
            events.append({
                "event": event_name,
                "data": json.loads("\n".join(data_lines)),
            })

    return events


def test_agent_stream_returns_workflow_failure_event(monkeypatch):
    async def fail_prediction(**kwargs):
        raise PredictionExecutionError(
            failed_step_id="supplier_agent",
            completed_step_ids={"demand_agent"},
        )

    monkeypatch.setattr(
        streaming_endpoint,
        "execute_inventory_prediction",
        fail_prediction,
    )
    _override_dependencies()

    try:
        response = client.get(
            "/api/v1/stream/agent-stream/101"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = _parse_sse_events(response.text)
    error_events = [event for event in events if event["event"] == "error"]

    assert len(error_events) == 1
    assert error_events[0]["data"] == {
        "failed_step_id": "supplier_agent",
        "completed_step_ids": ["demand_agent"],
        "message": "발주 예측 처리 중 단계 실행에 실패했습니다.",
    }

    assert not any(event["event"] == "result" for event in events)


def test_agent_stream_hides_unexpected_exception(monkeypatch):
    async def fail_unexpectedly(**kwargs):
        raise RuntimeError("sensitive internal details")

    monkeypatch.setattr(
        streaming_endpoint,
        "execute_inventory_prediction",
        fail_unexpectedly,
    )
    _override_dependencies()

    try:
        response = client.get(
            "/api/v1/stream/agent-stream/101"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    events = _parse_sse_events(response.text)
    error_events = [event for event in events if event["event"] == "error"]

    assert len(error_events) == 1
    assert error_events[0]["data"] == {
        "message": "발주 예측 처리에 실패했습니다.",
    }
    assert "sensitive internal details" not in response.text
    assert not any(event["event"] == "result" for event in events)
