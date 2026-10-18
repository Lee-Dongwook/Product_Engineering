from app.api.v1.endpoints.orders import build_workflow_steps


def test_build_workflow_steps_returns_structured_agent_results():
    initial_state = {
        "current_stock": 5,
        "safety_stock": 10,
        "sales_history": [12, 18, 22, 30],
        "lead_time_days": 7,
        "moq": 10,
    }

    workflow_result = {
        "predicted_demand": 24,
        "required_order_timing": "리드타임 7일 고려 시, 즉시 발주 필요",
        "suggested_qty": 30,
        "messages": [
            "Demand Agent: 예상 월간 수요량을 산출했습니다.",
            "Supplier Agent: 리드타임 7일 고려 시, 즉시 발주 필요",
            "Supervisor Agent: 최종 발주 제안 수량 30개 확정.",
        ],
    }

    steps = build_workflow_steps(workflow_result, initial_state)

    assert [step["id"] for step in steps] == [
        "demand_agent",
        "supplier_agent",
        "supervisor",
    ]

    assert all(step["status"] == "completed" for step in steps)

    assert steps[0]["message"] == "예상 월간 수요량을 산출했습니다."
    assert steps[0]["output_summary"] == "예상 월간 수요량 24개"

    assert steps[1]["output_summary"] == (
        "리드타임 7일 고려 시, 즉시 발주 필요"
    )

    assert steps[2]["output_summary"] == "최종 발주 제안 수량 30개"

    # UI 계약에 필요한 필드가 각 단계에 존재하는지 확인한다.
    for step in steps:
        assert "id" in step
        assert "status" in step
        assert "message" in step
        assert "input_summary" in step
        assert "output_summary" in step
