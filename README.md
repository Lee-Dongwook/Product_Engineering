# AI SCM 재고 최적화 플랫폼

판매 이력과 현재 재고, 안전재고, 최소 발주 수량(MOQ)을 바탕으로 적정 발주 수량을 제안하는 SCM(Supply Chain Management) MVP입니다. LangGraph 워크플로가 수요 예측, 공급 조건 검토, 최종 발주 제안을 순서대로 수행하고, 담당자는 웹 화면에서 제안을 승인·수정·거절할 수 있습니다.

## 해결하려는 문제

커머스 운영자는 품절에 따른 판매 기회 손실과 과잉 재고 비용을 함께 관리해야 합니다. 이 프로젝트는 수작업 재고 분석을 줄이고, 발주 판단의 근거를 일관되게 제공하는 것을 목표로 합니다.

자세한 배경과 지표는 [Business_Context_Metrics.md](docs/Business_Context_Metrics.md)를 참고하세요.

## 주요 기능

- 상품 조회 및 관리자/매니저의 상품 등록 API
- LangGraph 기반 3단계 발주 제안 워크플로
  - Demand Agent: 판매 이력 평균을 기반으로 예상 수요 산출
  - Supplier Agent: 리드타임을 고려한 발주 시점 안내
  - Supervisor Agent: 안전재고와 MOQ를 반영한 최종 제안 수량 산출
- 제안 결과를 발주 초안(`DRAFT`)으로 저장
- SSE(Server-Sent Events) 방식의 에이전트 진행 상태 스트림
- 발주 제안 승인·수정·거절 이벤트 수집 API
- Next.js 기반 발주 제안 검토 화면
- 헬스 체크 및 기본 API/워크플로 테스트
- 발주 AI 워크플로우 시각화
  - 수요 예측 → 공급 조건 검토 → 최종 발주 제안 → 운영자 결정
  - 단계별 실행 상태 및 메시지 표시
  - 선택한 단계의 입력·출력 요약 확인
  - AI 제안에 대한 운영자 승인·수정·거절 연동

## 기술 스택

| 영역           | 사용 기술                                |
| -------------- | ---------------------------------------- |
| Backend        | Python 3.11, FastAPI, Pydantic           |
| Database       | PostgreSQL 15, SQLAlchemy Async, Alembic |
| 비동기 처리    | Redis, Celery                            |
| Agent workflow | LangGraph, LangChain Core                |
| Frontend       | Next.js, React, TypeScript, Tailwind CSS |
| Test           | pytest, pytest-asyncio, httpx            |
| Container      | Docker Compose                           |

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
├── docker-compose.yaml      # Backend, Worker, PostgreSQL, Redis 실행 구성
└── requirements.txt
```

## 빠른 시작

### 1. Docker로 백엔드 인프라 실행

Docker와 Docker Compose가 설치되어 있다면 아래 명령으로 FastAPI, Celery worker, PostgreSQL, Redis를 함께 실행합니다.

```bash
docker compose up --build
```

실행 후 API 문서는 `http://localhost:8000/docs`, 상태 확인은 `http://localhost:8000/health`에서 할 수 있습니다.

```bash
curl http://localhost:8000/health
```

기대 결과:

```json
{ "status": "ok", "service": "scm-backend" }
```

### 2. 프론트엔드 실행

프론트엔드는 Docker Compose에 포함되어 있지 않으므로 별도 터미널에서 실행합니다.

```bash
cd frontend
pnpm install
pnpm dev
```

`pnpm`이 없다면 Corepack을 활성화한 뒤 다시 실행할 수 있습니다.

```bash
corepack enable
```

기본 주소는 `http://localhost:3000`이며, 발주 검토 화면은 `http://localhost:3000/orders`입니다.

### 3. 로컬 Python 실행(선택)

PostgreSQL과 Redis가 로컬에서 실행 중인 경우에만 사용하세요.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본 연결 값은 아래와 같습니다. 실제 운영 환경에서는 `.env` 파일 또는 배포 환경 변수로 안전하게 변경하세요.

```env
DATABASE_URL=postgresql+asyncpg://scm_user:scm_pass@localhost:5432/scm_db
REDIS_URL=redis://localhost:6379/0
```

Celery worker는 별도 터미널에서 실행합니다.

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

## 데이터베이스 마이그레이션

초기 스키마 migration과 화면 확인용 개발 시드 데이터가 포함되어 있습니다. DB를 실행한 뒤 아래 순서로 적용하세요.

```bash
alembic upgrade head
python -m app.scripts.seed
```

