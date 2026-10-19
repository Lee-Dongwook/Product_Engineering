# AI SCM 재고 최적화 플랫폼

판매 이력과 현재 재고, 안전재고, 최소 발주 수량(MOQ)을 바탕으로 적정 발주 수량을 제안하는 SCM(Supply Chain Management) MVP입니다.

LangGraph 기반 AI 워크플로가 수요 예측, 공급 조건 검토, 최종 발주 제안을 순차적으로 수행합니다. 담당자는 웹 화면에서 각 단계의 진행 상황과 판단 근거를 확인하고, 최종 발주 제안을 승인·수정·거절할 수 있습니다.

이 프로젝트의 핵심은 단순히 발주 수량을 계산하는 것이 아니라, **발주 판단 과정을 단계별로 추적하고 운영자가 결과를 검토할 수 있는 의사결정 워크플로를 구현하는 것**입니다.

## 주요 목표

- 수작업 재고 분석에 드는 운영 비용 감소
- 발주 판단 근거의 구조화 및 일관성 확보
- AI 워크플로의 단계별 실행 상태와 결과 시각화
- 운영자의 승인·수정·거절을 통한 의사결정 데이터 수집

자세한 비즈니스 배경과 측정 지표는 [Business_Context_Metrics.md](docs/Business_Context_Metrics.md)를 참고하세요.

## 주요 기능

### 1. 재고 기반 발주 제안

- 상품 및 현재 재고 정보 조회
- 안전재고와 판매 이력을 반영한 예상 수요 산출
- 공급 리드타임을 고려한 발주 시점 안내
- MOQ 단위로 올림 처리한 발주 수량 제안
- 판단 근거를 구조화된 데이터로 반환

### 2. LangGraph 기반 AI 워크플로

세 단계로 구성된 워크플로를 통해 발주 제안을 산출합니다.

| 단계             | 역할                                         | 주요 결과                         |
| ---------------- | -------------------------------------------- | --------------------------------- |
| Demand Agent     | 판매 이력을 바탕으로 예상 수요 계산          | 평균 판매량, 예측 배율, 예상 수요 |
| Supplier Agent   | 공급 리드타임을 고려한 발주 시점 검토        | 발주 시점 안내                    |
| Supervisor Agent | 재고와 안전재고, MOQ를 반영해 최종 수량 결정 | 필요 수량, 제안 수량, 판단 근거   |

현재는 규칙 기반 계산 로직을 사용합니다. 각 단계는 향후 실제 판매 데이터 및 공급사 정보와 연계할 수 있도록 구분되어 있습니다.

### 3. 실시간 워크플로 시각화

- SSE(Server-Sent Events)를 통한 단계별 진행 상태 전달
- 단계별 실행 상태와 메시지 표시
- 선택한 단계의 입력·출력 요약 확인
- 워크플로 실패 시 실패 단계와 완료된 단계 확인
- 최종 발주 제안과 판단 근거 표시

프론트엔드는 단순 로그 문자열을 해석하는 대신, API가 반환하는 구조화된 `workflow_steps`와 `decision_basis`를 이용해 실행 과정과 판단 근거를 표현합니다.

### 4. 운영자 의사결정

- 발주 제안을 `DRAFT` 상태로 저장
- 발주 수량 승인
- 제안 수량 수정 후 결정
- 발주 제안 거절
- 승인·수정·거절 이벤트 및 의사결정 지표 수집

### 5. 백엔드 및 개발 환경

- FastAPI 기반 REST API
- PostgreSQL과 SQLAlchemy Async 기반 데이터 관리
- Alembic 기반 데이터베이스 마이그레이션
- Redis와 Celery 기반 비동기 작업 환경
- Docker Compose 기반 개발 인프라
- pytest 기반 API 및 워크플로 테스트

## 시스템 아키텍처

```mermaid
flowchart TD
    User["운영자"] --> Frontend["Next.js Frontend"]
    Frontend --> API["FastAPI"]
    Frontend <-->|"SSE: 단계별 상태 및 결과"| API

    API --> Workflow["LangGraph Workflow"]
    Workflow --> Demand["Demand Agent"]
    Demand --> Supplier["Supplier Agent"]
    Supplier --> Supervisor["Supervisor Agent"]

    Supervisor --> Result["발주 제안 결과"]
    Result --> API
    API --> DB[("PostgreSQL")]
    API --> Decision["승인·수정·거절 처리"]
    Decision --> DB

    API -.-> Redis[("Redis")]
    Redis -.-> Worker["Celery Worker"]
```

> 위 다이어그램은 주요 구성 요소와 논리적인 관계를 표현합니다. Redis와 Celery는 실행 환경에 포함되지만, 모든 발주 예측 요청이 Celery를 경유한다고 의미하지는 않습니다.

### 발주 제안 처리 흐름

