from app.core.celery_app import celery_app
from app.services.agent_workflow import create_scm_agent_workflow
import asyncio

@celery_app.task(name="run_scm_agent_task")
def run_scm_agent_task(product_id: int, initial_data: dict):
    workflow = create_scm_agent_workflow()

    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(workflow.ainvoke(initial_data), loop)
        result = future.result()
    else:
        result = asyncio.run(workflow.ainvoke(initial_data))
    
    return {
        "product_id": product_id,
        "suggested_qty": result.get("suggested_qty"),
        "reasoning_summary": result.get("reasoning_summary"),
        "execution_logs": result.get("messages")
    }
