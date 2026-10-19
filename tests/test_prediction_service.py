
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
