from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.tenant import Tenant, User, UserRole

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        settings,
        "JWT_SECRET_KEY",
        "test-only-secret-key-for-auth-tests",
    )


@pytest.fixture
def tenant_a() -> Tenant:
    return Tenant(id=1, name="Company A")


@pytest.fixture
def tenant_b() -> Tenant:
    return Tenant(id=2, name="Company B")

@pytest.fixture
def user_factory():
    def create_user(
        *,
        user_id: int,
        email: str,
        tenant_id: int,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        return User(
            id=user_id,
            email=email,
            hashed_password=hash_password("correct-password"),
            role=role,
            tenant_id=tenant_id,
        )

    return create_user

@pytest.fixture
def test_user(user_factory) -> User:
    return user_factory(
        user_id=1,
        email="admin@companyA.com",
        tenant_id=1,
        role=UserRole.ADMIN,
    )

@pytest.fixture
def admin_user(user_factory) -> User:
    return user_factory(
        user_id=1,
        email="admin@companyA.com",
        tenant_id=1,
        role=UserRole.ADMIN,
    )


@pytest.fixture
def manager_user(user_factory) -> User:
    return user_factory(
        user_id=2,
        email="manager@companyA.com",
        tenant_id=1,
        role=UserRole.MANAGER,
    )


@pytest.fixture
def viewer_user(user_factory) -> User:
    return user_factory(
        user_id=3,
        email="viewer@companyA.com",
        tenant_id=1,
        role=UserRole.VIEWER,
    )


@pytest.fixture
def mock_db(test_user):
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = test_user
    session.execute.return_value = result

    async def override_db():
        yield session

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db

    try:
        yield session
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous

@pytest.fixture
def auth_headers(jwt_secret, test_user) -> dict[str, str]:
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}

