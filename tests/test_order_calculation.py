import pytest

from app.services.agent_workflow import supervisor_node

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
