import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.purchase_order import PurchaseOrder
from app.models.workflow_execution import WorkflowExecution
from app.services.summarize_step_output import summarize_step_output
from app.services.workflow_execution_service import WorkflowExecutionService
from app.services.run_tracked_workflow import run_tracked_workflow, create_purchase_order
from app.services.agent_workflow import WorkflowNodeError


def test_summarize_step_output_demand_agent():
    raw = {
        "average_sales": 15.0,
        "forecast_multiplier": 1.2,
        "predicted_demand": 18,
        "extra_field": "ignored",
    }
    summary = summarize_step_output("demand_agent", raw)
    assert summary == {
        "average_sales": 15.0,
        "forecast_multiplier": 1.2,
        "predicted_demand": 18,
    }


def test_summarize_step_output_supplier_agent():
    raw = {
        "required_order_timing": "리드타임 7일 고려 시, 즉시 발주 필요",
        "messages": ["some message"],
    }
    summary = summarize_step_output("supplier_agent", raw)
    assert summary == {
        "required_order_timing": "리드타임 7일 고려 시, 즉시 발주 필요",
    }


def test_summarize_step_output_supervisor():
    raw = {
        "net_required": 25,
        "suggested_qty": 30,
        "reasoning_summary": "최적 산출",
        "messages": [],
    }
    summary = summarize_step_output("supervisor", raw)
    assert summary == {
        "net_required": 25,
        "suggested_qty": 30,
        "reasoning_summary": "최적 산출",
    }


def test_summarize_step_output_unknown_step():
    assert summarize_step_output("unknown_step", {"foo": "bar"}) == {}


@pytest.mark.asyncio
async def test_workflow_execution_service_lifecycle():
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()

    service = WorkflowExecutionService(mock_db)

    # 1. start
    execution = await service.start(product_id=101)
    assert execution.product_id == 101
    assert execution.status == "RUNNING"
    assert execution.steps == []
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited()

    # Mock _get return
    mock_db.execute = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = execution
    result_mock.scalars.return_value.first.return_value = execution
    mock_db.execute.return_value = result_mock

    # 2. update_step (new step)
    await service.update_step(
        execution_id=execution.execution_id,
        step_id="demand_agent",
        status="PROCESSING",
        message="시작",
    )
    assert len(execution.steps) == 1
    assert execution.steps[0]["id"] == "demand_agent"
    assert execution.steps[0]["status"] == "PROCESSING"
    assert execution.steps[0]["message"] == "시작"

    # 3. update_step (existing step with output)
    await service.update_step(
        execution_id=execution.execution_id,
        step_id="demand_agent",
        status="COMPLETED",
        output={"predicted_demand": 20},
    )
    assert len(execution.steps) == 1
    assert execution.steps[0]["status"] == "COMPLETED"
    assert execution.steps[0]["output"] == {"predicted_demand": 20}
    assert execution.steps[0]["message"] == "시작"

    # 4. complete
    await service.complete(
        execution_id=execution.execution_id,
        purchase_order_id=42,
    )
    assert execution.status == "COMPLETED"
    assert execution.purchase_order_id == 42
    assert execution.completed_at is not None

    # 5. fail
    await service.fail(
        execution_id=execution.execution_id,
        error_message="something went wrong",
    )
    assert execution.status == "FAILED"
    assert execution.error_message == "something went wrong"

    # 6. get_by_execution_id
    found = await service.get_by_execution_id(execution.execution_id)
    assert found == execution


@pytest.mark.asyncio
async def test_run_tracked_workflow_success(monkeypatch):
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.execute = AsyncMock()

    service = WorkflowExecutionService(mock_db)

    execution = WorkflowExecution(
        execution_id="test-exec-1",
        product_id=101,
        status="RUNNING",
        steps=[],
    )
    service.start = AsyncMock(return_value=execution)
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = execution
    mock_db.execute.return_value = result_mock

    # Mock create_purchase_order_draft
    fake_order = PurchaseOrder(
        id=77,
        tenant_id=1,
        product_id=101,
        suggested_qty=20,
        reasoning_summary="OK",
    )

    async def mock_draft(*args, **kwargs):
        return fake_order

    monkeypatch.setattr(
        "app.services.inventory_service.InventoryService.create_purchase_order_draft",
        mock_draft,
    )

    sse_events = []

    async def mock_publish_sse(product_id, event):
        sse_events.append({"product_id": product_id, "event": event})

    initial_state = {
        "current_stock": 5,
        "safety_stock": 10,
        "sales_history": [10, 15, 20, 25],
        "lead_time_days": 7,
        "moq": 10,
    }

    result = await run_tracked_workflow(
        product_id=101,
        initial_state=initial_state,
        execution_service=service,
        publish_sse=mock_publish_sse,
        db=mock_db,
        tenant_id=1,
    )

    assert result["execution_id"] == execution.execution_id
    assert result["purchase_order_id"] == 77
    assert execution.status == "COMPLETED"
    assert execution.purchase_order_id == 77

    # Ensure SSE events were published for nodes
    assert len(sse_events) > 0
    step_ids = [e["event"]["step_id"] for e in sse_events]
    assert "demand_agent" in step_ids
    assert "supplier_agent" in step_ids
    assert "supervisor" in step_ids


@pytest.mark.asyncio
async def test_run_tracked_workflow_failure(monkeypatch):
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.execute = AsyncMock()

    service = WorkflowExecutionService(mock_db)

    execution = WorkflowExecution(
        execution_id="test-exec-err",
        product_id=101,
        status="RUNNING",
        steps=[],
    )
    service.start = AsyncMock(return_value=execution)
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = execution
    mock_db.execute.return_value = result_mock

    async def fail_node(state):
        raise ValueError("simulated node failure")

    monkeypatch.setattr(
        "app.services.agent_workflow.demand_prediction_node",
        fail_node,
    )

    initial_state = {
        "current_stock": 5,
        "safety_stock": 10,
        "sales_history": [10, 15, 20, 25],
        "lead_time_days": 7,
        "moq": 10,
    }

    with pytest.raises(WorkflowNodeError) as exc_info:
        await run_tracked_workflow(
            product_id=101,
            initial_state=initial_state,
            execution_service=service,
            publish_sse=None,
            db=mock_db,
            tenant_id=1,
        )

    assert "demand_agent" in str(exc_info.value)
    assert execution.status == "FAILED"
    assert "Workflow node failed: demand_agent" in execution.error_message
