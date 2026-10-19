
# tests/test_auth_api.py

from unittest.mock import MagicMock

from app.core.security import create_access_token


def test_login_success(client, jwt_secret, mock_db):
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


def test_login_rejects_wrong_password(client, jwt_secret, mock_db):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@companyA.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_rejects_unknown_user(client, jwt_secret, mock_db):
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


def test_me_rejects_missing_token(client, jwt_secret):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(client, jwt_secret, mock_db):
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


def test_me_rejects_invalid_token(client, jwt_secret):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
