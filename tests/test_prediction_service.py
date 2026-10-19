from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import prediction_service
from app.services.prediction_service import build_workflow_steps


def make_initial_state():
    return {
        "current_stock": 20,
        "safety_stock": 10,
        "sales_history": [12, 18, 22, 30],
        "lead_time_days": 7,
        "moq": 5,
    }


def make_workflow_result():
    return {
        "predicted_demand": 25,
        "required_order_timing": "즉시 발주 필요",
        "suggested_qty": 15,
        "messages": [],
    }


def test_all_completed_steps_are_marked_completed():
    steps = build_workflow_steps(
        workflow_result=make_workflow_result(),
        initial_state=make_initial_state(),
        completed_step_ids={
            "demand_agent",
            "supplier_agent",
            "supervisor",
        },
    )

    assert [step["status"] for step in steps] == [
        "completed",
        "completed",
        "completed",
    ]


def test_failed_step_is_error_and_following_steps_remain_pending():
    steps = build_workflow_steps(
        workflow_result=make_workflow_result(),
        initial_state=make_initial_state(),
        completed_step_ids={"demand_agent"},
        failed_step_id="supplier_agent",
        error_message="공급 조건 분석에 실패했습니다.",
    )

    assert [step["status"] for step in steps] == [
        "completed",
        "error",
        "pending",
    ]
    assert steps[1]["message"] == "공급 조건 분석에 실패했습니다."


def test_steps_are_pending_when_execution_has_not_completed():
    steps = build_workflow_steps(
        workflow_result=make_workflow_result(),
        initial_state=make_initial_state(),
        completed_step_ids=set(),
    )

    assert all(step["status"] == "pending" for step in steps)

@pytest.mark.asyncio
async def test_prediction_service_uses_calculated_quantity_consistently(monkeypatch):
    product = SimpleNamespace(
        id=101,
        current_stock=5,
        safety_stock=10,
        lead_time_days=7,
        moq=10,
    )
    draft_order = SimpleNamespace(
        id=77,
        suggested_qty=30,
        reasoning_summary="MOQ 단위로 산출",
    )

    monkeypatch.setattr(
        prediction_service.InventoryService,
        "get_product_with_inventory",
        AsyncMock(return_value=product),
    )
    create_draft = AsyncMock(return_value=draft_order)
    monkeypatch.setattr(
        prediction_service.InventoryService,
        "create_purchase_order_draft",
        create_draft,
    )

    class FakeWorkflow:
        async def astream(self, initial_state, stream_mode):
            yield {
                "demand_agent": {
                    "average_sales": 20,
                    "forecast_multiplier": 1.2,
                    "predicted_demand": 24,
                    "messages": ["Demand Agent: 수요 산출 완료"],
                }
            }
            yield {
                "supplier_agent": {
                    "required_order_timing": "즉시 발주 필요",
                    "messages": ["Supplier Agent: 공급 조건 확인"],
                }
            }
            yield {
                "supervisor": {
                    "net_required": 29,
                    "suggested_qty": 30,
                    "reasoning_summary": "MOQ 단위로 산출",
                    "messages": ["Supervisor Agent: 30개 확정"],
                }
            }

    monkeypatch.setattr(
        prediction_service,
        "create_scm_agent_workflow",
        lambda **kwargs: FakeWorkflow(),
    )

    result = await prediction_service.execute_inventory_prediction(
        db=AsyncMock(),
        product_id=101,
        tenant_id=1,
    )

    create_draft.assert_awaited_once()
    assert create_draft.await_args.kwargs["suggested_qty"] == 30
    assert result["suggested_qty"] == 30
    assert result["decision_basis"]["quantity_calculation"] == {
        "net_required": 29,
        "suggested_qty": 30,
        "moq_rounding_applied": True,
    }

@pytest.mark.asyncio
async def test_prediction_service_raises_when_persisted_quantity_differs(
    monkeypatch,
):
    product = SimpleNamespace(
        id=101,
        current_stock=5,
        safety_stock=10,
        lead_time_days=7,
        moq=10,
    )
    draft_order = SimpleNamespace(
        id=77,
        suggested_qty=20,
        reasoning_summary="MOQ 단위로 산출",
    )

    monkeypatch.setattr(
        prediction_service.InventoryService,
        "get_product_with_inventory",
        AsyncMock(return_value=product),
    )

    create_draft = AsyncMock(return_value=draft_order)
    monkeypatch.setattr(
        prediction_service.InventoryService,
        "create_purchase_order_draft",
        create_draft,
    )

    class FakeWorkflow:
        async def astream(self, initial_state, stream_mode):
            yield {
                "demand_agent": {
                    "average_sales": 20,
                    "forecast_multiplier": 1.2,
                    "predicted_demand": 24,
                    "messages": [],
                }
            }
            yield {
                "supplier_agent": {
                    "required_order_timing": "즉시 발주 필요",
                    "messages": [],
                }
            }
            yield {
                "supervisor": {
                    "net_required": 29,
                    "suggested_qty": 30,
                    "reasoning_summary": "MOQ 단위로 산출",
                    "messages": [],
                }
            }

    monkeypatch.setattr(
        prediction_service,
        "create_scm_agent_workflow",
        lambda **kwargs: FakeWorkflow(),
    )

    with pytest.raises(RuntimeError, match="발주 수량 불일치"):
        await prediction_service.execute_inventory_prediction(
            db=AsyncMock(),
            product_id=101,
            tenant_id=1,
        )

    create_draft.assert_awaited_once()