시드 명령은 여러 번 실행해도 `Company A`, 관리자 사용자, 기본 공급사, `SKU-001` 상품을 중복 생성하지 않습니다. 개발용 관리자 비밀번호 값은 인증 구현 전 임시 데이터이며 운영 환경에서 사용하면 안 됩니다.

## API 요약

모든 API는 `/api/v1` 접두사를 사용합니다.

| Method  | Endpoint                                      | 설명                                                          |
| ------- | --------------------------------------------- | ------------------------------------------------------------- |
| `GET`   | `/health`                                     | 서버 상태 확인                                                |
| `GET`   | `/api/v1/inventory/products`                  | 현재 테넌트의 상품 목록 조회                                  |
| `GET`   | `/api/v1/inventory/products/{product_id}`     | 상품 상세 조회                                                |
| `POST`  | `/api/v1/inventory/products`                  | 상품 등록 (ADMIN, MANAGER)                                    |
| `POST`  | `/api/v1/orders/run-prediction/{product_id}`  | 발주 수량 계산 및 발주 초안 저장                              |
| `GET`   | `/api/v1/stream/agent-stream/{product_id}`    | 에이전트 진행 상태 SSE 스트림                                 |
| `PATCH` | `/api/v1/orders/{purchase_order_id}/decision` | 발주 승인·수정·거절 및 결정 이력 저장                         |
| `GET`   | `/api/v1/orders/decision-metrics`             | 테넌트별 승인·수정·거절 건수 조회                             |
| `POST`  | `/api/v1/orders/run-prediction/{product_id}`  | 발주 수량 계산, 발주 초안 저장 및 단계별 워크플로우 결과 반환 |

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

응답에는 생성된 `purchase_order_id`, 제안 수량, 판단 근거, 에이전트 실행 로그가 포함됩니다.

## 발주 수량 산정 방식

현재 MVP는 아래의 단순 규칙을 사용합니다.

```text
예상 수요 = 판매 이력 평균 × 1.2
필요 수량 = 예상 수요 + 안전재고 - 현재 재고
제안 수량 = 필요 수량을 MOQ 단위로 올림
```

필요 수량이 0 이하이면 추가 발주를 제안하지 않습니다. 실제 예측 모델이나 외부 데이터 연동 전의 검증용 로직입니다.

## 테스트

백엔드 의존성을 설치한 환경에서 실행합니다.

```bash
pytest
```

현재 테스트 범위는 다음과 같습니다.

- `/health` 응답
- 발주 의사결정 상태 변경과 이력 저장
- LangGraph 발주 제안 워크플로의 수량 산출과 단계 로그

프론트엔드는 `pnpm dev` 실행 후 `/orders`에서 승인, 수량 수정, 거절 버튼을 눌러 발주 상태 변경 흐름을 확인할 수 있습니다.

## 현재 MVP의 제한 사항

- 인증은 아직 구현 전이며, 개발 편의를 위해 임시 관리자 사용자를 사용합니다. 운영 환경에 사용하면 안 됩니다.
- 프론트엔드의 발주 제안 데이터는 현재 예시 값으로 표시됩니다. 백엔드 발주 API와의 실제 조회 연동이 필요합니다.
- SSE 엔드포인트는 현재 데모용 단계 메시지를 전송하며, 실제 워크플로와 실시간으로 연결되어 있지 않습니다.
- 수요 예측은 고정된 판매 이력 기반의 단순 계산입니다. POS, 프로모션, 계절성, 공급사 데이터를 아직 연동하지 않았습니다.
- 상품 모델에는 공급사 관계가 있으나, 발주 계산에서는 공급사별 리드타임/MOQ를 직접 조회하지 않고 기본값을 사용합니다.
- 의사결정 지표는 현재 전체 누적 건수만 제공합니다. 기간별 추이와 상품별 분석이 필요합니다.

## 다음 개선 우선순위

1. 초기 migration과 테넌트·사용자·공급사 시드 데이터 추가
2. 실제 인증/권한 처리 및 개발용 임시 사용자 제거
3. 공급사 리드타임·MOQ를 발주 계산에 연동
4. 프론트엔드를 상품/발주 API와 연결하고 이벤트 전송 경로를 환경 변수화
5. 실제 판매 데이터 기반 예측, 기간·상품별 의사결정 분석 추가

## 참고

- API 문서: `http://localhost:8000/docs`
- 비즈니스 요구사항 및 측정 지표: [docs/Business_Context_Metrics.md](docs/Business_Context_Metrics.md)
