import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.get("/agent-stream/{product_id}")
async def agent_stream_endpoint(product_id: int):
    async def event_generator():
        yield {
            "event": "step",
            "data": "{\"step\": \"demand_agent\", \"status\": \"processing\", \"message\": \"[Demand Agent] 수요 예측 분석 시작...\"}"
        }
        await asyncio.sleep(1.0)

        yield {
            "event": "step",
            "data": "{\"step\": \"supplier_agent\", \"status\": \"processing\", \"message\": \"[Supplier Agent] 공급사 Lead Time 및 MOQ 검토 중...\"}"
        }
        await asyncio.sleep(1.0)

        yield {
            "event": "step",
            "data": "{\"step\": \"supervisor\", \"status\": \"completed\", \"message\": \"[Supervisor Agent] 최종 발주 제안 수량 25개 확정.\", \"suggested_qty\": 25}"
        }

    return EventSourceResponse(event_generator())

