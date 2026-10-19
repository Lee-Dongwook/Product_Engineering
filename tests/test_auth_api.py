
# tests/test_auth_api.py

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.tenant import User, UserRole


client = TestClient(app)


@pytest.fixture
def jwt_secret(monkeypatch):
    monkeypatch.setattr(
        settings,
        "JWT_SECRET_KEY",
        "test-only-secret-key-for-auth-tests",
    )


@pytest.fixture
def test_user():
    return User(
        id=1,
        email="admin@companyA.com",
        hashed_password=hash_password("correct-password"),
        role=UserRole.ADMIN,
        tenant_id=1,
    )


@pytest.fixture
def mock_db(test_user):
    session = MagicMock()
    session.execute = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = test_user
    session.execute.return_value = result

    async def override_db():
        yield session

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db

    yield session

    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous


def test_login_success(jwt_secret, mock_db):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@companyA.com",
            "password": "correct-password",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_rejects_wrong_password(jwt_secret, mock_db):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@companyA.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_rejects_unknown_user(jwt_secret, mock_db):
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@companyA.com",
            "password": "correct-password",
        },
    )

    assert response.status_code == 401


def test_me_rejects_missing_token(jwt_secret):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(jwt_secret, mock_db):
    token = create_access_token(subject=1)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "admin@companyA.com",
        "role": "ADMIN",
        "tenant_id": 1,
    }


def test_me_rejects_invalid_token(jwt_secret):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
