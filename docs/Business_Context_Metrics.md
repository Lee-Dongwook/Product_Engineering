# RFC: AI 기반 커머스 공급망 (SCM) 및 재고 최적화 예측 에이전트 시스템

과거 판매 실적, POS 데이터, 공급 업체 리드 타임(Lead Time)및 외부 변수(시즌/프로모션)를 분석하여 **자동 재고 예측**, **적정 발주 제안**, **비이상 재고 감지 리포트** 제공을 목표한다.

## Business Context & Metrics

- 커머스 기업은 재고 부족으로 인한 판매 기회 손실(Stock-out)과 과다 재고로 인한 보관/폐기 비용 증가(Overstock) 사이에서 늘 균형을 잡기 어렵다.

- 담당자의 수작업 엑셀 분석은 실시간 수요 변화 대응에 한계가 있으며, 공급업체별 Lead Time 차이를 반영한 발주 타이밍 계산이 부정확하다.

## 목표 비즈니스 & 엔지니어링 지표 (Metrics)

1. 재고 회전율 (Inventory Turnover)
2. 품절 발생률 (Stock-out Rate)
3. 발주 제안 수용률 (Recommendation Acceptance Rate)
4. 시스템 성능

## System Architecture

```
[ Client / Web Portal ]  <--->  [ FastAPI Backend ]  <--->  [ PostgreSQL DB ]
 (React / Next.js)              (REST / SSE Stream)          (POS / 재고 / 발주)
         │                              │                            │
         ▼                              ▼                            ▼
[ Zod / Event Queue ]        [ Redis & Celery Queue ]     [ Qdrant Vector DB ]
(유저 행동 트래킹)           (비동기 발주/예측 Worker)    (상품/공급사 매핑 RAG)
                                        │
                                        ▼
                            [ Multi-Agent Engine ]
                            (LangGraph Orchestrator)
                                        │
                                        ▼
                            [ MLOps & Observability ]
                            (LangSmith / Phoenix)
```
