import operator
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class SCMState(TypedDict):
    product_id: int
    current_stock: int
    safety_stock: int
    sales_history: List[int]
    lead_time_days: int
    moq: int
    predicted_demand: int
    required_order_timing: str
    suggested_qty: int
    reasoning_summary: str
    messages: Annotated[List[str], operator.add]

async def demand_prediction_node(state: SCMState) -> Dict[str, Any]:
    sales = state.get("sales_history", [10, 12, 15, 20])
    avg_sales = sum(sales) / len(sales) if sales else 10
    predicted_demand = int(avg_sales * 1.2)

    return {
        "predicted_demand": predicted_demand,
        "messages": ["Demand Agent: 예상 월간 수요량을 산출했습니다."]
    }

async def supplier_analysis_node(state: SCMState) -> Dict[str, Any]:
    lead_time = state.get("lead_time_days", 7)
    
    timing_msg = f"리드타임 {lead_time}일 고려 시, 즉시 발주 필요" if lead_time > 5 else "정상 범위 내 재고"
    
    return {
        "required_order_timing": timing_msg,
        "messages": [f"Supplier Agent: {timing_msg}"]
    }

async def supervisor_node(state: SCMState) -> Dict[str, Any]:
    print("--- [Supervisor Agent] 최종 발주 수량 산정 및 리포트 작성 중 ---")
    current_stock = state.get("current_stock", 0)
    safety_stock = state.get("safety_stock", 10)
    predicted_demand = state.get("predicted_demand", 20)
    moq = state.get("moq", 1)

    net_required = (predicted_demand + safety_stock) - current_stock

    if net_required <= 0:
        suggested_qty = 0
        reasoning = "현재 재고가 충분하여 추가 발주가 불필요합니다."
    else :
        suggested_qty = ((net_required + moq -1) // moq) * moq
        reasoning = f"예상 수요({predicted_demand})와 안전재고({safety_stock}) 확보를 위해 MOQ({moq}) 단위로 최적 산출되었습니다."
    
    return {
        "suggested_qty": suggested_qty,
        "reasoning_summary": reasoning,
        "messages": [f"Supervisor Agent: 최종 발주 제안 수량 {suggested_qty}개 확정."]
    }

def create_scm_agent_workflow():
    workflow = StateGraph(SCMState)

    workflow.add_node("demand_agent", demand_prediction_node)
    workflow.add_node("supplier_agent", supplier_analysis_node)
    workflow.add_node("supervisor", supervisor_node)

    workflow.set_entry_point("demand_agent")
    workflow.add_edge("demand_agent", "supplier_agent")
    workflow.add_edge("supplier_agent", "supervisor")
    workflow.add_edge("supervisor", END)

    return workflow.compile()