1. 운영자가 상품의 발주 제안을 요청합니다.
2. Demand Agent가 판매 이력을 바탕으로 예상 수요를 산출합니다.
3. Supplier Agent가 리드타임을 고려한 발주 시점을 안내합니다.
4. Supervisor Agent가 필요 수량과 MOQ를 바탕으로 최종 발주 수량을 계산합니다.
5. 백엔드는 제안 결과를 발주 초안으로 저장하고 판단 근거를 반환합니다.
6. 프론트엔드는 실행 단계와 결과를 시각화합니다.
7. 운영자가 제안을 승인·수정·거절하면 의사결정 결과를 기록합니다.

## 기술 스택

| 영역           | 기술                                     | 역할                          |
| -------------- | ---------------------------------------- | ----------------------------- |
| Backend        | Python 3.11, FastAPI, Pydantic           | API 및 데이터 검증            |
| Database       | PostgreSQL 15, SQLAlchemy Async, Alembic | 데이터 저장 및 스키마 관리    |
| 비동기 처리    | Redis, Celery                            | 비동기 작업 실행 환경         |
| Agent Workflow | LangGraph, LangChain Core                | 단계별 발주 제안 워크플로     |
| Frontend       | Next.js, React, TypeScript, Tailwind CSS | 발주 검토 및 워크플로 시각화  |
| Testing        | pytest, pytest-asyncio, httpx            | API 및 비동기 워크플로 테스트 |
| Container      | Docker Compose                           | 개발 인프라 실행              |

## 프로젝트 구조

```text
.
├── app/
│   ├── api/v1/endpoints/    # 재고, 발주, 스트림, 이벤트 API
│   ├── core/                # 설정, DB 세션, Celery 설정, 예외
│   ├── models/              # Tenant, User, Product, Supplier, PurchaseOrder 등
│   ├── schemas/             # 요청/응답 Pydantic 스키마
│   ├── services/            # 재고 서비스와 LangGraph 워크플로
│   ├── worker/              # Celery 작업
│   └── main.py              # FastAPI 앱 진입점
├── alembic/                 # DB 마이그레이션 설정
├── frontend/                # Next.js 사용자 화면
├── tests/                   # API와 워크플로 테스트
├── docker-compose.yaml      # Backend, Worker, PostgreSQL, Redis
└── requirements.txt
```

## 빠른 시작

### 사전 요구 사항

- Docker 및 Docker Compose
- Node.js와 pnpm
- Python 3.11은 로컬 백엔드 실행 시 필요

### 1. 백엔드 인프라 실행

```bash
docker compose up --build
```

실행 후 다음 주소에서 API를 확인할 수 있습니다.

- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

```bash
curl http://localhost:8000/health
```

정상 응답 예시:

```json
{
  "status": "ok",
  "service": "scm-backend"
}
```

### 2. 프론트엔드 실행

프론트엔드는 Docker Compose와 별도로 실행합니다.

```bash
cd frontend
pnpm install
pnpm dev
```

`pnpm`을 사용할 수 없다면 Corepack을 활성화할 수 있습니다.

```bash
corepack enable
```

- 프론트엔드: http://localhost:3000
- 발주 검토 화면: http://localhost:3000/orders

### 3. 로컬 Python 실행 (선택)

PostgreSQL과 Redis가 실행 중인 환경에서 사용할 수 있습니다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

환경 변수 예시:

```env
DATABASE_URL=postgresql+asyncpg://scm_user:scm_pass@localhost:5432/scm_db
REDIS_URL=redis://localhost:6379/0
```

Celery Worker를 별도로 실행하려면 다음 명령을 사용합니다.

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

실제 환경에서는 데이터베이스 인증 정보와 기타 비밀 값을 환경에 맞게 설정해야 합니다.

## 데이터베이스 마이그레이션

DB가 실행 중인 상태에서 초기 스키마와 개발 시드 데이터를 적용합니다.

```bash
alembic upgrade head
python -m app.scripts.seed
```

시드 스크립트는 여러 번 실행해도 `Company A`, 관리자 사용자, 기본 공급사 및 `SKU-001` 상품을 중복 생성하지 않도록 구성되어 있습니다.

개발용 관리자 비밀번호는 인증 구현 전의 임시 데이터이므로 운영 환경에서 사용하면 안 됩니다.

## API 요약

모든 API는 `/api/v1` 접두사를 사용합니다.

| Method  | Endpoint                                      | 설명                                      |
| ------- | --------------------------------------------- | ----------------------------------------- |
| `GET`   | `/health`                                     | 서버 상태 확인                            |
| `GET`   | `/api/v1/inventory/products`                  | 현재 테넌트의 상품 목록 조회              |
| `GET`   | `/api/v1/inventory/products/{product_id}`     | 상품 상세 조회                            |
| `POST`  | `/api/v1/inventory/products`                  | 상품 등록 (`ADMIN`, `MANAGER`)            |
| `POST`  | `/api/v1/orders/run-prediction/{product_id}`  | 발주 수량 계산 및 발주 초안 저장          |
| `GET`   | `/api/v1/stream/agent-stream/{product_id}`    | 발주 워크플로 실행 및 SSE 이벤트 스트리밍 |
| `PATCH` | `/api/v1/orders/{purchase_order_id}/decision` | 발주 승인·수정·거절                       |
| `GET`   | `/api/v1/orders/decision-metrics`             | 의사결정 지표 조회                        |

