# AI SCM 재고 최적화 플랫폼

판매 이력과 현재 재고, 안전재고, 최소 발주 수량(MOQ)을 바탕으로 적정 발주 수량을 제안하는 SCM(Supply Chain Management) MVP입니다.

LangGraph 기반 AI 워크플로가 수요 예측, 공급 조건 검토, 최종 발주 제안을 순차적으로 수행합니다. 담당자는 웹 화면에서 발주 제안을 확인하고 승인·수정·거절할 수 있습니다.

현재는 AI 발주 워크플로와 API를 기반으로 인증·권한 관리 및 멀티테넌트 데이터 격리 기능을 개발하고 있습니다.

## 주요 기능

### 1. AI 기반 발주 수량 제안

- 현재 재고와 안전재고를 기반으로 발주 필요량 계산
- 최소 발주 수량(MOQ) 등 공급 조건 반영
- LangGraph 기반 다단계 AI 워크플로 실행
- 발주 제안 수량과 판단 근거 생성
- 생성된 발주 제안을 초안(DRAFT)으로 저장

### 2. 워크플로 진행 상황 추적

- 워크플로 단계별 실행 상태 및 결과 추적
- SSE(Server-Sent Events)를 이용한 실행 진행 상황 전달
- 프론트엔드에서 단계별 처리 상태 시각화
- 워크플로 실행 실패 시 실패 단계와 완료된 단계를 구분

### 3. 발주 의사결정

- 발주 제안 조회
- 발주 제안 승인·수정·거절
- 발주 의사결정 이벤트 기록
- 의사결정 지표 조회

### 4. 인증 및 권한 관리

- 이메일과 비밀번호 기반 로그인
- 비밀번호 해시 검증
- JWT 액세스 토큰 발급 및 검증
- 인증된 사용자의 정보 조회
- 역할 기반 API 접근 제어

현재 정의된 사용자 역할은 다음과 같습니다.

| 역할      | 설명                     |
| --------- | ------------------------ |
| `ADMIN`   | 관리자 권한              |
| `MANAGER` | 발주 관련 주요 작업 수행 |
| `VIEWER`  | 조회 중심 접근           |

실제 접근 가능 범위는 각 API에 설정된 권한 정책을 기준으로 합니다.

### 5. 멀티테넌트 데이터 격리

- 사용자에 연결된 `tenant_id`를 기준으로 데이터 조회
- 상품 조회 시 테넌트 범위 제한
- 발주 조회 및 의사결정 이벤트 조회 시 테넌트 범위 제한
- 상품 생성 시 요청 데이터의 테넌트 값을 신뢰하지 않고 인증된 사용자의 테넌트를 사용
- 발주 생성 서비스에서도 테넌트 소유권을 검증하도록 개선

## 기술 스택

| 영역             | 기술                         |
| ---------------- | ---------------------------- |
| Backend          | Python, FastAPI              |
| Database         | PostgreSQL, SQLAlchemy Async |
| Authentication   | JWT, PyJWT                   |
| Password Hashing | pwdlib, Argon2               |
| AI Workflow      | LangGraph                    |
| Async Processing | Redis, Celery                |
| Frontend         | Next.js                      |
| API Testing      | pytest, FastAPI TestClient   |

## 아키텍처 개요

```text
Frontend (Next.js)
        |
        | REST API / SSE
        v
Backend (FastAPI)
        |
        +-- Authentication & Authorization
        |       +-- JWT validation
        |       +-- Role-based access control
        |       +-- Tenant context
        |
        +-- Inventory / Order Services
        |       +-- Product & Inventory
        |       +-- Purchase Order
        |       +-- Decision Events
        |
        +-- Prediction Service
                |
                v
          LangGraph Workflow
                |
                +-- Demand Agent
                +-- Supplier Agent
                +-- Supervisor
```

인증 계층은 요청의 사용자 정보를 검증하고, API와 서비스 계층은 해당 사용자의 테넌트 범위 안에서 데이터에 접근하도록 구성합니다.

## 프로젝트 구조

