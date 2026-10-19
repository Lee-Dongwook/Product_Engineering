import pytest

from app.services.agent_workflow import supervisor_node, demand_prediction_node

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("predicted_demand", "safety_stock", "current_stock", "moq", "expected"),
    [
        (20, 10, 5, 10, 30),   # 필요 수량 25 → MOQ 올림
        (20, 10, 30, 10, 0),   # 필요 수량 0
        (20, 10, 35, 10, 0),   # 필요 수량 음수
        (1, 0, 0, 10, 10),     # 필요 수량 1 → MOQ 올림
        (10, 0, 0, 10, 10),    # MOQ와 정확히 일치
        (11, 0, 0, 10, 20),    # MOQ보다 1개 많음
    ],
)
async def test_supervisor_calculates_suggested_quantity(
    predicted_demand,
    safety_stock,
    current_stock,
    moq,
    expected,
):
    result = await supervisor_node(
        {
            "predicted_demand": predicted_demand,
            "safety_stock": safety_stock,
            "current_stock": current_stock,
            "moq": moq,
        }
    )
    assert result["net_required"] == (
        predicted_demand + safety_stock - current_stock
    )
    assert result["suggested_qty"] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("moq", [0, -1, -10])
async def test_supervisor_rejects_invalid_moq(moq):
    with pytest.raises(ValueError):
        await supervisor_node(
            {
                "predicted_demand": 20,
                "safety_stock": 10,
                "current_stock": 5,
                "moq": moq,
            }
        )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing_field",
    [
        "predicted_demand",
        "current_stock",
        "safety_stock",
        "moq",
    ],
)
async def test_supervisor_rejects_missing_required_input(missing_field):
    state = {
        "predicted_demand": 20,
        "current_stock": 5,
        "safety_stock": 10,
        "moq": 10,
    }
    del state[missing_field]

    with pytest.raises(ValueError, match=missing_field):
        await supervisor_node(state)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sales_history",
    [
        [],
        [-1, 10, 20],
        [10, -5, 20],
    ],
)
async def test_demand_prediction_rejects_invalid_sales_history(sales_history):
    with pytest.raises(ValueError, match="sales_history"):
        await demand_prediction_node({"sales_history": sales_history})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "predicted_demand",
        "safety_stock",
        "current_stock",
        "moq",
        "expected_qty",
        "expected_rounding",
    ),
    [
        (20, 10, 15, 5, 15, False),  # 필요 수량 15, 정확히 MOQ 배수
        (20, 10, 14, 5, 20, True),   # 필요 수량 16, MOQ 올림
        (20, 10, 30, 5, 0, False),   # 발주 불필요
        (20, 10, 20, 5, 10, False),  # 필요 수량 10, 정확히 MOQ 배수
    ],
)
async def test_moq_rounding_matches_calculated_quantity(
    predicted_demand,
    safety_stock,
    current_stock,
    moq,
    expected_qty,
    expected_rounding,
):
    result = await supervisor_node(
        {
            "predicted_demand": predicted_demand,
            "safety_stock": safety_stock,
            "current_stock": current_stock,
            "moq": moq,
        }
    )

    assert result["suggested_qty"] == expected_qty
    assert (
        result["net_required"] > 0
        and result["suggested_qty"] != result["net_required"]
    ) is expected_rounding