### 상품 등록 예시

```bash
curl -X POST http://localhost:8000/api/v1/inventory/products \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 1,
    "sku": "SKU-001",
    "name": "무선 키보드",
    "category": "전자기기",
    "current_stock": 5,
    "safety_stock": 10,
    "unit_cost": 35000
  }'
```

### 발주 제안 실행 예시

```bash
curl -X POST http://localhost:8000/api/v1/orders/run-prediction/1
```

응답에는 생성된 `purchase_order_id`, 제안 수량, 판단 근거 및 워크플로 실행 정보가 포함됩니다.

### 발주 제안 응답 구조

`POST /api/v1/orders/run-prediction/{product_id}`는 발주 초안과 함께 다음 정보를 반환합니다.

| 필드                                  | 설명                                     |
| ------------------------------------- | ---------------------------------------- |
| `suggested_qty`                       | 최종 발주 제안 수량                      |
| `reasoning_summary`                   | 발주 판단 요약                           |
| `workflow_steps`                      | 단계별 워크플로 정보                     |
| `decision_basis.inputs`               | 재고, 판매 이력, 리드타임, MOQ 등 입력값 |
| `decision_basis.demand`               | 평균 판매량, 예측 배율, 예상 수요        |
| `decision_basis.quantity_calculation` | 필요 수량 및 최종 제안 수량              |
| `decision_basis.supply`               | 리드타임 기반 발주 시점 안내             |

프론트엔드는 구조화된 `decision_basis`를 이용해 판단 근거를 표시합니다. 문자열 로그를 파싱해 계산값을 추출하는 방식은 사용하지 않습니다.

### 실시간 워크플로 이벤트

`GET /api/v1/stream/agent-stream/{product_id}`는 워크플로를 실행하면서 SSE 이벤트를 전달합니다.

| 이벤트   | 역할                                                    |
| -------- | ------------------------------------------------------- |
| `step`   | 단계별 실행 상태, 메시지, 표시 이름 전달                |
| `result` | 최종 발주 제안, `workflow_steps`, `decision_basis` 전달 |
| `error`  | 실패 단계, 완료된 단계 및 오류 정보 전달                |

프론트엔드는 이벤트를 받아 워크플로 시각화 상태를 갱신하고, 최종 결과를 발주 검토 화면에 표시합니다.

## 발주 수량 산정 방식

현재 MVP는 실제 시계열 예측 모델 대신 단순한 규칙 기반 계산을 사용합니다.

```text
예상 수요 = 판매 이력 평균 × 1.2
필요 수량 = 예상 수요 + 안전재고 - 현재 재고
제안 수량 = 필요 수량을 MOQ 단위로 올림
```

필요 수량이 0 이하이면 추가 발주를 제안하지 않습니다.

예를 들어 예상 수요가 20개, 안전재고가 10개, 현재 재고가 5개라면 필요 수량은 25개입니다. MOQ가 12개라면 최종 제안 수량은 36개입니다.

이 계산 방식은 워크플로와 의사결정 흐름을 검증하기 위한 MVP 로직이며, 실제 수요 예측 성능을 보장하지 않습니다.

## 테스트

백엔드 의존성을 설치한 환경에서 실행합니다.

```bash
pytest
```

현재 테스트 범위는 다음과 같습니다.

- 헬스 체크 API 응답
- 발주 의사결정 상태 변경 및 이력 저장
- LangGraph 발주 제안 워크플로의 수량 산출 및 단계 로그

프론트엔드는 `pnpm dev` 실행 후 `/orders`에서 승인·수량 수정·거절 흐름을 확인할 수 있습니다.

## 현재 MVP의 제한 사항

- 인증은 아직 구현 전이며, 개발 편의를 위한 임시 관리자 데이터가 사용됩니다.
- 수요 예측은 판매 이력 평균에 고정 배율을 적용하는 단순 계산입니다.
- POS, 프로모션, 계절성 등 외부 수요 요인을 반영하지 않습니다.
- 상품에 공급사 관계가 존재하더라도, 발주 계산에서 공급사별 리드타임과 MOQ를 직접 조회하지 않고 기본값을 사용합니다.
- 의사결정 지표는 누적 건수 중심이며, 기간별 추이와 상품별 분석은 추가 개선이 필요합니다.
- 워크플로의 실시간 진행 상황은 제공하지만, 실행 이력을 독립적인 영속 데이터로 관리하는 기능은 별도 개선 대상입니다.

## 다음 개선 우선순위

1. 워크플로 실행 이력 영속화 및 단계별 결과 조회
2. 실제 인증·권한 처리 및 개발용 임시 사용자 제거
3. 공급사별 리드타임·MOQ를 발주 계산에 연동
4. 프론트엔드 API 연결 설정 및 이벤트 스트리밍 경로 환경 변수화
5. 실제 판매 데이터 기반 수요 예측 고도화
6. 기간별·상품별 의사결정 지표 및 운영 분석 추가

## 참고

- API 문서: http://localhost:8000/docs
- 비즈니스 요구사항 및 측정 지표: [docs/Business_Context_Metrics.md](docs/Business_Context_Metrics.md)