```text
app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── router.py
│       └── endpoints/
│           ├── auth.py
│           ├── inventory.py
│           ├── orders.py
│           ├── streaming.py
│           └── ...
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── exceptions.py
├── models/
├── schemas/
├── services/
│   ├── inventory_service.py
│   └── prediction_service.py
└── ...

tests/
├── test_auth_api.py
├── test_inventory_api.py
├── test_prediction_api.py
├── test_prediction_service.py
├── test_order_calculation.py
├── test_streaming_api.py
├── test_tracked_workflow.py
└── test_workflow_visualization.py
```

실제 디렉터리 및 테스트 파일 구성은 저장소의 현재 상태와 일치하도록 유지합니다.

## 실행 방법

### 1. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 데이터베이스 연결 정보와 인증 관련 설정을 구성합니다.

```dotenv
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/scm

JWT_SECRET_KEY=your-secure-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

- `JWT_SECRET_KEY`에는 충분히 강한 임의의 비밀 키를 사용합니다.
- 실제 비밀 키는 저장소에 커밋하지 않습니다.
- 위 데이터베이스 주소와 계정은 예시이며, 프로젝트 설정에 맞게 변경해야 합니다.

### 2. 의존성 설치

`uv`를 사용하는 경우:

```bash
uv sync
```

### 3. 서버 실행

프로젝트의 FastAPI 진입점이 `app.main:app`인 경우:

```bash
uv run uvicorn app.main:app --reload
```

서버 실행 후 `/docs`에서 API 명세를 확인할 수 있습니다.

## 인증 API

API 기본 경로는 `/api/v1`입니다.

| Method | Endpoint             | 설명                               |
| ------ | -------------------- | ---------------------------------- |
| `POST` | `/api/v1/auth/login` | 이메일·비밀번호 로그인 및 JWT 발급 |
| `GET`  | `/api/v1/auth/me`    | 인증된 사용자 정보 조회            |

로그인 요청은 `OAuth2PasswordRequestForm` 형식을 사용합니다. 따라서 JSON이 아닌 `application/x-www-form-urlencoded` 형식으로 `username`과 `password`를 전달합니다. 이때 `username` 필드에는 이메일 주소를 입력합니다.

로그인 성공 시 액세스 토큰을 반환합니다.

```json
{
  "access_token": "<access-token>",
  "token_type": "bearer"
}
```

인증이 필요한 API에는 다음 헤더를 전달합니다.

```http
Authorization: Bearer <access-token>
```

잘못된 토큰이나 인증 정보가 없는 요청은 `401 Unauthorized`, 권한이 부족한 요청은 `403 Forbidden`으로 처리합니다.

## 테스트

전체 테스트 실행:

```bash
uv run pytest -q
```

인증 API 테스트만 실행:

```bash
uv run pytest tests/test_auth_api.py -q
```

인증 테스트에서는 다음 항목을 검증합니다.

- 정상 로그인
- 잘못된 비밀번호
- 존재하지 않는 사용자
- 토큰 없는 사용자 정보 조회
- 유효한 토큰을 사용한 사용자 정보 조회
- 잘못된 토큰 검증

테넌트 격리와 권한 제어는 별도의 테스트로 검증해 회귀를 방지하는 것이 목표입니다.

## 현재 한계

- 실제 판매 이력과 연동한 수요 예측 데이터 파이프라인이 추가로 필요합니다.
- 현재 예측 워크플로에 하드코딩된 판매 이력 데이터는 실제 운영 데이터 기반으로 대체해야 합니다.
- JWT 액세스 토큰만으로 구성된 인증은 토큰 갱신·폐기 정책을 별도로 고려해야 합니다.
- 테넌트 격리는 API뿐 아니라 서비스 계층과 데이터베이스 무결성 제약에서도 일관되게 보장해야 합니다.
- 워크플로 실행 이력의 영속화 범위와 장애 복구 정책을 구체화해야 합니다.

## 로드맵

- [x] JWT 기반 인증 모듈 구현
- [x] 로그인 및 사용자 정보 조회 API 구현
- [x] 역할 기반 API 권한 검사 적용
- [x] 주요 상품·발주 API의 테넌트 범위 조회 적용
- [x] 테넌트 격리 및 역할별 권한 테스트 확대
- [ ] 서비스 계층의 테넌트 소유권 검증 강화
- [ ] 실제 판매 이력 기반 수요 예측 연결
- [ ] 워크플로 실행 이력 및 단계별 결과 영속화
- [ ] 예측 결과와 발주 의사결정 지표 고도화
