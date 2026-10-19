from typing import Any

def summarize_step_output(
    step_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    output_fields = {
        "demand_agent": [
            "average_sales",
            "forecast_multiplier",
            "predicted_demand",
        ],
        "supplier_agent": [
            "required_order_timing",
        ],
        "supervisor": [
            "net_required",
            "suggested_qty",
            "reasoning_summary",
        ],
    }

    fields = output_fields.get(step_id, [])

    return {
        key: result[key]
        for key in fields
        if key in result
    }

